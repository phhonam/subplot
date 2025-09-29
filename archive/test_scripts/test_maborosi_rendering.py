#!/usr/bin/env python3
"""
Test script to check if Maborosi's data causes rendering issues
"""

import json

def test_maborosi_rendering():
    print("🧪 Testing Maborosi rendering...")
    
    # Load the data files
    with open('movie_profiles_merged.json', 'r', encoding='utf-8') as f:
        profiles = json.load(f)
    
    with open('merged_movie_data_with_images.json', 'r', encoding='utf-8') as f:
        images_data = json.load(f)
    
    # Get Maborosi's raw data
    if 'Maborosi' not in profiles:
        print("❌ Maborosi not found in profiles!")
        return
    
    maborosi_profile = profiles['Maborosi']
    print("📊 Maborosi profile data:")
    for key, value in maborosi_profile.items():
        if isinstance(value, str) and len(value) > 100:
            print(f"   {key}: {value[:100]}...")
        else:
            print(f"   {key}: {value}")
    
    # Check for potential rendering issues
    print(f"\n🔍 Checking for potential rendering issues:")
    
    # Check for null/undefined values
    issues = []
    for key, value in maborosi_profile.items():
        if value is None:
            issues.append(f"   ⚠️  {key} is None")
        elif isinstance(value, str) and value.strip() == "":
            issues.append(f"   ⚠️  {key} is empty string")
        elif isinstance(value, list) and len(value) == 0:
            issues.append(f"   ⚠️  {key} is empty list")
    
    if issues:
        print("   Found potential issues:")
        for issue in issues:
            print(issue)
    else:
        print("   ✅ No obvious data issues found")
    
    # Check for special characters that might cause issues
    print(f"\n🔍 Checking for special characters:")
    title = maborosi_profile.get('title', '')
    if any(ord(c) > 127 for c in title):
        print(f"   ⚠️  Title contains non-ASCII characters: {title}")
    else:
        print(f"   ✅ Title is ASCII: {title}")
    
    # Check poster URL
    poster_url = maborosi_profile.get('poster_url', '')
    if poster_url and not poster_url.startswith('http'):
        print(f"   ⚠️  Invalid poster URL: {poster_url}")
    elif not poster_url:
        print(f"   ⚠️  No poster URL")
    else:
        print(f"   ✅ Valid poster URL: {poster_url[:50]}...")
    
    # Simulate the frontend's normalizeMovie function
    def normalizeMovie(obj):
        try:
            return {
                'title': str(obj.get('title') or 'Untitled'),
                'director': str(obj.get('director') or ''),
                'year': str(obj.get('year') or ''),
                'poster_url': str(obj.get('poster_url') or ''),
                'backdrop_url': str(obj.get('backdrop_url') or ''),
                'emotional_tone': [obj.get('primary_emotional_tone'), obj.get('secondary_emotional_tone')] if obj.get('primary_emotional_tone') else [],
                'themes': [obj.get('primary_theme'), obj.get('secondary_theme')] if obj.get('primary_theme') else [],
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
        except Exception as e:
            print(f"   ❌ Error in normalizeMovie: {e}")
            return None
    
    # Test normalization
    print(f"\n🧪 Testing movie normalization:")
    normalized = normalizeMovie(maborosi_profile)
    if normalized:
        print("   ✅ Normalization successful")
        print(f"   Title: {normalized['title']}")
        print(f"   Director: {normalized['director']}")
        print(f"   Year: {normalized['year']}")
        print(f"   Poster: {normalized['poster_url'][:50]}..." if normalized['poster_url'] else "   Poster: None")
        print(f"   Emotional tone: {normalized['emotional_tone']}")
        print(f"   Themes: {normalized['themes']}")
    else:
        print("   ❌ Normalization failed")
    
    # Check if it would pass filters
    print(f"\n🔍 Testing filter compatibility:")
    
    # Test search filter
    search_terms = ['maborosi', 'kore-eda', 'japanese', 'drama']
    for term in search_terms:
        hay = ' '.join([
            normalized['title'],
            normalized['pacing_style'],
            normalized['energy_level'],
            normalized['visual_aesthetic'],
            normalized['target_audience'],
            normalized['narrative_structure'],
            normalized['profile_text'],
            ' '.join(normalized['emotional_tone']),
            ' '.join(normalized['themes']),
            ' '.join(normalized['similar_films']),
            ' '.join(normalized['cultural_context']),
            ' '.join(normalized['discussion_topics']),
        ]).lower()
        
        if term in hay:
            print(f"   ✅ Would match search term: '{term}'")
        else:
            print(f"   ❌ Would NOT match search term: '{term}'")

if __name__ == "__main__":
    test_maborosi_rendering()
