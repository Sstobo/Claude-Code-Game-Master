import os
from pathlib import Path

# Use relative path from current directory
chunks_dir = Path('world-state/campaigns/dungeon-crawler-carl/chunks')
print(f"Path: {chunks_dir}")
print(f"Exists: {chunks_dir.exists()}")
print(f"Is dir: {chunks_dir.is_dir()}")

# Use glob with pathlib
chunk_files = sorted(chunks_dir.glob('chunk_*.txt'))
print(f"Found {len(chunk_files)} files")
print(f"First 5: {[f.name for f in chunk_files[:5]]}")

# Also check as absolute
abs_path = chunks_dir.absolute()
print(f"\nAbsolute path: {abs_path}")
print(f"Absolute exists: {abs_path.exists()}")
