#!/usr/bin/env python3
"""
Diagnose and fix incorrect director attributions in movie profiles.
This script helps identify movies that may have incorrect director information
and provides options to fix them.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

def load_movie_profiles(file_path: str = "movie_profiles_merged.json") -> Dict:
    """Load movie profiles from JSON file"""
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_director_name(name: str) -> str:
    """Normalize director name for comparison"""
    if not name:
        return ""
    return re.sub(r'\s+', ' ', name.strip().lower())

def find_director_inconsistencies(profiles: Dict) -> Dict[str, List[str]]:
    """Find movies that might have incorrect director attributions"""
    director_movies = defaultdict(list)
    inconsistencies = {}
    
    for title, profile in profiles.items():
        director = profile.get('director', '').strip()
        if not director:
            continue
            
        # Group movies by normalized director name
        normalized_director = normalize_director_name(director)
        director_movies[normalized_director].append((title, director))
    
    # Look for potential issues
    for normalized_director, movies in director_movies.items():
        if len(movies) > 1:
            # Check if all movies have the same director name (case variations)
            director_names = set(movie[1] for movie in movies)
            if len(director_names) > 1:
                inconsistencies[normalized_director] = movies
    
    return inconsistencies

def find_suspicious_directors(profiles: Dict) -> List[Tuple[str, str, str]]:
    """Find movies with potentially suspicious director names"""
    suspicious = []
    
    # Common patterns that might indicate incorrect attribution
    suspicious_patterns = [
        r'^[A-Z][a-z]+ [A-Z][a-z]+$',  # Simple "First Last" pattern
        r'^[A-Z]\. [A-Z][a-z]+$',      # "F. Lastname" pattern
        r'^[A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+$',  # "First M. Last" pattern
    ]
    
    for title, profile in profiles.items():
        director = profile.get('director', '').strip()
        if not director:
            continue
            
        # Check if director name matches suspicious patterns
        for pattern in suspicious_patterns:
            if re.match(pattern, director):
                suspicious.append((title, director, "Matches common name pattern"))
                break
    
    return suspicious

def find_movies_without_directors(profiles: Dict) -> List[str]:
    """Find movies that don't have director information"""
    missing_directors = []
    
    for title, profile in profiles.items():
        director = profile.get('director', '').strip()
        if not director:
            missing_directors.append(title)
    
    return missing_directors

def validate_director_attribution(profiles: Dict) -> Dict:
    """Comprehensive validation of director attributions"""
    print("🔍 Analyzing director attributions...")
    
    # Find inconsistencies
    inconsistencies = find_director_inconsistencies(profiles)
    
    # Find suspicious directors
    suspicious = find_suspicious_directors(profiles)
    
    # Find missing directors
    missing = find_movies_without_directors(profiles)
    
    # Count total movies with directors
    total_with_directors = sum(1 for p in profiles.values() if p.get('director', '').strip())
    
    results = {
        'total_movies': len(profiles),
        'movies_with_directors': total_with_directors,
        'movies_without_directors': len(missing),
        'inconsistencies': inconsistencies,
        'suspicious_directors': suspicious,
        'missing_directors': missing
    }
    
    return results

def print_validation_report(results: Dict):
    """Print a comprehensive validation report"""
    print(f"\n{'='*60}")
    print("DIRECTOR ATTRIBUTION VALIDATION REPORT")
    print(f"{'='*60}")
    
    print(f"📊 Total movies: {results['total_movies']}")
    print(f"🎬 Movies with directors: {results['movies_with_directors']}")
    print(f"❓ Movies without directors: {results['movies_without_directors']}")
    
    if results['inconsistencies']:
        print(f"\n⚠️  DIRECTOR INCONSISTENCIES ({len(results['inconsistencies'])} groups):")
        for normalized_director, movies in results['inconsistencies'].items():
            print(f"\n  Director: {normalized_director}")
            for title, director in movies:
                print(f"    - {title}: {director}")
    
    if results['suspicious_directors']:
        print(f"\n🔍 SUSPICIOUS DIRECTOR ATTRIBUTIONS ({len(results['suspicious_directors'])} movies):")
        for title, director, reason in results['suspicious_directors']:
            print(f"  - {title}: {director} ({reason})")
    
    if results['missing_directors']:
        print(f"\n❌ MOVIES WITHOUT DIRECTORS ({len(results['missing_directors'])} movies):")
        for title in results['missing_directors'][:10]:  # Show first 10
            print(f"  - {title}")
        if len(results['missing_directors']) > 10:
            print(f"  ... and {len(results['missing_directors']) - 10} more")

def main():
    """Main function to run the validation"""
    print("🎬 Director Attribution Validator")
    print("=" * 40)
    
    # Load movie profiles
    profiles = load_movie_profiles()
    if not profiles:
        return
    
    # Run validation
    results = validate_director_attribution(profiles)
    
    # Print report
    print_validation_report(results)
    
    # Save detailed results to file
    with open('director_validation_report.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed report saved to: director_validation_report.json")
    
    # Provide recommendations
    print(f"\n{'='*60}")
    print("RECOMMENDATIONS")
    print(f"{'='*60}")
    
    if results['inconsistencies']:
        print("1. Review director inconsistencies - some directors may have name variations")
        print("2. Consider standardizing director names across all movies")
    
    if results['suspicious_directors']:
        print("3. Review suspicious director attributions - they may be incorrect")
        print("4. Cross-reference with reliable sources (IMDb, TMDB)")
    
    if results['missing_directors']:
        print("5. Consider adding director information for movies that lack it")
        print("6. Use the director collection script to gather missing data")

if __name__ == "__main__":
    main()
