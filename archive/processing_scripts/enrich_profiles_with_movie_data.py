#!/usr/bin/env python3
"""
Enrich movie profiles with movie data (poster URLs, IMDB IDs, etc.)
"""

import json

# Load the profiles
print("Loading profiles...")
with open('movie_profiles_merged.json', 'r') as f:
    profiles = json.load(f)

print(f"Profiles loaded: {len(profiles)}")

# Load the movie data
print("Loading movie data...")
with open('merged_movie_data_updated.json', 'r') as f:
    movie_data = json.load(f)

movies = movie_data['movies']
print(f"Movies loaded: {len(movies)}")

# Create a lookup dictionary for movie data
movie_lookup = {}
for movie in movies:
    title = movie.get('title', '').strip().lower()
    movie_lookup[title] = movie

print(f"Movie lookup created: {len(movie_lookup)} entries")

# Enrich profiles with movie data
print("Enriching profiles with movie data...")
enriched_count = 0
for title, profile in profiles.items():
    movie_title_lower = title.strip().lower()
    if movie_title_lower in movie_lookup:
        movie_data = movie_lookup[movie_title_lower]
        
        # Add missing fields to profile
        profile['imdb_id'] = movie_data.get('imdb_id')
        profile['tmdb_id'] = movie_data.get('tmdb_id')
        profile['poster_url'] = movie_data.get('poster_url')
        profile['year'] = movie_data.get('year')
        profile['director'] = movie_data.get('director')
        profile['genre_tags'] = movie_data.get('genre_tags', [])
        profile['plot_summary'] = movie_data.get('plot_summary', '')
        
        enriched_count += 1

print(f"Enriched {enriched_count} profiles with movie data")

# Save the enriched profiles
print("Saving enriched profiles...")
with open('movie_profiles_merged.json', 'w') as f:
    json.dump(profiles, f, indent=2, ensure_ascii=False)

print("✅ Successfully enriched profiles with movie data!")
print(f"Final count: {len(profiles)} profiles with metadata")
