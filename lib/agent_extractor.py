#!/usr/bin/env python3
"""
Agent Extraction Coordinator
Manages concurrent agent extraction from D&D modules

Uses RAG-based semantic extraction for document categorization.
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

from lib.extraction_schemas import (
    get_schema, validate_extraction,
    EXTRACTION_RESULT_SCHEMA
)
from lib.json_ops import JsonOperations
from lib.validators import Validators
from lib.campaign_manager import CampaignManager

# RAG imports - required, no fallback
from lib.rag import check_rag_available, get_missing_deps


class AgentExtractor:
    """Coordinates concurrent agent extraction of D&D content"""

    def __init__(self, world_state_dir: str = "world-state", campaign_name: str = None):
        self.world_state_dir = Path(world_state_dir)
        self.campaigns_dir = self.world_state_dir / "campaigns"
        self.campaign_name = campaign_name

        # Auto-approve mode - suppress confirmation prompts
        self.auto_approve = os.getenv("DM_AUTO_APPROVE", "0") == "1"

        # Set extraction directory based on campaign
        if campaign_name:
            self.extraction_dir = self.campaigns_dir / self._sanitize_name(campaign_name)
        else:
            self.extraction_dir = self.world_state_dir / "extraction-temp"

        # Initialize managers
        self.json_ops = JsonOperations(world_state_dir)
        self.validators = Validators()
        self.campaign_manager = CampaignManager(world_state_dir)

        # RAG extractor initialized lazily in prepare_for_agents
        self._rag_extractor = None

        # Backup of existing campaign data (preserved before extraction)
        self._existing_backup = {}

        # Ensure extraction directory exists
        self.extraction_dir.mkdir(parents=True, exist_ok=True)
        (self.extraction_dir / "chunks").mkdir(exist_ok=True)
        (self.extraction_dir / "extracted").mkdir(exist_ok=True)
        (self.extraction_dir / "saves").mkdir(exist_ok=True)

    def _backup_existing_data(self) -> Dict[str, Any]:
        """Backup existing campaign data before extraction.

        This preserves NPCs, locations, facts, items, and plots that were
        created manually or from previous imports so they aren't lost.
        """
        backup = {}
        files_to_backup = ['npcs.json', 'locations.json', 'facts.json', 'items.json', 'plots.json', 'consequences.json']

        for filename in files_to_backup:
            filepath = self.extraction_dir / filename
            if filepath.exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    # Only backup if there's actual content
                    if data and (isinstance(data, dict) and len(data) > 0) or (isinstance(data, list) and len(data) > 0):
                        backup[filename] = data
                        print(f"  Backed up existing {filename} ({len(data) if isinstance(data, dict) else 'list'} entries)")
                except (json.JSONDecodeError, IOError) as e:
                    print(f"  Warning: Could not backup {filename}: {e}")

        return backup

    def prepare_for_agents(self, filepath: str) -> Dict[str, Any]:
        """
        Extract text and vectorize document for agent extraction and /enhance.

        Returns dict with:
        - document_name: Source document
        - campaign_folder: Where content is being extracted
        - total_chunks: Number of chunks created
        - metadata: Additional info
        """
        # Check RAG availability - required, no fallback
        if not check_rag_available():
            missing = get_missing_deps()
            print("ERROR: RAG dependencies not installed.")
            print(f"Missing: {', '.join(missing)}")
            print("Install with: uv pip install -e '.[rag]'")
            print("Or: pip install sentence-transformers chromadb")
            sys.exit(1)

        # Import RAG components (safe now that we checked availability)
        from lib.rag import RAGExtractor

        print(f"Preparing document: {filepath}")

        # Set campaign name from document if not already set
        if not self.campaign_name:
            self.campaign_name = Path(filepath).stem
            self.extraction_dir = self.campaigns_dir / self._sanitize_name(self.campaign_name)
            self.extraction_dir.mkdir(parents=True, exist_ok=True)
            (self.extraction_dir / "chunks").mkdir(exist_ok=True)
            (self.extraction_dir / "extracted").mkdir(exist_ok=True)
            (self.extraction_dir / "saves").mkdir(exist_ok=True)

        print(f"Campaign folder: {self.extraction_dir}")

        # Ensure campaign_name is sanitized (in case it was passed to __init__)
        sanitized_name = self._sanitize_name(self.campaign_name)

        # BACKUP existing data BEFORE initializing (prevents data loss on re-import)
        self._existing_backup = self._backup_existing_data()
        if self._existing_backup:
            print(f"  Preserved {len(self._existing_backup)} existing data files for merge")

        # Initialize full campaign structure with preserve_existing=True
        # This ensures we don't overwrite existing files
        display_name = sanitized_name.replace('-', ' ').title()
        self.campaign_manager.init_campaign_files(
            self.extraction_dir,
            f"{display_name} Campaign",
            preserve_existing=True
        )

        # Clear previous extraction temp files (chunks, extracted) but not world state
        self._clear_extraction_temp()

        # Initialize RAG extractor for this campaign
        self._rag_extractor = RAGExtractor(str(self.extraction_dir))

        # Extract and vectorize document (no categorization - all chunks stored uniformly)
        rag_metadata = self._rag_extractor.extract_from_document(filepath, clear_existing=True)

        # Save the full text for reference
        from lib.content_extractor import ContentExtractor
        extractor = ContentExtractor()
        full_text = extractor.extract_text(filepath)
        (self.extraction_dir / "current-document.txt").write_text(full_text)

        # Write chunks to files for extraction agents to read
        chunks = self._rag_extractor._split_into_chunks(full_text)
        self._write_chunk_files(chunks)

        # Create metadata
        metadata = {
            "source_file": filepath,
            "document_name": Path(filepath).stem,
            "extraction_date": datetime.now().isoformat(),
            "extraction_method": "rag",
            "total_chunks": rag_metadata.get("total_chunks", 0),
            "total_chars": rag_metadata.get("total_chars", 0),
            "chunk_size": rag_metadata.get("chunk_size", 3000),
            "rag_stats": self._rag_extractor.get_stats()
        }

        # Save metadata
        (self.extraction_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, default=str)
        )

        return {
            "document_name": metadata["document_name"],
            "campaign_folder": str(self.extraction_dir),
            "total_chunks": metadata["total_chunks"],
            "metadata": metadata
        }

    def create_agent_prompts(self, chunks: Dict) -> List[Dict]:
        """
        Create specialized prompts for each agent

        Returns list of agent task definitions
        """
        prompts = []
        chunk_dir = self.extraction_dir / "chunks"

        # NPC extraction agent
        if chunks.get('npc_chunks', 0) > 0:
            prompts.append({
                "agent_type": "extractor-npcs",
                "prompt": f"Extract all NPCs from chunks in {chunk_dir}/npc_*.txt. "
                          f"Focus on character names, descriptions, personalities, stats, "
                          f"and relationships. Output to {self.extraction_dir}/extracted/agent-npcs.json",
                "chunk_count": chunks['npc_chunks']
            })

        # Location extraction agent
        if chunks.get('location_chunks', 0) > 0:
            prompts.append({
                "agent_type": "extractor-locations",
                "prompt": f"Extract all locations from chunks in {chunk_dir}/location_*.txt. "
                          f"Focus on place names, descriptions, connections, and features. "
                          f"Output to {self.extraction_dir}/extracted/agent-locations.json",
                "chunk_count": chunks['location_chunks']
            })

        # Item extraction agent
        if chunks.get('item_chunks', 0) > 0:
            prompts.append({
                "agent_type": "extractor-items",
                "prompt": f"Extract all items from chunks in {chunk_dir}/item_*.txt. "
                          f"Focus on magic items, treasures, equipment, and their properties. "
                          f"Output to {self.extraction_dir}/extracted/agent-items.json",
                "chunk_count": chunks['item_chunks']
            })

        # Plot extraction agent
        if chunks.get('plot_chunks', 0) > 0:
            prompts.append({
                "agent_type": "extractor-plots",
                "prompt": f"Extract all plot hooks from chunks in {chunk_dir}/plot_*.txt. "
                          f"Focus on quests, objectives, rewards, and story elements. "
                          f"Output to {self.extraction_dir}/extracted/agent-plots.json",
                "chunk_count": chunks['plot_chunks']
            })

        # General content agent (for mixed chunks)
        if chunks.get('general_chunks', 0) > 0:
            prompts.append({
                "agent_type": "extractor-general",
                "prompt": f"Extract all game content from chunks in {chunk_dir}/general_*.txt. "
                          f"Identify NPCs, locations, items, and plot hooks. Categorize appropriately. "
                          f"Output to {self.extraction_dir}/extracted/agent-general.json",
                "chunk_count": chunks['general_chunks']
            })

        return prompts

    def merge_agent_results(self, validate: bool = True) -> Dict:
        """
        Combine results from all concurrent agents

        Returns merged extraction results
        """
        print("Merging agent results...")

        extracted_dir = self.extraction_dir / "extracted"
        merged = {
            "npcs": {},
            "locations": {},
            "items": {},
            "plot_hooks": {},
            "monsters": {},
            "traps": {},
            "factions": {}
        }

        # Load metadata
        metadata_path = self.extraction_dir / "metadata.json"
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text())
        else:
            metadata = {"document_name": "unknown", "extraction_date": datetime.now().isoformat()}

        # Process each agent's output - look for both naming conventions:
        # 1. agent-npcs.json, agent-locations.json (old format)
        # 2. npcs.json, locations.json, items.json, plots.json (new format from agents)
        agent_files = list(extracted_dir.glob("agent-*.json"))

        # Also check for direct JSON files (npcs.json, locations.json, etc.)
        for direct_file in ['npcs.json', 'locations.json', 'items.json', 'plots.json']:
            direct_path = extracted_dir / direct_file
            if direct_path.exists() and direct_path not in agent_files:
                agent_files.append(direct_path)

        def to_dict(items, key_field='name'):
            """Convert list to dict using name as key, or return dict as-is"""
            if isinstance(items, dict):
                return items
            elif isinstance(items, list):
                return {item.get(key_field, f"unnamed_{i}"): item for i, item in enumerate(items)}
            return {}

        for agent_file in agent_files:
            try:
                data = json.loads(agent_file.read_text())

                # Determine if this is a direct file (npcs.json) vs wrapped (agent-npcs.json)
                # Direct files from agents are just {id: {...}, id2: {...}}
                # Wrapped files have {"npcs": {...}, "locations": {...}}
                filename = agent_file.name

                # For direct files (npcs.json, locations.json, etc.), the whole file IS the data
                if filename == 'npcs.json':
                    npcs = to_dict(data)
                    for name, npc in npcs.items():
                        merged['npcs'][name] = npc
                elif filename == 'locations.json':
                    locs = to_dict(data)
                    for name, loc in locs.items():
                        merged['locations'][name] = loc
                elif filename == 'items.json':
                    items = to_dict(data)
                    for name, item in items.items():
                        merged['items'][name] = item
                elif filename == 'plots.json':
                    plots = to_dict(data)
                    for name, plot in plots.items():
                        merged['plot_hooks'][name] = plot
                else:
                    # Agent-wrapped format (agent-*.json with nested keys)
                    if 'npcs' in data:
                        npcs = to_dict(data['npcs'])
                        for name, npc in npcs.items():
                            merged['npcs'][name] = npc

                    if 'locations' in data:
                        locs = to_dict(data['locations'])
                        for name, loc in locs.items():
                            merged['locations'][name] = loc

                    if 'items' in data:
                        items = to_dict(data['items'])
                        for name, item in items.items():
                            merged['items'][name] = item

                    if 'plot_hooks' in data:
                        plots = to_dict(data['plot_hooks'])
                        for name, plot in plots.items():
                            merged['plot_hooks'][name] = plot

                    # Merge other content types
                    for content_type in ['monsters', 'traps', 'factions']:
                        if content_type in data:
                            content = to_dict(data[content_type])
                            merged[content_type].update(content)

            except Exception as e:
                print(f"  Error processing {agent_file.name}: {e}")

        # Add metadata
        merged['metadata'] = metadata
        merged['extraction_summary'] = {
            "npcs_extracted": len(merged['npcs']),
            "locations_extracted": len(merged['locations']),
            "items_extracted": len(merged['items']),
            "plot_hooks_extracted": len(merged['plot_hooks']),
            "monsters_extracted": len(merged['monsters']),
            "traps_extracted": len(merged['traps']),
            "factions_extracted": len(merged['factions']),
            "agent_files_processed": len(agent_files)
        }

        # Save merged results
        merged_path = self.extraction_dir / "merged-results.json"
        merged_path.write_text(json.dumps(merged, indent=2))

        print(f"Merged {len(agent_files)} agent outputs:")
        for key, count in merged['extraction_summary'].items():
            if count > 0:
                print(f"  - {key}: {count}")

        return merged

    def validate_and_save(self, merged_data: Dict, conflict_strategy: str = "rename") -> Dict:
        """
        Validate combined results and save atomically to extraction folder

        Args:
            merged_data: Merged extraction results
            conflict_strategy: How to handle conflicts (rename/skip/overwrite)

        Returns:
            Dict with save results
        """
        print(f"Validating and saving to campaign folder: {self.extraction_dir}")

        results = {
            "npcs_saved": 0,
            "locations_saved": 0,
            "items_saved": 0,
            "plots_saved": 0,
            "conflicts": [],
            "errors": [],
            "preserved_from_backup": {}
        }

        # Use JsonOperations to work directly with extraction folder
        extraction_json = JsonOperations(str(self.extraction_dir))

        # Load BACKED UP existing data (preserved from before extraction started)
        # This ensures we merge with the original campaign data, not empty files
        existing_npcs_dict = self._existing_backup.get('npcs.json', {})
        existing_locations_dict = self._existing_backup.get('locations.json', {})

        # Track what we preserved
        if existing_npcs_dict:
            results['preserved_from_backup']['npcs'] = len(existing_npcs_dict)
        if existing_locations_dict:
            results['preserved_from_backup']['locations'] = len(existing_locations_dict)

        # Start with existing data (from backup)
        npcs_dict = existing_npcs_dict.copy()
        locations_dict = existing_locations_dict.copy()

        existing_npcs = set(npcs_dict.keys())
        existing_locations = set(locations_dict.keys())

        # Process NPCs from merged extraction data
        for name, npc_data in merged_data.get('npcs', {}).items():
            if name in existing_npcs:
                if conflict_strategy == "skip":
                    results['conflicts'].append(f"NPC '{name}' already exists, skipping")
                    continue
                elif conflict_strategy == "rename":
                    new_name = self._find_unique_name(name, existing_npcs)
                    results['conflicts'].append(f"Renamed NPC '{name}' to '{new_name}'")
                    name = new_name

            # Build NPC record
            npc_record = {
                'description': npc_data.get('description', ''),
                'attitude': npc_data.get('attitude', 'neutral'),
                'created': datetime.now().isoformat(),
                'events': npc_data.get('events', []),
                'tags': {
                    'locations': npc_data.get('location_tags', []),
                    'quests': npc_data.get('quest_tags', [])
                }
            }

            # Preserve dialogue from agent extraction as context
            agent_dialogue = npc_data.get('dialogue', [])
            if agent_dialogue:
                npc_record['context'] = agent_dialogue.copy()

            npcs_dict[name] = npc_record
            existing_npcs.add(name)

        # Save NPCs directly to extraction folder
        if npcs_dict:
            try:
                extraction_json.save_json("npcs.json", npcs_dict)
                results['npcs_saved'] = len(merged_data.get('npcs', {}))
                print(f"  Saved {results['npcs_saved']} NPCs to npcs.json")
            except Exception as e:
                results['errors'].append(f"Failed to save NPCs: {e}")

        # Process locations (locations_dict already initialized from backup above)
        for name, loc_data in merged_data.get('locations', {}).items():
            if name in existing_locations:
                if conflict_strategy == "skip":
                    results['conflicts'].append(f"Location '{name}' already exists, skipping")
                    continue
                elif conflict_strategy == "rename":
                    new_name = self._find_unique_name(name, existing_locations)
                    results['conflicts'].append(f"Renamed location '{name}' to '{new_name}'")
                    name = new_name

            locations_dict[name] = {
                'position': loc_data.get('position', ''),
                'description': loc_data.get('description', ''),
                'connections': loc_data.get('connections', []),
                'discovered': True
            }
            existing_locations.add(name)

        # Save locations directly to extraction folder
        if locations_dict:
            try:
                extraction_json.save_json("locations.json", locations_dict)
                results['locations_saved'] = len(merged_data.get('locations', {}))
                print(f"  Saved {results['locations_saved']} locations to locations.json")
            except Exception as e:
                results['errors'].append(f"Failed to save locations: {e}")

        # Save items and plot hooks to campaign folder (merge with backup)
        if merged_data.get('items') or self._existing_backup.get('items.json'):
            existing_items = self._existing_backup.get('items.json', {})
            if existing_items:
                results['preserved_from_backup']['items'] = len(existing_items)

            # Merge new items with existing (new items take precedence on conflict)
            items_dict = existing_items.copy()
            new_items = merged_data.get('items', {})
            for name, item_data in new_items.items():
                if name in items_dict:
                    results['conflicts'].append(f"Item '{name}' already exists, overwriting")
                items_dict[name] = item_data

            items_path = self.extraction_dir / "items.json"
            items_path.write_text(json.dumps(items_dict, indent=2))
            results['items_saved'] = len(new_items)
            print(f"  Saved {len(items_dict)} total items ({len(new_items)} new, {len(existing_items)} preserved)")

        if merged_data.get('plot_hooks') or self._existing_backup.get('plots.json'):
            existing_plots = self._existing_backup.get('plots.json', {})
            if existing_plots:
                results['preserved_from_backup']['plots'] = len(existing_plots)

            # Merge new plots with existing
            plots_dict = existing_plots.copy()
            new_plots = merged_data.get('plot_hooks', {})
            for name, plot_data in new_plots.items():
                if name in plots_dict:
                    results['conflicts'].append(f"Plot '{name}' already exists, overwriting")
                plots_dict[name] = plot_data

            plots_path = self.extraction_dir / "plots.json"
            plots_path.write_text(json.dumps(plots_dict, indent=2))
            results['plots_saved'] = len(new_plots)
            print(f"  Saved {len(plots_dict)} total plots ({len(new_plots)} new, {len(existing_plots)} preserved)")

        # Pass 2: Enrich NPCs with semantic context from vector store
        if results['npcs_saved'] > 0:
            try:
                from lib.rag import QuoteExtractor, check_rag_available
                if check_rag_available():
                    print("  Pass 2: Extracting semantic context for NPCs...")
                    context_extractor = QuoteExtractor(str(self.extraction_dir))
                    enriched_count = context_extractor.enrich_all_npcs()
                    results['npcs_enriched_with_context'] = enriched_count
                    print(f"  Enriched {enriched_count} NPCs with context")
            except Exception as e:
                print(f"  Warning: Context extraction failed: {e}")
                results['context_extraction_error'] = str(e)

        # Cleanup temp extraction files
        self._cleanup_extraction_temp()

        # Log extraction to session (optional - session_manager.add_event not yet implemented)
        doc_name = merged_data.get('metadata', {}).get('document_name', 'unknown')
        print(f"  Logged extraction from '{doc_name}'")

        return results

    def review_extraction(self) -> Dict:
        """Review extracted content before saving"""
        merged_path = self.extraction_dir / "merged-results.json"

        if not merged_path.exists():
            return {"error": "No merged results found. Run merge first."}

        data = json.loads(merged_path.read_text())

        review = {
            "source": data.get('metadata', {}).get('document_name', 'unknown'),
            "extracted": data.get('extraction_summary', {}),
            "samples": {}
        }

        # Sample first few of each type
        if data.get('npcs'):
            review['samples']['npcs'] = list(data['npcs'].keys())[:5]

        if data.get('locations'):
            review['samples']['locations'] = list(data['locations'].keys())[:5]

        if data.get('items'):
            review['samples']['items'] = list(data['items'].keys())[:5]

        if data.get('plot_hooks'):
            review['samples']['plot_hooks'] = list(data['plot_hooks'].keys())[:5]

        return review

    def _write_chunk_files(self, chunks: list) -> Dict:
        """Write chunks to files for extraction agents to read."""
        chunk_dir = self.extraction_dir / "chunks"
        chunk_dir.mkdir(exist_ok=True)

        chunk_files = []
        for idx, chunk_text in enumerate(chunks):
            filename = f"chunk_{idx:03d}.txt"
            filepath = chunk_dir / filename

            # Add header to chunk
            header = f"# Chunk {idx + 1} of {len(chunks)}\n"
            header += "---\n\n"

            filepath.write_text(header + chunk_text)
            chunk_files.append(str(filepath))

        print(f"  Wrote {len(chunk_files)} chunk files to {chunk_dir}")
        return {"chunk_files": chunk_files, "total_chunks": len(chunks)}

    def _save_chunks(self, categorized: Dict) -> Dict:
        """Save chunks to files for agent processing (legacy format)"""
        chunk_dir = self.extraction_dir / "chunks"
        chunk_files = {}

        for category, chunks in categorized.items():
            prefix = category.replace('_chunks', '')
            category_files = []

            for idx, chunk_info in enumerate(chunks):
                filename = f"{prefix}_{idx:03d}.txt"
                filepath = chunk_dir / filename

                # Add header to chunk
                header = f"# Chunk {idx + 1} of {len(chunks)} ({prefix} content)\n"
                header += f"# Confidence: {chunk_info.get('confidence', 0):.2f}\n"
                header += f"# Start line: ~{chunk_info.get('start_line', 0)}\n"
                header += "---\n\n"

                filepath.write_text(header + chunk_info['text'])
                category_files.append(str(filepath))

            chunk_files[category] = category_files

        return chunk_files

    def _clear_extraction_temp(self):
        """Clear the extraction temp directory (before extraction)"""
        for subdir in ['chunks', 'extracted']:
            dir_path = self.extraction_dir / subdir
            if dir_path.exists():
                shutil.rmtree(dir_path)
            dir_path.mkdir(exist_ok=True)

    def _cleanup_extraction_temp(self):
        """Remove temp files after extraction is complete (preserves vectors for /enhance)"""
        cleanup_items = [
            'chunks',           # Chunk text files for agents
            'extracted',        # Agent output JSON files
            'merged-results.json',  # Pre-save merged data
            # 'vectors' - KEEP for /enhance command
            'current-document.txt',  # Source text (can re-extract from PDF)
            'metadata.json',    # Extraction metadata
        ]

        cleaned = []
        for item in cleanup_items:
            item_path = self.extraction_dir / item
            if item_path.exists():
                if item_path.is_dir():
                    shutil.rmtree(item_path)
                else:
                    item_path.unlink()
                cleaned.append(item)

        if cleaned:
            print(f"  Cleaned up: {', '.join(cleaned)}")

    def _find_unique_name(self, base_name: str, existing: set) -> str:
        """Find a unique name by appending numbers"""
        if base_name not in existing:
            return base_name

        counter = 2
        while f"{base_name} ({counter})" in existing:
            counter += 1

        return f"{base_name} ({counter})"

    def _sanitize_name(self, name: str) -> str:
        """Sanitize campaign name for use as directory name"""
        import re
        # Remove file extension if present
        name = Path(name).stem
        # Replace spaces with dashes, remove special chars
        name = re.sub(r'[^a-zA-Z0-9\-_]', '-', name)
        # Collapse multiple dashes
        name = re.sub(r'-+', '-', name)
        # Remove leading/trailing dashes
        name = name.strip('-')
        # Lowercase for consistency
        return name.lower() or 'unnamed-campaign'


def main():
    """CLI interface for agent extraction"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: agent_extractor.py [prepare|merge|save|review] <args> [--campaign name]")
        sys.exit(1)

    # Check for campaign flag
    campaign_name = None
    if '--campaign' in sys.argv:
        idx = sys.argv.index('--campaign')
        if idx + 1 < len(sys.argv):
            campaign_name = sys.argv[idx + 1]
            # Remove the flag and value from argv
            sys.argv.pop(idx)
            sys.argv.pop(idx)

    extractor = AgentExtractor(campaign_name=campaign_name)
    command = sys.argv[1]

    if command == "prepare" and len(sys.argv) > 2:
        # Prepare document for extraction
        filepath = sys.argv[2]
        result = extractor.prepare_for_agents(filepath)
        print(json.dumps(result, indent=2))

    elif command == "merge":
        # Merge agent results
        result = extractor.merge_agent_results()
        print(f"\nExtraction complete: {result['extraction_summary']}")

    elif command == "save":
        # Save to world state
        strategy = sys.argv[2] if len(sys.argv) > 2 else "rename"
        merged_path = extractor.extraction_dir / "merged-results.json"

        if merged_path.exists():
            data = json.loads(merged_path.read_text())
            result = extractor.validate_and_save(data, conflict_strategy=strategy)
            print(f"\nSave complete: {result}")
        else:
            print("No merged results to save. Run merge first.")

    elif command == "review":
        # Review extracted content
        result = extractor.review_extraction()
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        print("Usage: agent_extractor.py [prepare|merge|save|review] <args>")


if __name__ == "__main__":
    main()