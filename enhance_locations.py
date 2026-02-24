import os
import json
import re
from pathlib import Path
from collections import defaultdict

chunks_dir = "world-state/campaigns/dungeon-crawler-carl/chunks"
output_dir = "world-state/campaigns/dungeon-crawler-carl/extracted"

locations = {}

# Read all chunks and extract comprehensive location information
chunk_files = sorted(Path(chunks_dir).glob("chunk_*.txt"))

for chunk_file in chunk_files:
    try:
        with open(chunk_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Extract station mentions with their numbers and surrounding context
            station_pattern = r'(?:station|Station)(?:\s+number)?\s+(\d+)'
            for match in re.finditer(station_pattern, content, re.IGNORECASE):
                station_num = match.group(1)
                station_key = f"Station {station_num}"
                
                if station_key not in locations:
                    locations[station_key] = {
                        "name": station_key,
                        "type": "station",
                        "station_number": int(station_num),
                        "mentions": 0,
                        "features": set(),
                        "connections": set(),
                        "chunks": set(),
                        "descriptions": set()
                    }
                
                locations[station_key]["mentions"] += 1
                locations[station_key]["chunks"].add(chunk_file.name)
                
                # Get surrounding context (500 chars)
                start = max(0, match.start() - 250)
                end = min(len(content), match.end() + 250)
                context = content[start:end].strip()
                
                # Extract features
                context_lower = context.lower()
                if "transfer" in context_lower or "traveler" in context_lower:
                    locations[station_key]["features"].add("Transfer Station")
                if "mora" in context_lower:
                    locations[station_key]["features"].add("Mora Station")
                if "sirin" in context_lower:
                    locations[station_key]["features"].add("Sirin Station")
                if "monster" in context_lower or "creature" in context_lower or "enemy" in context_lower:
                    locations[station_key]["features"].add("Contains monsters")
                if "safe" in context_lower or "refuge" in context_lower:
                    locations[station_key]["features"].add("Safe haven")
                if "trap" in context_lower:
                    locations[station_key]["features"].add("Trapped area")
                if "guard" in context_lower:
                    locations[station_key]["features"].add("Guarded")
                
                locations[station_key]["descriptions"].add(context[:200])
                
                # Find connected stations (look for references to next/previous stations)
                adjacent = re.findall(r'station\s+(?:number\s+)?(\d+)', context, re.IGNORECASE)
                for adj_num in adjacent:
                    if adj_num != station_num:
                        locations[station_key]["connections"].add(f"Station {adj_num}")
            
            # Extract car mentions with context
            car_pattern = r'(?:car|Car)(?:\s+number)?\s+(\d+)'
            for match in re.finditer(car_pattern, content, re.IGNORECASE):
                car_num = match.group(1)
                car_key = f"Car {car_num}"
                
                if car_key not in locations:
                    locations[car_key] = {
                        "name": car_key,
                        "type": "train_car",
                        "car_number": int(car_num),
                        "mentions": 0,
                        "features": set(),
                        "connections": set(),
                        "chunks": set(),
                        "descriptions": set()
                    }
                
                locations[car_key]["mentions"] += 1
                locations[car_key]["chunks"].add(chunk_file.name)
                
                # Get surrounding context
                start = max(0, match.start() - 200)
                end = min(len(content), match.end() + 200)
                context = content[start:end].strip()
                
                # Extract features
                context_lower = context.lower()
                if "door" in context_lower:
                    locations[car_key]["features"].add("Has doors")
                if "drek" in context_lower:
                    locations[car_key]["features"].add("Inhabited by Dreks")
                if "ghoul" in context_lower:
                    locations[car_key]["features"].add("Inhabited by Ghouls")
                if "monster" in context_lower or "creature" in context_lower:
                    locations[car_key]["features"].add("Contains monsters")
                if "empty" in context_lower:
                    locations[car_key]["features"].add("Empty/Abandoned")
                if "safe" in context_lower:
                    locations[car_key]["features"].add("Safe area")
                if "trap" in context_lower:
                    locations[car_key]["features"].add("Trapped")
                
                locations[car_key]["descriptions"].add(context[:150])
                
                # Find adjacent cars
                adjacent = re.findall(r'car\s+(?:number\s+)?(\d+)', context, re.IGNORECASE)
                for adj_num in adjacent:
                    if adj_num != car_num:
                        locations[car_key]["connections"].add(f"Car {adj_num}")
    
    except Exception as e:
        print(f"Error processing {chunk_file.name}: {e}")

# Convert sets to lists and prepare final output
locations_output = {}

for name, data in sorted(locations.items()):
    clean_data = {
        "name": data["name"],
        "type": data["type"],
        "mentions": data["mentions"],
        "features": sorted(list(data["features"])) if data["features"] else [],
        "connections": sorted(list(data["connections"])) if data["connections"] else [],
        "chunks_referenced": sorted(list(data["chunks"])),
        "description": list(data["descriptions"])[0][:250] if data["descriptions"] else ""
    }
    
    if "station_number" in data:
        clean_data["station_number"] = data["station_number"]
    if "car_number" in data:
        clean_data["car_number"] = data["car_number"]
    
    locations_output[name] = clean_data

# Create final output
output = {
    "metadata": {
        "source": "The Dungeon Anarchist's Cookbook Book 3",
        "total_chunks_scanned": len(chunk_files),
        "total_locations_extracted": len(locations_output),
        "extraction_method": "comprehensive_regex_pattern_matching",
        "location_types_found": ["train_car", "station"]
    },
    "locations": locations_output
}

# Write to file
output_file = Path(output_dir) / "locations.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"Location extraction complete!")
print(f"Total locations found: {len(locations_output)}")
print(f"Output file: {output_file}")
print(f"\nLocation summary:")
print(f"  Stations: {sum(1 for loc in locations_output.values() if loc['type'] == 'station')}")
print(f"  Train Cars: {sum(1 for loc in locations_output.values() if loc['type'] == 'train_car')}")

