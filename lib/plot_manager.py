#!/usr/bin/env python3
"""
Plot management module for DM tools
Handles plot listing, searching, and status updates
"""

import sys
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add lib directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from entity_manager import EntityManager


class PlotManager(EntityManager):
    """Manage plot operations. Inherits from EntityManager for common functionality."""

    def __init__(self, world_state_dir: str = None):
        super().__init__(world_state_dir)
        self.plots_file = "plots.json"

    def add_plot(self, name: str, description: str, plot_type: str = "side",
                 npcs: list = None, locations: list = None, objectives: list = None,
                 rewards: str = None, consequences: str = None) -> bool:
        plots = self._load_entities(self.plots_file)
        if name in plots:
            print(f"[ERROR] Plot '{name}' already exists")
            return False
        plots[name] = {
            "name": name,
            "description": description,
            "type": plot_type,
            "status": "active",
            "npcs": npcs or [],
            "locations": locations or [],
            "objectives": objectives or [],
            "rewards": rewards or "",
            "consequences": consequences or "",
            "events": [],
            "created_at": self.get_timestamp()
        }
        if self._save_entities(self.plots_file, plots):
            print(f"[SUCCESS] Created plot '{name}' (type: {plot_type})")
            if objectives:
                for obj in objectives:
                    print(f"  • {obj}")
            return True
        return False

    def list_plots(self, plot_type: Optional[str] = None,
                   status: Optional[str] = None) -> Dict[str, Dict]:
        """
        List all plots with optional filtering by type and status
        """
        plots = self._load_entities(self.plots_file)
        filtered = {}

        for name, data in plots.items():
            if not isinstance(data, dict):
                continue

            # Apply type filter
            if plot_type and data.get('type', '').lower() != plot_type.lower():
                continue

            # Apply status filter (default to 'active' if not set)
            plot_status = data.get('status', 'active').lower()
            if status and plot_status != status.lower():
                continue

            filtered[name] = data

        return filtered

    def get_plot(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get full details of a specific plot by name
        """
        actual_name = self._find_entity_name(self.plots_file, name)
        if not actual_name:
            return None
        return self._get_entity(self.plots_file, actual_name)

    def search_plots(self, query: str) -> Dict[str, Dict]:
        """
        Search plots by name, description, NPCs, locations, or objectives
        """
        plots = self._load_entities(self.plots_file)
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

    def update_plot(self, name: str, event: str) -> bool:
        """
        Add a progress event to a plot's history
        """
        actual_name = self._find_entity_name(self.plots_file, name)
        if not actual_name:
            print(f"[ERROR] Plot '{name}' not found")
            return False

        plots = self._load_entities(self.plots_file)

        # Ensure events list exists
        if 'events' not in plots[actual_name]:
            plots[actual_name]['events'] = []

        # Add event with timestamp
        event_data = {
            'event': event,
            'timestamp': self.get_timestamp()
        }
        plots[actual_name]['events'].append(event_data)

        # Ensure status is set
        if 'status' not in plots[actual_name]:
            plots[actual_name]['status'] = 'active'

        if self._save_entities(self.plots_file, plots):
            print(f"[SUCCESS] Updated plot '{actual_name}': {event}")
            return True
        return False

    def complete_plot(self, name: str, outcome: Optional[str] = None) -> bool:
        """
        Mark a plot as completed
        """
        actual_name = self._find_entity_name(self.plots_file, name)
        if not actual_name:
            print(f"[ERROR] Plot '{name}' not found")
            return False

        plots = self._load_entities(self.plots_file)

        plots[actual_name]['status'] = 'completed'
        plots[actual_name]['completed_at'] = self.get_timestamp()

        # Add completion event
        if 'events' not in plots[actual_name]:
            plots[actual_name]['events'] = []

        event_text = f"COMPLETED: {outcome}" if outcome else "Plot completed"
        plots[actual_name]['events'].append({
            'event': event_text,
            'timestamp': self.get_timestamp()
        })

        if self._save_entities(self.plots_file, plots):
            print(f"[SUCCESS] Completed plot '{actual_name}'")
            if outcome:
                print(f"  Outcome: {outcome}")
            return True
        return False

    def fail_plot(self, name: str, reason: Optional[str] = None) -> bool:
        """
        Mark a plot as failed
        """
        actual_name = self._find_entity_name(self.plots_file, name)
        if not actual_name:
            print(f"[ERROR] Plot '{name}' not found")
            return False

        plots = self._load_entities(self.plots_file)

        plots[actual_name]['status'] = 'failed'
        plots[actual_name]['failed_at'] = self.get_timestamp()

        # Add failure event
        if 'events' not in plots[actual_name]:
            plots[actual_name]['events'] = []

        event_text = f"FAILED: {reason}" if reason else "Plot failed"
        plots[actual_name]['events'].append({
            'event': event_text,
            'timestamp': self.get_timestamp()
        })

        if self._save_entities(self.plots_file, plots):
            print(f"[SUCCESS] Failed plot '{actual_name}'")
            if reason:
                print(f"  Reason: {reason}")
            return True
        return False

    def get_plot_counts(self) -> Dict[str, int]:
        """
        Get counts of plots by type and status
        """
        plots = self._load_entities(self.plots_file)

        counts = {
            'total': 0,
            'active': 0,
            'completed': 0,
            'failed': 0,
            'dormant': 0,
            'main': 0,
            'side': 0,
            'mystery': 0,
            'threat': 0
        }

        for name, data in plots.items():
            if not isinstance(data, dict):
                continue

            counts['total'] += 1

            # Count by status (default to 'active')
            status = data.get('status', 'active').lower()
            if status in counts:
                counts[status] += 1

            # Count by type
            plot_type = data.get('type', '').lower()
            if plot_type in counts:
                counts[plot_type] += 1

        return counts

    def format_plot_status(self, name: str) -> Optional[str]:
        """
        Format plot details for display
        """
        plot = self.get_plot(name)
        if not plot:
            print(f"[ERROR] Plot '{name}' not found")
            return None

        lines = [f"=== {plot.get('name', name)} ===", ""]

        # Type and status
        plot_type = plot.get('type', 'unknown').upper()
        status = plot.get('status', 'active').upper()
        lines.append(f"Type: {plot_type} | Status: {status}")
        lines.append("")

        # Description
        lines.append("Description:")
        lines.append(f"  {plot.get('description', 'No description')}")
        lines.append("")

        # NPCs involved
        npcs = plot.get('npcs', [])
        if npcs:
            lines.append(f"NPCs: {', '.join(npcs)}")

        # Locations
        locations = plot.get('locations', [])
        if locations:
            lines.append(f"Locations: {', '.join(locations)}")

        # Objectives
        objectives = plot.get('objectives', [])
        if objectives:
            lines.append("")
            lines.append("Objectives:")
            for obj in objectives:
                lines.append(f"  • {obj}")

        # Consequences
        consequences = plot.get('consequences', '')
        if consequences:
            lines.append("")
            lines.append(f"Consequences: {consequences}")

        # Progress events
        events = plot.get('events', [])
        if events:
            lines.append("")
            lines.append("--- PROGRESS ---")
            for event in events[-5:]:  # Show last 5 events
                if isinstance(event, dict):
                    lines.append(f"  • {event.get('event', '')}")
                else:
                    lines.append(f"  • {event}")

        return "\n".join(lines)

    def format_plot_list(self, plots: Dict[str, Dict]) -> str:
        """
        Format a list of plots for display
        """
        if not plots:
            return "No plots found."

        lines = ["=== PLOTS ===", ""]

        # Group by type
        by_type = {'main': [], 'side': [], 'mystery': [], 'threat': [], 'other': []}
        for name, data in plots.items():
            plot_type = data.get('type', 'other').lower()
            if plot_type not in by_type:
                plot_type = 'other'
            by_type[plot_type].append((name, data))

        type_labels = {
            'main': 'MAIN PLOTS',
            'side': 'SIDE QUESTS',
            'mystery': 'MYSTERIES',
            'threat': 'THREATS',
            'other': 'OTHER'
        }

        for plot_type, label in type_labels.items():
            type_plots = by_type[plot_type]
            if type_plots:
                lines.append(f"--- {label} ---")
                for name, data in type_plots:
                    status = data.get('status', 'active').upper()
                    status_marker = ""
                    if status == 'COMPLETED':
                        status_marker = " [DONE]"
                    elif status == 'FAILED':
                        status_marker = " [FAILED]"
                    elif status == 'DORMANT':
                        status_marker = " [DORMANT]"

                    desc = data.get('description', '')[:60]
                    if len(data.get('description', '')) > 60:
                        desc += "..."
                    lines.append(f"  • {name}{status_marker}")
                    lines.append(f"    {desc}")
                lines.append("")

        return "\n".join(lines)


    def get_active_threads(self) -> Dict[str, List[Dict]]:
        """
        Get active plot threads grouped by type, with staleness info.
        Returns dict keyed by type, each containing list of thread summaries.
        """
        from datetime import datetime, timezone

        plots = self._load_entities(self.plots_file)
        threads = {'main': [], 'side': [], 'mystery': [], 'threat': [], 'other': []}

        # Try to get session count for staleness
        try:
            from session_manager import SessionManager
            sm = SessionManager()
            current_session = sm._get_session_number()
        except Exception:
            current_session = None

        for name, data in plots.items():
            if not isinstance(data, dict):
                continue

            status = data.get('status', 'active').lower()
            if status != 'active':
                continue

            plot_type = data.get('type', 'other').lower()
            if plot_type not in threads:
                plot_type = 'other'

            # Get last event
            events = data.get('events', [])
            last_event = None
            last_event_session = None
            if events:
                last = events[-1]
                if isinstance(last, dict):
                    last_event = last.get('event', '')
                    last_event_session = last.get('session_number')
                else:
                    last_event = str(last)

            # Calculate staleness based on session number if available
            stale_sessions = None
            if current_session and last_event_session is not None:
                stale_sessions = current_session - last_event_session

            thread = {
                'name': name,
                'last_event': last_event,
                'stale_sessions': stale_sessions,
                'npcs': data.get('npcs', []),
                'locations': data.get('locations', []),
                'description': data.get('description', ''),
            }

            threads[plot_type].append(thread)

        return threads

    def format_threads(self, threads: Dict[str, List[Dict]]) -> str:
        """
        Format active threads for display — DM notes style, not a database query.
        """
        has_any = any(threads[t] for t in threads)
        if not has_any:
            return "No active story threads. Time to create some plot hooks!"

        lines = ["=== ACTIVE STORY THREADS ===", ""]

        type_labels = {
            'main': 'MAIN PLOTS',
            'side': 'SIDE QUESTS',
            'mystery': 'MYSTERIES',
            'threat': 'THREATS',
            'other': 'OTHER',
        }

        for plot_type, label in type_labels.items():
            type_threads = threads[plot_type]
            if not type_threads:
                continue

            lines.append(label)
            for thread in type_threads:
                # Staleness warning
                stale_marker = ""
                if thread['stale_sessions'] is not None and thread['stale_sessions'] >= 3:
                    stale_marker = f" (!! stale - {thread['stale_sessions']} sessions)"
                elif thread['stale_sessions'] is not None and thread['stale_sessions'] >= 2:
                    stale_marker = f" ({thread['stale_sessions']} sessions ago)"

                lines.append(f"  > {thread['name']}{stale_marker}")

                # Last event
                if thread['last_event']:
                    lines.append(f"    Last: \"{thread['last_event']}\"")
                else:
                    lines.append(f"    (no events recorded)")

                # Connected NPCs
                if thread['npcs']:
                    lines.append(f"    NPCs: {', '.join(thread['npcs'])}")

                # Connected locations
                if thread['locations']:
                    lines.append(f"    Locations: {', '.join(thread['locations'])}")

                lines.append("")

        return "\n".join(lines)


def main():
    """CLI interface for plot management"""
    import argparse

    parser = argparse.ArgumentParser(description='Plot management')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')

    # Add plot
    add_parser = subparsers.add_parser('add', help='Create new plot/quest')
    add_parser.add_argument('name', help='Plot name')
    add_parser.add_argument('description', help='Plot description')
    add_parser.add_argument('--type', dest='plot_type', default='side',
                            choices=['main', 'side', 'mystery', 'threat'])
    add_parser.add_argument('--npcs', nargs='+', default=[])
    add_parser.add_argument('--locations', nargs='+', default=[])
    add_parser.add_argument('--objectives', nargs='+', default=[])
    add_parser.add_argument('--rewards', default='')
    add_parser.add_argument('--consequences', default='')

    # List plots
    list_parser = subparsers.add_parser('list', help='List plots')
    list_parser.add_argument('--type', help='Filter by type (main, side, mystery, threat)')
    list_parser.add_argument('--status', help='Filter by status (active, completed, failed, dormant)')

    # Show plot
    show_parser = subparsers.add_parser('show', help='Show plot details')
    show_parser.add_argument('name', help='Plot name')

    # Search plots
    search_parser = subparsers.add_parser('search', help='Search plots')
    search_parser.add_argument('query', help='Search query')

    # Update plot
    update_parser = subparsers.add_parser('update', help='Add progress event to plot')
    update_parser.add_argument('name', help='Plot name')
    update_parser.add_argument('event', help='Progress event description')

    # Complete plot
    complete_parser = subparsers.add_parser('complete', help='Mark plot as completed')
    complete_parser.add_argument('name', help='Plot name')
    complete_parser.add_argument('outcome', nargs='?', help='Outcome description')

    # Fail plot
    fail_parser = subparsers.add_parser('fail', help='Mark plot as failed')
    fail_parser.add_argument('name', help='Plot name')
    fail_parser.add_argument('reason', nargs='?', help='Failure reason')

    # Counts
    counts_parser = subparsers.add_parser('counts', help='Get plot counts')

    # Active threads summary
    subparsers.add_parser('threads', help='Show active story threads (DM dashboard)')

    args = parser.parse_args()

    if not args.action:
        parser.print_help()
        sys.exit(1)

    manager = PlotManager()

    if args.action == 'add':
        if not manager.add_plot(
            name=args.name,
            description=args.description,
            plot_type=args.plot_type,
            npcs=args.npcs,
            locations=args.locations,
            objectives=args.objectives,
            rewards=args.rewards,
            consequences=args.consequences
        ):
            sys.exit(1)

    elif args.action == 'list':
        plots = manager.list_plots(args.type, args.status)
        print(manager.format_plot_list(plots))

    elif args.action == 'show':
        formatted = manager.format_plot_status(args.name)
        if formatted:
            print(formatted)
        else:
            sys.exit(1)

    elif args.action == 'search':
        plots = manager.search_plots(args.query)
        if plots:
            print(manager.format_plot_list(plots))
        else:
            print(f"No plots found matching '{args.query}'")

    elif args.action == 'update':
        if not manager.update_plot(args.name, args.event):
            sys.exit(1)

    elif args.action == 'complete':
        if not manager.complete_plot(args.name, args.outcome):
            sys.exit(1)

    elif args.action == 'fail':
        if not manager.fail_plot(args.name, args.reason):
            sys.exit(1)

    elif args.action == 'counts':
        import json
        counts = manager.get_plot_counts()
        print(json.dumps(counts, indent=2, ensure_ascii=False))

    elif args.action == 'threads':
        threads = manager.get_active_threads()
        print(manager.format_threads(threads))


if __name__ == "__main__":
    main()
