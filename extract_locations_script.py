import os
import json
import re
from pathlib import Path
from collections import defaultdict

chunks_dir = "world-state/campaigns/dungeon-crawler-carl/chunks"
output_dir = "world-state/campaigns/dungeon-crawler-carl/extracted"

# Create output directory
Path(output_dir).mkdir(parents=True, exist_ok=True)

locations = {}
location_mentions = defaultdict(int)

# Read all chunks
chunk_files = sorted(Path(chunks_dir).glob("chunk_*.txt"))
print(f"Found {len(chunk_files)} chunk files")

for chunk_file in chunk_files:
    try:
        with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Extract station numbers
            stations = re.findall(r'\bstation\s+(?:number\s+)?(\d+)', content, re.IGNORECASE)
            for station in stations:
                location_mentions[f"Station {station}"] += 1
            
            # Extract car numbers
            cars = re.findall(r'\bcar\s+(?:number\s+)?(\d+)', content, re.IGNORECASE)
            for car in cars:
                location_mentions[f"Car {car}"] += 1
            
            # Extract other named locations
            named_patterns = [
                (r'\bMora\b', 'Mora'),
                (r'\bDungeon\b', 'Dungeon'),
                (r'\bTraveler Transfer Station\b', 'Traveler Transfer Station'),
                (r'\bTransfer Station\b', 'Transfer Station'),
                (r'\bMordecai\b', 'Mordecai'),
            ]
            
            for pattern, name in named_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    location_mentions[name] += 1
                    
    except Exception as e:
        print(f"Error reading {chunk_file}: {e}")

# Sort by frequency
sorted_locations = sorted(location_mentions.items(), key=lambda x: x[1], reverse=True)
print(f"\nFound {len(sorted_locations)} unique locations")
print("\nTop 30 locations by mention frequency:")
for i, (loc, count) in enumerate(sorted_locations[:30], 1):
    print(f"  {i}. {loc}: {count} mentions")

# Now extract detailed information for each location
for chunk_file in chunk_files:
    try:
        with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Process stations
            stations = re.finditer(r'(?:station|Station)\s+(?:number\s+)?(\d+)', content, re.IGNORECASE)
            for match in stations:
                station_num = match.group(1)
                station_key = f"Station {station_num}"
                
                if station_key not in locations:
                    locations[station_key] = {
                        "name": station_key,
                        "type": "station",
                        "station_number": int(station_num),
                        "description": "",
                        "mentions": 0,
                        "features": set(),
                        "connections": set(),
                        "chunks": set()
                    }
                
                locations[station_key]["mentions"] += 1
                locations[station_key]["chunks"].add(str(chunk_file.name))
                
                # Extract surrounding context
                start = max(0, match.start() - 200)
                end = min(len(content), match.end() + 200)
                context = content[start:end]
                if context not in locations[station_key].get("_contexts", []):
                    if "_contexts" not in locations[station_key]:
                        locations[station_key]["_contexts"] = []
                    locations[station_key]["_contexts"].append(context)
            
            # Process cars
            cars = re.finditer(r'(?:car|Car)\s+(?:number\s+)?(\d+)', content, re.IGNORECASE)
            for match in cars:
                car_num = match.group(1)
                car_key = f"Car {car_num}"
                
                if car_key not in locations:
                    locations[car_key] = {
                        "name": car_key,
                        "type": "train_car",
                        "car_number": int(car_num),
                        "description": "",
                        "mentions": 0,
                        "features": set(),
                        "connections": set(),
                        "chunks": set()
                    }
                
                locations[car_key]["mentions"] += 1
                locations[car_key]["chunks"].add(str(chunk_file.name))
                
                # Extract surrounding context
                start = max(0, match.start() - 150)
                end = min(len(content), match.end() + 150)
                context = content[start:end]
                
                # Extract features from context
                if "drek" in context.lower():
                    locations[car_key]["features"].add("Inhabited by Dreks")
                if "door" in context.lower():
                    locations[car_key]["features"].add("Has doors")
                if "ghoul" in context.lower():
                    locations[car_key]["features"].add("Haunted - Ghouls")
                if "trap" in context.lower():
                    locations[car_key]["features"].add("Contains traps")
                    
    except Exception as e:
        print(f"Error processing {chunk_file.name}: {e}")

# Convert sets to lists for JSON serialization
locations_output = {}
for name, data in locations.items():
    clean_data = {
        "name": data["name"],
        "type": data["type"],
        "mentions": data["mentions"],
        "features": sorted(list(data["features"])) if data["features"] else [],
        "connections": sorted(list(data["connections"])) if data["connections"] else [],
        "chunks_referenced": sorted(list(data["chunks"]))
    }
    
    if "station_number" in data:
        clean_data["station_number"] = data["station_number"]
    if "car_number" in data:
        clean_data["car_number"] = data["car_number"]
    
    # Add first few contexts as descriptions
    if "_contexts" in data:
        clean_data["description"] = data["_contexts"][0][:300] if data["_contexts"] else ""
    
    locations_output[name] = clean_data

# Create final output structure
output = {
    "metadata": {
        "source": "The Dungeon Anarchist's Cookbook Book 3",
        "total_chunks_scanned": len(chunk_files),
        "total_locations_extracted": len(locations_output),
        "extraction_method": "regex_pattern_matching_with_context"
    },
    "locations": locations_output
}

# Write output
output_file = Path(output_dir) / "locations.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"\n✓ Extraction complete!")
print(f"✓ Total locations extracted: {len(locations_output)}")
print(f"✓ Output written to: {output_file}")

