#!/usr/bin/env python3
"""
Debug script to find why Maborosi is missing from the M section
"""

import json

def debug_missing_movies():
    print("🔍 Debugging missing movies in M section...")
    
    # Load the data files
    with open('movie_profiles_merged.json', 'r', encoding='utf-8') as f:
        profiles = json.load(f)
    
    with open('merged_movie_data_with_images.json', 'r', encoding='utf-8') as f:
        images_data = json.load(f)
    
    # Simulate frontend processing exactly
    def makeKey(title):
        return str(title or '').lower().strip()
    
    def normalizeMovie(obj):
        return {
            'title': str(obj.get('title') or 'Untitled'),
            'director': str(obj.get('director') or ''),
            'year': str(obj.get('year') or ''),
            'poster_url': str(obj.get('poster_url') or ''),
            'backdrop_url': str(obj.get('backdrop_url') or ''),
            'emotional_tone': [obj.get('primary_emotional_tone'), obj.get('secondary_emotional_tone')] if obj.get('primary_emotional_tone') else [],
            'themes': [obj.get('primary_theme'), obj.get('secondary_theme')] if obj.get('primary_theme') else [],
        }
    
    # Create image data lookup
    movieInfo = {}
    for movie in images_data['movies']:
        key = makeKey(movie['title'])
        movieInfo[key] = {
            'director': movie.get('director', ''),
            'year': movie.get('year', ''),
            'poster_url': movie.get('poster_url', ''),
            'backdrop_url': movie.get('backdrop_url', '')
        }
    
    # Process movies like frontend
    processed_movies = []
    for title, obj in profiles.items():
        m = normalizeMovie(obj)
        key = makeKey(m['title'])
        
        # Merge with image data if available
        if key in movieInfo:
            originalInfo = movieInfo[key]
            m['director'] = originalInfo['director']
            m['year'] = originalInfo['year']
            m['poster_url'] = originalInfo['poster_url']
            m['backdrop_url'] = originalInfo['backdrop_url']
        
        processed_movies.append(m)
    
    # Sort like frontend
    processed_movies.sort(key=lambda x: x['title'])
    
    # Find movies in the M section (around M*A*S*H and Mad Heidi)
    m_section_movies = []
    for i, movie in enumerate(processed_movies):
        if movie['title'].startswith('M'):
            m_section_movies.append((i, movie))
    
    print(f"📊 Found {len(m_section_movies)} movies starting with 'M'")
    
    # Show movies around M*A*S*H and Mad Heidi
    print(f"\n🔍 Movies in M section:")
    for i, movie in m_section_movies:
        if 'M*A*S*H' in movie['title'] or 'Mad Heidi' in movie['title'] or 'Maborosi' in movie['title']:
            print(f"   {i:3d}: {movie['title']} ({movie['year']}) - {movie['director']}")
    
    # Show a broader range around where Maborosi should be
    print(f"\n🔍 Movies around position 567 (where Maborosi should be):")
    start_idx = max(0, 560)
    end_idx = min(len(processed_movies), 580)
    
    for i in range(start_idx, end_idx):
        movie = processed_movies[i]
        marker = ">>> " if 'Maborosi' in movie['title'] else "    "
        print(f"   {marker}{i:3d}: {movie['title']} ({movie['year']}) - {movie['director']}")
    
    # Check if Maborosi exists at all
    maborosi_found = False
    for i, movie in enumerate(processed_movies):
        if movie['title'] == 'Maborosi':
            maborosi_found = True
            print(f"\n✅ Maborosi found at position {i}")
            print(f"   Title: {movie['title']}")
            print(f"   Director: {movie['director']}")
            print(f"   Year: {movie['year']}")
            print(f"   Poster: {movie['poster_url'][:50]}..." if movie['poster_url'] else "   Poster: None")
            break
    
    if not maborosi_found:
        print(f"\n❌ Maborosi NOT FOUND in processed movies!")
        
        # Check if it exists in raw profiles
        if 'Maborosi' in profiles:
            print(f"   But Maborosi exists in raw profiles data")
            raw_maborosi = profiles['Maborosi']
            print(f"   Raw title: {raw_maborosi.get('title')}")
            print(f"   Raw director: {raw_maborosi.get('director')}")
        else:
            print(f"   Maborosi does not exist in raw profiles data")
    
    # Check for any movies with similar titles
    print(f"\n🔍 Movies with 'Mabor' in title:")
    for i, movie in enumerate(processed_movies):
        if 'mabor' in movie['title'].lower():
            print(f"   {i:3d}: {movie['title']} ({movie['year']}) - {movie['director']}")
    
    # Check for any Koreeda movies in the M section
    print(f"\n🔍 Koreeda movies in M section:")
    for i, movie in m_section_movies:
        if movie['director'] == 'Hirokazu Kore-eda':
            print(f"   {i:3d}: {movie['title']} ({movie['year']}) - {movie['director']}")

if __name__ == "__main__":
    debug_missing_movies()
