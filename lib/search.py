#!/usr/bin/env python3
"""
Search functionality for the DM's world state
Provides Python API for searching facts, NPCs, locations, and consequences
"""

import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from json_ops import JsonOperations
from campaign_manager import CampaignManager


class WorldSearcher:
    """Search across world state files"""

    def __init__(self, world_state_dir: str = None):
        # Use campaign manager to resolve the correct directory
        base_dir = world_state_dir or "world-state"
        campaign_mgr = CampaignManager(base_dir)

        # Get the active campaign directory (falls back to legacy root)
        active_dir = campaign_mgr.get_active_campaign_dir()
        self.json_ops = JsonOperations(str(active_dir))

    def search_facts(self, query: str) -> Dict[str, List[Dict]]:
        """Search facts by category or content"""
        facts = self.json_ops.load_json('facts.json')
        results = {}
        query_lower = query.lower()

        for category, fact_list in facts.items():
            if not isinstance(fact_list, list):
                continue
            # Check category name
            if query_lower in category.lower():
                results[category] = fact_list
            else:
                # Check fact content
                matching_facts = [
                    fact for fact in fact_list
                    if isinstance(fact, dict) and query_lower in fact.get('fact', '').lower()
                ]
                if matching_facts:
                    results[category] = matching_facts

        return results

    def search_npcs(self, query: str) -> Dict[str, Dict]:
        """Search NPCs by name or description"""
        npcs = self.json_ops.load_json('npcs.json')
        results = {}
        query_lower = query.lower()

        for name, npc_data in npcs.items():
            if not isinstance(npc_data, dict):
                continue
            if (query_lower in name.lower() or
                query_lower in npc_data.get('description', '').lower()):
                results[name] = npc_data

        return results

    def search_npcs_by_tag(self, tag_type: str, tag_value: str) -> Dict[str, Dict]:
        """Search NPCs by location or quest tag"""
        npcs = self.json_ops.load_json('npcs.json')
        results = {}
        tag_lower = tag_value.lower()

        # Normalize tag type (locations vs location, quests vs quest)
        if tag_type in ('location', 'locations'):
            tag_key = 'locations'
        elif tag_type in ('quest', 'quests'):
            tag_key = 'quests'
        else:
            tag_key = tag_type

        for name, npc_data in npcs.items():
            if not isinstance(npc_data, dict):
                continue
            tags = npc_data.get('tags', {})
            if isinstance(tags, dict):
                tag_list = tags.get(tag_key, [])
                if isinstance(tag_list, list):
                    if any(tag_lower in t.lower() for t in tag_list):
                        results[name] = npc_data

        return results

    def search_locations(self, query: str) -> Dict[str, Dict]:
        """Search locations by name, description, or position"""
        locations = self.json_ops.load_json('locations.json')
        results = {}
        query_lower = query.lower()

        for name, loc_data in locations.items():
            if not isinstance(loc_data, dict):
                continue
            if (query_lower in name.lower() or
                query_lower in loc_data.get('description', '').lower() or
                query_lower in loc_data.get('position', '').lower()):
                results[name] = loc_data

        return results

    def search_consequences(self, query: str) -> List[Dict]:
        """Search active consequences"""
        consequences = self.json_ops.load_json('consequences.json')
        results = []
        query_lower = query.lower()

        for consequence in consequences.get('active', []):
            if isinstance(consequence, dict):
                if query_lower in consequence.get('consequence', '').lower():
                    results.append(consequence)

        return results

    def search_plots(self, query: str) -> Dict[str, Dict]:
        """Search plots by name, description, NPCs, locations, or objectives"""
        plots = self.json_ops.load_json('plots.json')
        results = {}
        query_lower = query.lower()

        for name, data in plots.items():
            if not isinstance(data, dict):
                continue

            # Search in name
            if query_lower in name.lower():
                results[name] = data
                continue

            # Search in description
            if query_lower in data.get('description', '').lower():
                results[name] = data
                continue

            # Search in NPCs list
            npcs = data.get('npcs', [])
            if any(query_lower in npc.lower() for npc in npcs):
                results[name] = data
                continue

            # Search in locations list
            locations = data.get('locations', [])
            if any(query_lower in loc.lower() for loc in locations):
                results[name] = data
                continue

            # Search in objectives
            objectives = data.get('objectives', [])
            if any(query_lower in obj.lower() for obj in objectives):
                results[name] = data
                continue

            # Search in consequences
            if query_lower in data.get('consequences', '').lower():
                results[name] = data
                continue

        return results

    def find_related_plots(self, entity_name: str, entity_type: str = 'any') -> Dict[str, Dict]:
        """
        Find plots that reference a specific NPC or location.
        Used for cross-referencing when searching NPCs/locations.
        """
        plots = self.json_ops.load_json('plots.json')
        related = {}
        name_lower = entity_name.lower()

        for plot_name, data in plots.items():
            if not isinstance(data, dict):
                continue

            # Check NPCs list
            if entity_type in ('any', 'npc'):
                npcs = data.get('npcs', [])
                if any(name_lower in npc.lower() for npc in npcs):
                    related[plot_name] = data
                    continue

            # Check locations list
            if entity_type in ('any', 'location'):
                locations = data.get('locations', [])
                if any(name_lower in loc.lower() for loc in locations):
                    related[plot_name] = data
                    continue

        return related

    def search_all(self, query: str) -> Dict[str, Any]:
        """Search across all world state"""
        results = {
            'facts': self.search_facts(query),
            'npcs': self.search_npcs(query),
            'locations': self.search_locations(query),
            'consequences': self.search_consequences(query),
            'plots': self.search_plots(query)
        }

        # Cross-reference: find plots related to matched NPCs and locations
        related_plots = {}

        # Check if any NPCs matched and find their related plots
        for npc_name in results['npcs'].keys():
            npc_plots = self.find_related_plots(npc_name, 'npc')
            for plot_name, plot_data in npc_plots.items():
                if plot_name not in results['plots'] and plot_name not in related_plots:
                    related_plots[plot_name] = plot_data

        # Check if any locations matched and find their related plots
        for loc_name in results['locations'].keys():
            loc_plots = self.find_related_plots(loc_name, 'location')
            for plot_name, plot_data in loc_plots.items():
                if plot_name not in results['plots'] and plot_name not in related_plots:
                    related_plots[plot_name] = plot_data

        results['related_plots'] = related_plots
        return results

    def get_npc(self, name: str) -> Optional[Dict]:
        """Get specific NPC by exact name"""
        npcs = self.json_ops.load_json('npcs.json')
        return npcs.get(name)

    def get_location(self, name: str) -> Optional[Dict]:
        """Get specific location by exact name"""
        locations = self.json_ops.load_json('locations.json')
        return locations.get(name)

    def get_pending_consequences(self, trigger: Optional[str] = None) -> List[Dict]:
        """Get pending consequences, optionally filtered by trigger"""
        consequences = self.json_ops.load_json('consequences.json')
        active = consequences.get('active', [])

        if trigger:
            return [c for c in active if trigger.lower() in c.get('trigger', '').lower()]
        return active

    def get_facts_by_category(self, category: str) -> List[Dict]:
        """Get all facts in a specific category"""
        facts = self.json_ops.load_json('facts.json')
        return facts.get(category, [])

    def _format_text(self, text: str, full: bool = False, limit: int = 220) -> str:
        """Optionally truncate long text for token-efficient output."""
        if full or not text:
            return text
        if len(text) <= limit:
            return text
        return text[:limit - 3].rstrip() + "..."

    def print_results(self, results: Dict[str, Any], query: str = "", full: bool = False):
        """Print formatted search results"""
        found_anything = False

        if results.get('facts'):
            print("\nFACTS:")
            found_anything = True
            for category, facts in results['facts'].items():
                for fact in facts:
                    print(f"  [{category}] {fact.get('fact', '')}")

        if results.get('npcs'):
            print("\nNPCs:")
            found_anything = True
            for name, npc in results['npcs'].items():
                desc = self._format_text(npc.get('description', ''), full=full, limit=240)
                print(f"  - {name}: {desc} ({npc.get('attitude', '')})")
                if npc.get('events'):
                    last_event = npc['events'][-1]
                    # Handle both string events and dict events
                    if isinstance(last_event, dict):
                        print(f"    Last event: {self._format_text(last_event.get('event', ''), full=full, limit=140)}")
                    else:
                        print(f"    Last event: {self._format_text(str(last_event), full=full, limit=140)}")

        if results.get('locations'):
            print("\nLOCATIONS:")
            found_anything = True
            for name, loc in results['locations'].items():
                print(f"  - {name}: {loc.get('position', '')}")
                if loc.get('description'):
                    print(f"    {self._format_text(loc['description'], full=full, limit=260)}")
                if loc.get('connections'):
                    print(f"    Connections: {len(loc['connections'])}")

        if results.get('consequences'):
            print("\nCONSEQUENCES:")
            found_anything = True
            for c in results['consequences']:
                consequence_text = self._format_text(c.get('consequence', ''), full=full, limit=180)
                trigger_text = self._format_text(c.get('trigger', ''), full=full, limit=60)
                print(f"  [{c.get('id', '?')}] {consequence_text} (triggers: {trigger_text})")

        if results.get('plots'):
            print("\nPLOTS:")
            found_anything = True
            for name, plot in results['plots'].items():
                status = plot.get('status', 'active').upper()
                plot_type = plot.get('type', 'unknown').upper()
                status_marker = ""
                if status == 'COMPLETED':
                    status_marker = " [DONE]"
                elif status == 'FAILED':
                    status_marker = " [FAILED]"
                print(f"  - {name} ({plot_type}){status_marker}")
                print(f"    {self._format_text(plot.get('description', ''), full=full, limit=80)}")

        if results.get('related_plots'):
            related_items = list(results['related_plots'].items())
            max_related = len(related_items) if full else 3
            print("\nRELATED PLOTS (referenced by matched NPCs/locations):")
            found_anything = True
            for name, plot in related_items[:max_related]:
                plot_type = plot.get('type', 'unknown').upper()
                # Show which NPCs/locations link this plot
                npcs = plot.get('npcs', [])
                locations = plot.get('locations', [])
                links = []
                if npcs:
                    links.append(f"NPCs: {', '.join(npcs[:3])}")
                if locations:
                    links.append(f"Locations: {', '.join(locations[:3])}")
                link_str = " | ".join(links) if links else ""
                print(f"  - {name} ({plot_type})")
                if link_str:
                    print(f"    → {link_str}")
            if len(related_items) > max_related:
                print(f"  ... and {len(related_items) - max_related} more (use --full)")

        if not found_anything:
            print(f"\nNo results found for \"{query}\"")
            self._print_suggestions()

    def print_npc_results(self, npcs: Dict[str, Dict], tag_type: str = "", tag_value: str = "", full: bool = False):
        """Print formatted NPC results with tag details"""
        if not npcs:
            print(f"\nNo NPCs found with {tag_type} tag \"{tag_value}\"")
            self._print_suggestions()
            return

        print("\nNPCs:")
        for name, npc in npcs.items():
            desc = self._format_text(npc.get('description', ''), full=full, limit=240)
            print(f"  - {name}: {desc} ({npc.get('attitude', '')})")
            tags = npc.get('tags', {})
            if isinstance(tags, dict):
                if tags.get('locations'):
                    print(f"    Locations: {', '.join(tags['locations'])}")
                if tags.get('quests'):
                    print(f"    Quests: {', '.join(tags['quests'])}")
            if npc.get('events'):
                last_event = npc['events'][-1]
                if isinstance(last_event, dict):
                    text = last_event.get('event', '')
                else:
                    text = str(last_event)
                print(f"    Last event: {self._format_text(text, full=full, limit=140)}")

    def _print_suggestions(self):
        """Print available NPCs and dungeons to help with typos"""
        print("\n--- Did you mean? ---")

        # List available NPCs
        npcs = self.json_ops.load_json('npcs.json')
        if npcs:
            npc_names = sorted([name for name in npcs.keys() if isinstance(npcs[name], dict)])
            if npc_names:
                print(f"\nKnown NPCs ({len(npc_names)}):")
                for name in npc_names[:10]:  # Show first 10
                    print(f"  - {name}")
                if len(npc_names) > 10:
                    print(f"  ... and {len(npc_names) - 10} more")

        # List available dungeons and locations
        locations = self.json_ops.load_json('locations.json')
        if locations:
            dungeons = set()
            other_locations = []
            for name, loc_data in locations.items():
                if isinstance(loc_data, dict) and loc_data.get('dungeon'):
                    dungeons.add(loc_data['dungeon'])
                elif isinstance(loc_data, dict):
                    other_locations.append(name)

            if dungeons:
                print(f"\nKnown Dungeons ({len(dungeons)}):")
                for dungeon in sorted(dungeons):
                    # Count rooms
                    room_count = sum(1 for loc in locations.values()
                                   if isinstance(loc, dict) and loc.get('dungeon') == dungeon)
                    print(f"  - {dungeon} ({room_count} rooms)")

            if other_locations:
                print(f"\nKnown Locations ({len(other_locations)}):")
                for name in sorted(other_locations)[:8]:  # Show first 8
                    print(f"  - {name}")
                if len(other_locations) > 8:
                    print(f"  ... and {len(other_locations) - 8} more")


def main():
    """CLI interface for searching"""
    import argparse

    parser = argparse.ArgumentParser(description='Search world state')
    parser.add_argument('query', nargs='*', help='Search query')
    parser.add_argument('--tag-location', help='Search NPCs by location tag')
    parser.add_argument('--tag-quest', help='Search NPCs by quest tag')
    parser.add_argument('--full', action='store_true', help='Show full descriptions')

    args = parser.parse_args()

    searcher = WorldSearcher()

    # Tag-based search
    if args.tag_location:
        npcs = searcher.search_npcs_by_tag('locations', args.tag_location)
        searcher.print_npc_results(npcs, 'location', args.tag_location, full=args.full)
    elif args.tag_quest:
        npcs = searcher.search_npcs_by_tag('quests', args.tag_quest)
        searcher.print_npc_results(npcs, 'quest', args.tag_quest, full=args.full)
    elif args.query:
        # Regular search
        query = ' '.join(args.query)
        results = searcher.search_all(query)
        searcher.print_results(results, query, full=args.full)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
