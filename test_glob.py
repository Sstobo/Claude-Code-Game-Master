import glob
import os

chunks_dir = '/c/Users/SJG/Documents/CodePlayground/dm/Claude-Code-Game-Master/world-state/campaigns/dungeon-crawler-carl/chunks'
pattern = os.path.join(chunks_dir, 'chunk_*.txt')
print(f"Pattern: {pattern}")
print(f"Dir exists: {os.path.isdir(chunks_dir)}")

files = glob.glob(pattern)
print(f"Found {len(files)} files")
print(f"First 5: {files[:5]}")

# Try alternative
files2 = glob.glob(f"{chunks_dir}/chunk_*.txt")
print(f"Found with direct pattern: {len(files2)}")
