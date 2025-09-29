#!/usr/bin/env python3
"""
Integrate director-collected movies with existing merged dataset.
This script merges new director movies and their profiles into the main dataset.
"""

import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('director_integration.log'),
        logging.StreamHandler()
    ]
)

class DirectorDataIntegrator:
    def __init__(self):
        self.existing_movies = []
        self.existing_profiles = []
        self.new_movies = []
        self.new_profiles = []
        
    def load_existing_data(self, movies_file: str, profiles_file: str = None):
        """Load existing merged movie data and profiles"""
        # Load movies
        if Path(movies_file).exists():
            with open(movies_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.existing_movies = data.get('movies', [])
                logging.info(f"Loaded {len(self.existing_movies)} existing movies")
        else:
            logging.warning(f"Movies file not found: {movies_file}")
            
        # Load profiles if available
        if profiles_file and Path(profiles_file).exists():
            with open(profiles_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.existing_profiles = data.get('profiles', [])
                logging.info(f"Loaded {len(self.existing_profiles)} existing profiles")
        else:
            logging.warning("No existing profiles found")
            
    def load_director_data(self, movies_file: str, profiles_file: str = None):
        """Load new director movies and profiles"""
        # Load new movies
        if Path(movies_file).exists():
            with open(movies_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.new_movies = data.get('movies', [])
                logging.info(f"Loaded {len(self.new_movies)} new director movies")
        else:
            logging.error(f"Director movies file not found: {movies_file}")
            return False
            
        # Load new profiles if available
        if profiles_file and Path(profiles_file).exists():
            with open(profiles_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.new_profiles = data.get('profiles', [])
                logging.info(f"Loaded {len(self.new_profiles)} new director profiles")
        else:
            logging.warning("No director profiles found - will create basic profiles")
            
        return True
        
    def create_movie_identifier(self, movie: Dict[str, Any]) -> str:
        """Create a unique identifier for a movie"""
        if movie.get('imdb_id'):
            return f"imdb:{movie['imdb_id']}"
        elif movie.get('tmdb_id'):
            return f"tmdb:{movie['tmdb_id']}"
        else:
            title = movie.get('title', '').lower().strip()
            year = movie.get('year', '').strip()
            return f"title:{title}|year:{year}"
            
    def find_duplicates(self) -> Set[str]:
        """Find movies that already exist in the dataset"""
        existing_ids = set()
        for movie in self.existing_movies:
            existing_ids.add(self.create_movie_identifier(movie))
            
        duplicates = set()
        for movie in self.new_movies:
            movie_id = self.create_movie_identifier(movie)
            if movie_id in existing_ids:
                duplicates.add(movie_id)
                
        return duplicates
        
    def integrate_movies(self) -> List[Dict[str, Any]]:
        """Integrate new movies with existing ones, removing duplicates"""
        duplicates = self.find_duplicates()
        logging.info(f"Found {len(duplicates)} duplicate movies")
        
        # Filter out duplicates from new movies
        unique_new_movies = []
        for movie in self.new_movies:
            movie_id = self.create_movie_identifier(movie)
            if movie_id not in duplicates:
                unique_new_movies.append(movie)
            else:
                logging.info(f"  ⏭️  Skipping duplicate: {movie.get('title')} ({movie.get('year')})")
                
        # Combine all movies
        all_movies = self.existing_movies + unique_new_movies
        
        logging.info(f"Integrated {len(unique_new_movies)} new movies")
        logging.info(f"Total movies: {len(all_movies)}")
        
        return all_movies
        
    def integrate_profiles(self) -> List[Dict[str, Any]]:
        """Integrate new profiles with existing ones"""
        # Create a mapping of movie titles to profiles for new movies
        new_profile_map = {}
        for profile in self.new_profiles:
            title = profile.get('title', '').lower().strip()
            new_profile_map[title] = profile
            
        # Create a mapping of existing profiles
        existing_profile_map = {}
        for profile in self.existing_profiles:
            title = profile.get('title', '').lower().strip()
            existing_profile_map[title] = profile
            
        # Combine profiles, preferring new ones for new movies
        all_profiles = []
        processed_titles = set()
        
        # Add existing profiles
        for profile in self.existing_profiles:
            title = profile.get('title', '').lower().strip()
            all_profiles.append(profile)
            processed_titles.add(title)
            
        # Add new profiles for new movies
        for profile in self.new_profiles:
            title = profile.get('title', '').lower().strip()
            if title not in processed_titles:
                all_profiles.append(profile)
                processed_titles.add(title)
                
        logging.info(f"Integrated {len(self.new_profiles)} new profiles")
        logging.info(f"Total profiles: {len(all_profiles)}")
        
        return all_profiles
        
    def save_integrated_data(self, movies: List[Dict[str, Any]], 
                           profiles: List[Dict[str, Any]],
                           movies_output: str, profiles_output: str = None):
        """Save the integrated dataset"""
        # Save integrated movies
        movies_data = {
            "movies": movies,
            "metadata": {
                "total_movies": len(movies),
                "last_updated": datetime.now().isoformat(),
                "sources": ["existing", "director_collection"]
            }
        }
        
        with open(movies_output, 'w', encoding='utf-8') as f:
            json.dump(movies_data, f, indent=2, ensure_ascii=False)
            
        logging.info(f"✓ Saved {len(movies)} movies to {movies_output}")
        
        # Save integrated profiles if available
        if profiles and profiles_output:
            profiles_data = {
                "profiles": profiles,
                "metadata": {
                    "total_profiles": len(profiles),
                    "last_updated": datetime.now().isoformat(),
                    "sources": ["existing", "director_collection"]
                }
            }
            
            with open(profiles_output, 'w', encoding='utf-8') as f:
                json.dump(profiles_data, f, indent=2, ensure_ascii=False)
                
            logging.info(f"✓ Saved {len(profiles)} profiles to {profiles_output}")

def main():
    parser = argparse.ArgumentParser(description="Integrate director movies with existing dataset")
    parser.add_argument("--director-movies", required=True,
                       help="JSON file with director-collected movies")
    parser.add_argument("--director-profiles", 
                       help="JSON file with director movie profiles (optional)")
    parser.add_argument("--existing-movies", default="merged_movie_data.json",
                       help="Existing merged movies file")
    parser.add_argument("--existing-profiles", 
                       help="Existing movie profiles file (optional)")
    parser.add_argument("--output-movies", default="merged_movie_data_updated.json",
                       help="Output file for integrated movies")
    parser.add_argument("--output-profiles", 
                       help="Output file for integrated profiles (optional)")
    
    args = parser.parse_args()
    
    # Initialize integrator
    integrator = DirectorDataIntegrator()
    
    # Load existing data
    integrator.load_existing_data(args.existing_movies, args.existing_profiles)
    
    # Load director data
    if not integrator.load_director_data(args.director_movies, args.director_profiles):
        return
        
    # Integrate movies
    integrated_movies = integrator.integrate_movies()
    
    # Integrate profiles
    integrated_profiles = integrator.integrate_profiles()
    
    # Save integrated data
    integrator.save_integrated_data(
        integrated_movies, 
        integrated_profiles,
        args.output_movies,
        args.output_profiles
    )
    
    logging.info(f"\n{'='*60}")
    logging.info("INTEGRATION COMPLETE")
    logging.info(f"{'='*60}")
    logging.info(f"Movies: {len(integrated_movies)} total")
    logging.info(f"Profiles: {len(integrated_profiles)} total")
    logging.info(f"Updated movies saved to: {args.output_movies}")
    if args.output_profiles:
        logging.info(f"Updated profiles saved to: {args.output_profiles}")

if __name__ == "__main__":
    main()
