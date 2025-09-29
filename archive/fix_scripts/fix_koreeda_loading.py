#!/usr/bin/env python3
"""
Fix Koreeda movies loading issue by merging them into merged_movie_data_with_images.json

The problem: Koreeda movies appear in search but show up empty (no images, tags, metadata)
The cause: Koreeda movies are missing from merged_movie_data_with_images.json that the frontend loads
The solution: Merge Koreeda movies from merged_movie_data_final.json into merged_movie_data_with_images.json
"""

import json
import sys
from pathlib import Path

def fix_koreeda_movies():
    """Fix the Koreeda movies loading issue"""
    print("🎬 Fixing Koreeda movies loading issue...")
    
    # Check if required files exist
    required_files = [
        'merged_movie_data_with_images.json',
        'merged_movie_data_final.json'
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Error: Required file not found: {file_path}")
            return False
    
    try:
        # Load the current merged_movie_data_with_images.json
        print("📁 Loading merged_movie_data_with_images.json...")
        with open('merged_movie_data_with_images.json', 'r', encoding='utf-8') as f:
            current_data = json.load(f)
        
        print(f"   Current movies: {len(current_data['movies'])}")
        
        # Load the Koreeda movies from merged_movie_data_final.json
        print("📁 Loading Koreeda movies from merged_movie_data_final.json...")
        with open('merged_movie_data_final.json', 'r', encoding='utf-8') as f:
            final_data = json.load(f)
        
        # Find Koreeda movies (directed by Hirokazu Kore-eda)
        koreeda_movies = []
        for movie in final_data['movies']:
            if movie.get('director') == 'Hirokazu Kore-eda':
                koreeda_movies.append(movie)
                print(f"   Found Kore-eda movie: {movie['title']} ({movie.get('year', 'N/A')})")
        
        print(f"   Total Kore-eda movies found: {len(koreeda_movies)}")
        
        # Check which Koreeda movies are missing from merged_movie_data_with_images.json
        current_titles = {movie['title'] for movie in current_data['movies']}
        missing_koreeda = [movie for movie in koreeda_movies if movie['title'] not in current_titles]
        
        print(f"\n🔍 Missing Kore-eda movies in merged_movie_data_with_images.json: {len(missing_koreeda)}")
        for movie in missing_koreeda:
            print(f"   - {movie['title']} ({movie.get('year', 'N/A')})")
        
        if missing_koreeda:
            # Add missing Koreeda movies to the current data
            print(f"\n➕ Adding {len(missing_koreeda)} missing Kore-eda movies...")
            current_data['movies'].extend(missing_koreeda)
            
            # Save the updated file
            print("💾 Saving updated merged_movie_data_with_images.json...")
            with open('merged_movie_data_with_images.json', 'w', encoding='utf-8') as f:
                json.dump(current_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Successfully added {len(missing_koreeda)} Kore-eda movies!")
            print(f"   Total movies in merged_movie_data_with_images.json: {len(current_data['movies'])}")
            print("\n🎉 Koreeda movies should now appear properly on the homepage with images and metadata!")
            return True
        else:
            print("✅ All Kore-eda movies are already present in merged_movie_data_with_images.json")
            return True
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("KOREEDA MOVIES LOADING FIX")
    print("=" * 60)
    
    success = fix_koreeda_movies()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Fix completed successfully!")
        print("\nNext steps:")
        print("1. Refresh your browser")
        print("2. Check the homepage - Koreeda movies should now appear with images")
        print("3. Test search functionality")
    else:
        print("❌ Fix failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
