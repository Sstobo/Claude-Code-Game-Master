import glob
import os
from pathlib import Path

# Use pathlib for cross-platform handling
chunks_dir = Path('/c/Users/SJG/Documents/CodePlayground/dm/Claude-Code-Game-Master/world-state/campaigns/dungeon-crawler-carl/chunks')
print(f"Path: {chunks_dir}")
print(f"Exists: {chunks_dir.exists()}")
print(f"Is dir: {chunks_dir.is_dir()}")

# Use glob with pathlib
chunk_files = sorted(chunks_dir.glob('chunk_*.txt'))
print(f"Found {len(chunk_files)} files")
print(f"First 5: {[f.name for f in chunk_files[:5]]}")
