#!/usr/bin/env python3
"""
Director-based movie collection script for TMDB + OMDB enrichment.
This script searches for a director by name, retrieves their filmography,
enriches the data, and integrates with the existing movie recommender system.
"""

import os
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import requests
from datetime import datetime

# Import existing functions from fetch_movies.py
import sys
sys.path.append('.')
from fetch_movies import (
    load_env_from_dotenv, session_with_api_key, tmdb_get, 
    get_movie_details_and_credits, enrich_with_omdb, map_to_schema,
    tmdb_external_ids
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('director_collection.log'),
        logging.StreamHandler()
    ]
)

class DirectorMovieCollector:
    def __init__(self):
        self.tmdb_session = None
        self.omdb_api_key = None
        self.existing_movies = set()
        self.collected_movies = []
        
    def setup_apis(self):
        """Initialize API connections"""
        load_env_from_dotenv()
        tmdb_api_key = os.environ.get("TMDB_API_KEY")
        self.omdb_api_key = os.environ.get("OMDB_API_KEY")
        
        if not tmdb_api_key:
            raise SystemExit("TMDB_API_KEY is not set in environment or .env")
            
        self.tmdb_session = session_with_api_key(tmdb_api_key)
        logging.info("✓ API connections established")
        
    def load_existing_movies(self, merged_data_path: str = "merged_movie_data.json"):
        """Load existing movies to avoid duplicates"""
        if not Path(merged_data_path).exists():
            logging.warning(f"Existing movie data not found at {merged_data_path}")
            return
            
        try:
            with open(merged_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                movies = data.get('movies', [])
                
            # Create set of existing movie identifiers
            for movie in movies:
                if movie.get('imdb_id'):
                    self.existing_movies.add(f"imdb:{movie['imdb_id']}")
                if movie.get('tmdb_id'):
                    self.existing_movies.add(f"tmdb:{movie['tmdb_id']}")
                # Also add title+year combinations
                title = movie.get('title', '').lower().strip()
                year = movie.get('year', '').strip()
                if title and year:
                    self.existing_movies.add(f"title:{title}|year:{year}")
                    
            logging.info(f"✓ Loaded {len(movies)} existing movies for duplicate checking")
            
        except Exception as e:
            logging.error(f"Failed to load existing movies: {e}")
            
    def search_director(self, director_name: str) -> Optional[int]:
        """Search for director by name and return their TMDB person ID"""
        logging.info(f"Searching for director: {director_name}")
        
        params = {
            "query": director_name,
            "include_adult": "false"
        }
        
        try:
            data = tmdb_get(self.tmdb_session, "/search/person", params)
            results = data.get("results", [])
            
            if not results:
                logging.warning(f"No results found for director: {director_name}")
                return None
                
            # Find best match (exact name match preferred)
            director_name_lower = director_name.lower()
            for person in results:
                name = person.get("name", "").lower()
                if name == director_name_lower:
                    logging.info(f"✓ Found exact match: {person['name']} (ID: {person['id']})")
                    return person["id"]
                    
            # If no exact match, take the first result
            best_match = results[0]
            logging.info(f"✓ Found best match: {best_match['name']} (ID: {best_match['id']})")
            return best_match["id"]
            
        except Exception as e:
            logging.error(f"Failed to search for director {director_name}: {e}")
            return None
            
    def get_director_filmography(self, director_id: int, 
                                min_year: Optional[int] = None,
                                max_year: Optional[int] = None,
                                min_vote_count: int = 0,
                                include_adult: bool = False) -> List[Dict[str, Any]]:
        """Get all movies directed by the director"""
        logging.info(f"Fetching filmography for director ID: {director_id}")
        
        try:
            data = tmdb_get(self.tmdb_session, f"/person/{director_id}/movie_credits", {})
            crew_credits = data.get("crew", [])
            
            # Filter for directing credits only
            directed_movies = []
            for credit in crew_credits:
                if credit.get("job") == "Director":
                    # Apply filters
                    release_date = credit.get("release_date", "")
                    year = int(release_date[:4]) if release_date and len(release_date) >= 4 else 0
                    vote_count = credit.get("vote_count", 0)
                    adult = credit.get("adult", False)
                    
                    # Skip if filters don't match
                    if min_year and year < min_year:
                        continue
                    if max_year and year > max_year:
                        continue
                    if vote_count < min_vote_count:
                        continue
                    if adult and not include_adult:
                        continue
                        
                    directed_movies.append(credit)
                    
            logging.info(f"✓ Found {len(directed_movies)} directing credits")
            return directed_movies
            
        except Exception as e:
            logging.error(f"Failed to fetch filmography: {e}")
            return []
            
    def is_duplicate(self, movie: Dict[str, Any]) -> bool:
        """Check if movie already exists in our dataset"""
        # Check by IMDB ID
        if movie.get('imdb_id'):
            if f"imdb:{movie['imdb_id']}" in self.existing_movies:
                return True
                
        # Check by TMDB ID
        if movie.get('tmdb_id'):
            if f"tmdb:{movie['tmdb_id']}" in self.existing_movies:
                return True
                
        # Check by title+year
        title = movie.get('title', '').lower().strip()
        year = movie.get('year', '').strip()
        if title and year:
            if f"title:{title}|year:{year}" in self.existing_movies:
                return True
                
        return False
        
    def collect_movie_data(self, movie_credit: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Collect detailed data for a single movie"""
        tmdb_id = movie_credit.get("id")
        if not tmdb_id:
            return None
            
        try:
            # Get detailed movie information
            core = get_movie_details_and_credits(self.tmdb_session, tmdb_id)
            
            # Ensure we have IMDB ID
            if not core.get("imdb_id"):
                ext = tmdb_external_ids(self.tmdb_session, tmdb_id)
                if ext.get("imdb_id"):
                    core["imdb_id"] = ext["imdb_id"]
                    
            # Check for duplicates
            if self.is_duplicate(core):
                logging.info(f"  ⏭️  Skipping duplicate: {core.get('title')} ({core.get('year')})")
                return None
                
            # Add source tracking
            core["_source"] = f"director_collection_{datetime.now().strftime('%Y%m%d')}"
            
            # Enrich with OMDB
            core = enrich_with_omdb(core, self.omdb_api_key)
            
            # Map to standard schema
            movie_data = map_to_schema(core)
            
            logging.info(f"  ✓ Collected: {movie_data['title']} ({movie_data['year']})")
            return movie_data
            
        except Exception as e:
            logging.error(f"Failed to collect data for movie {tmdb_id}: {e}")
            return None
            
    def collect_director_movies(self, director_name: str, 
                               min_year: Optional[int] = None,
                               max_year: Optional[int] = None,
                               min_vote_count: int = 0,
                               include_adult: bool = False,
                               max_movies: Optional[int] = None) -> List[Dict[str, Any]]:
        """Main method to collect all movies by a director"""
        logging.info(f"\n{'='*60}")
        logging.info(f"COLLECTING MOVIES BY DIRECTOR: {director_name}")
        logging.info(f"{'='*60}")
        
        # Search for director
        director_id = self.search_director(director_name)
        if not director_id:
            logging.error(f"Could not find director: {director_name}")
            return []
            
        # Get filmography
        filmography = self.get_director_filmography(
            director_id, min_year, max_year, min_vote_count, include_adult
        )
        
        if not filmography:
            logging.warning("No movies found in filmography")
            return []
            
        # Sort by popularity (vote_count) descending
        filmography.sort(key=lambda x: x.get("vote_count", 0), reverse=True)
        
        # Limit number of movies if specified
        if max_movies:
            filmography = filmography[:max_movies]
            
        logging.info(f"Processing {len(filmography)} movies...")
        
        # Collect detailed data for each movie
        collected_movies = []
        for i, movie_credit in enumerate(filmography, 1):
            logging.info(f"\n[{i}/{len(filmography)}] Processing: {movie_credit.get('title')} ({movie_credit.get('release_date', '')[:4]})")
            
            movie_data = self.collect_movie_data(movie_credit)
            if movie_data:
                collected_movies.append(movie_data)
                
            # Rate limiting
            time.sleep(0.3)
            
        logging.info(f"\n✓ Collection complete: {len(collected_movies)} new movies collected")
        return collected_movies
        
    def save_collection(self, movies: List[Dict[str, Any]], output_file: str):
        """Save collected movies to JSON file"""
        if not movies:
            logging.warning("No movies to save")
            return
            
        data = {
            "movies": movies,
            "metadata": {
                "collection_date": datetime.now().isoformat(),
                "total_movies": len(movies),
                "source": "director_collection"
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logging.info(f"✓ Saved {len(movies)} movies to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Collect movies by director via TMDB + OMDB")
    parser.add_argument("director", help="Director name to search for")
    parser.add_argument("--output", "-o", default="director_movies.json", 
                       help="Output JSON file (default: director_movies.json)")
    parser.add_argument("--min-year", type=int, help="Minimum release year")
    parser.add_argument("--max-year", type=int, help="Maximum release year")
    parser.add_argument("--min-vote-count", type=int, default=0, 
                       help="Minimum vote count (default: 0)")
    parser.add_argument("--max-movies", type=int, 
                       help="Maximum number of movies to collect")
    parser.add_argument("--include-adult", action="store_true", 
                       help="Include adult movies")
    parser.add_argument("--existing-data", default="merged_movie_data.json",
                       help="Path to existing movie data for duplicate checking")
    
    args = parser.parse_args()
    
    # Initialize collector
    collector = DirectorMovieCollector()
    collector.setup_apis()
    collector.load_existing_movies(args.existing_data)
    
    # Collect movies
    movies = collector.collect_director_movies(
        director_name=args.director,
        min_year=args.min_year,
        max_year=args.max_year,
        min_vote_count=args.min_vote_count,
        include_adult=args.include_adult,
        max_movies=args.max_movies
    )
    
    # Save results
    collector.save_collection(movies, args.output)
    
    # Next steps
    if movies:
        logging.info(f"\n{'='*60}")
        logging.info("NEXT STEPS:")
        logging.info(f"{'='*60}")
        logging.info("1. Generate movie profiles:")
        logging.info(f"   python director_profile_generator.py --input {args.output}")
        logging.info("2. Merge with existing data:")
        logging.info(f"   python director_data_integrator.py --input {args.output}")
        logging.info("3. Update your recommender system with the new data")

if __name__ == "__main__":
    main()
