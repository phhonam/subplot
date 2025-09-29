#!/usr/bin/env python3
"""
Test script to simulate frontend data loading and check if Koreeda movies are processed correctly
"""

import json

def test_frontend_data_processing():
    print("🧪 Testing frontend data processing...")
    
    # Load the data files like the frontend does
    with open('movie_profiles_merged.json', 'r', encoding='utf-8') as f:
        profiles = json.load(f)
    
    with open('merged_movie_data_with_images.json', 'r', encoding='utf-8') as f:
        images_data = json.load(f)
    
    # Simulate the frontend's makeKey function
    def makeKey(title):
        return str(title or '').lower().strip()
    
    # Simulate the frontend's normalizeMovie function
    def normalizeMovie(obj):
        return {
            'title': str(obj.get('title') or 'Untitled'),
            'director': str(obj.get('director') or ''),
            'year': str(obj.get('year') or ''),
            'poster_url': str(obj.get('poster_url') or ''),
            'backdrop_url': str(obj.get('backdrop_url') or ''),
            'primary_emotional_tone': obj.get('primary_emotional_tone'),
            'secondary_emotional_tone': obj.get('secondary_emotional_tone'),
            'primary_theme': obj.get('primary_theme'),
            'secondary_theme': obj.get('secondary_theme'),
            'intensity_level': obj.get('intensity_level'),
            'pacing_style': str(obj.get('pacing_style') or ''),
            'visual_aesthetic': str(obj.get('visual_aesthetic') or ''),
            'target_audience': str(obj.get('target_audience') or ''),
            'similar_films': obj.get('similar_films', []),
            'cultural_context': obj.get('cultural_context', []),
            'narrative_structure': str(obj.get('narrative_structure') or ''),
            'energy_level': str(obj.get('energy_level') or ''),
            'discussion_topics': obj.get('discussion_topics', []),
            'card_description': str(obj.get('card_description') or ''),
            'profile_text': str(obj.get('profile_text') or ''),
        }
    
    # Create image data lookup like frontend does
    movieInfo = {}
    for movie in images_data['movies']:
        key = makeKey(movie['title'])
        movieInfo[key] = {
            'director': movie.get('director', ''),
            'year': movie.get('year', ''),
            'poster_url': movie.get('poster_url', ''),
            'backdrop_url': movie.get('backdrop_url', '')
        }
    
    # Process movies like frontend does
    processed_movies = []
    koreeda_movies = []
    
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
        
        # Check if it's a Koreeda movie
        if m['director'] == 'Hirokazu Kore-eda':
            koreeda_movies.append(m)
    
    # Sort like frontend does
    processed_movies.sort(key=lambda x: x['title'])
    
    print(f"📊 Total processed movies: {len(processed_movies)}")
    print(f"🎬 Koreeda movies found: {len(koreeda_movies)}")
    
    # Check specific movies
    test_movies = ['Maborosi', 'Our Little Sister', 'Broker', 'After the Storm']
    
    print(f"\n🔍 Checking specific movies:")
    for movie_title in test_movies:
        found = False
        for movie in processed_movies:
            if movie['title'] == movie_title:
                found = True
                print(f"   ✅ {movie_title}")
                print(f"      Director: {movie['director']}")
                print(f"      Year: {movie['year']}")
                print(f"      Poster: {movie['poster_url'][:50]}..." if movie['poster_url'] else "      Poster: None")
                print(f"      Primary Theme: {movie['primary_theme']}")
                print(f"      Emotional Tone: {movie['primary_emotional_tone']}")
                break
        
        if not found:
            print(f"   ❌ {movie_title} - NOT FOUND")
        print()
    
    # Check if Maborosi is in the right position alphabetically
    print("🔍 Checking Maborosi position in sorted list:")
    for i, movie in enumerate(processed_movies):
        if movie['title'] == 'Maborosi':
            print(f"   Maborosi found at position {i}")
            print(f"   Movies around it:")
            start = max(0, i-3)
            end = min(len(processed_movies), i+4)
            for j in range(start, end):
                marker = ">>> " if j == i else "    "
                print(f"   {marker}{j}: {processed_movies[j]['title']}")
            break
    else:
        print("   ❌ Maborosi not found in processed movies!")
    
    # Check for any movies with missing critical data
    print(f"\n🔍 Checking for movies with missing critical data:")
    missing_data_count = 0
    for movie in processed_movies:
        missing = []
        if not movie['title'] or movie['title'] == 'Untitled':
            missing.append('title')
        if not movie['director']:
            missing.append('director')
        if not movie['year']:
            missing.append('year')
        if not movie['poster_url']:
            missing.append('poster_url')
        
        if missing:
            missing_data_count += 1
            if missing_data_count <= 5:  # Show first 5
                print(f"   ⚠️  {movie['title']}: missing {', '.join(missing)}")
    
    if missing_data_count > 5:
        print(f"   ... and {missing_data_count - 5} more movies with missing data")
    
    print(f"\n📈 Summary:")
    print(f"   Total movies: {len(processed_movies)}")
    print(f"   Koreeda movies: {len(koreeda_movies)}")
    print(f"   Movies with missing data: {missing_data_count}")

if __name__ == "__main__":
    test_frontend_data_processing()
