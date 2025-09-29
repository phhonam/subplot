#!/usr/bin/env python3
"""
Fix Maborosi's malformed similar_films data that's causing JavaScript rendering errors
"""

import json

def fix_maborosi_data():
    print("🔧 Fixing Maborosi's malformed data...")
    
    # Load the profiles
    with open('movie_profiles_merged.json', 'r', encoding='utf-8') as f:
        profiles = json.load(f)
    
    if 'Maborosi' not in profiles:
        print("❌ Maborosi not found in profiles!")
        return
    
    maborosi = profiles['Maborosi']
    print("📊 Current Maborosi similar_films:")
    print(f"   {maborosi.get('similar_films', [])}")
    
    # Fix the malformed similar_films
    original_similar_films = maborosi.get('similar_films', [])
    fixed_similar_films = []
    
    for film in original_similar_films:
        if isinstance(film, str):
            # Clean up the malformed string
            cleaned = film.strip()
            # Remove broken quotes and fix formatting
            cleaned = cleaned.replace('"', '').replace('"', '').strip()
            if cleaned and cleaned not in fixed_similar_films:
                fixed_similar_films.append(cleaned)
    
    print(f"📊 Fixed Maborosi similar_films:")
    print(f"   {fixed_similar_films}")
    
    # Update the profile
    maborosi['similar_films'] = fixed_similar_films
    
    # Check for other Koreeda movies with similar issues
    print(f"\n🔍 Checking other Koreeda movies for similar issues...")
    koreeda_movies_with_issues = []
    
    for title, profile in profiles.items():
        if profile.get('director') == 'Hirokazu Kore-eda':
            similar_films = profile.get('similar_films', [])
            has_issues = False
            
            for film in similar_films:
                if isinstance(film, str) and ('"' in film or '"' in film):
                    has_issues = True
                    break
            
            if has_issues:
                koreeda_movies_with_issues.append(title)
                print(f"   ⚠️  {title} has malformed similar_films: {similar_films}")
                
                # Fix this movie too
                fixed_films = []
                for film in similar_films:
                    if isinstance(film, str):
                        cleaned = film.strip().replace('"', '').replace('"', '').strip()
                        if cleaned and cleaned not in fixed_films:
                            fixed_films.append(cleaned)
                profile['similar_films'] = fixed_films
                print(f"   ✅ Fixed: {fixed_films}")
    
    if not koreeda_movies_with_issues:
        print("   ✅ No other Koreeda movies have similar issues")
    
    # Save the fixed profiles
    print(f"\n💾 Saving fixed profiles...")
    with open('movie_profiles_merged.json', 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Successfully fixed Maborosi and {len(koreeda_movies_with_issues)} other Koreeda movies!")
    print(f"🎉 Maborosi should now render properly on the homepage!")

if __name__ == "__main__":
    fix_maborosi_data()
