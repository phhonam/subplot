#!/usr/bin/env python3
"""
Merge Kore-eda profiles with the main movie_profiles_merged.json
"""

import json

# Load the main profiles (1,204 profiles)
print("Loading main profiles from backup...")
with open('movie_profiles_merged_backup.json', 'r') as f:
    main_profiles = json.load(f)

print(f"Main profiles loaded: {len(main_profiles)}")

# Load the Kore-eda profiles
print("Loading Kore-eda profiles...")
with open('koreeda_profiles.json', 'r') as f:
    koreeda_data = json.load(f)

koreeda_profiles = koreeda_data['profiles']
print(f"Kore-eda profiles loaded: {len(koreeda_profiles)}")

# Convert Kore-eda profiles to the main format (title -> profile dict)
koreeda_dict = {}
for profile in koreeda_profiles:
    title = profile['title']
    koreeda_dict[title] = profile

# Merge the profiles
print("Merging profiles...")
main_profiles.update(koreeda_dict)

print(f"Total profiles after merge: {len(main_profiles)}")

# Save the merged profiles
print("Saving merged profiles...")
with open('movie_profiles_merged.json', 'w') as f:
    json.dump(main_profiles, f, indent=2, ensure_ascii=False)

print("✅ Successfully merged Kore-eda profiles!")
print(f"Final count: {len(main_profiles)} profiles")
