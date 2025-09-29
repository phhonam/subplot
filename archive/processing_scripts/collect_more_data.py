#!/usr/bin/env python3
"""
Enhanced movie data collection script with rate limiting, error handling, and batch processing.
This script implements the comprehensive collection strategy for TMDB + OMDB enrichment.
"""

import subprocess
import json
import time
import logging
from pathlib import Path
from collections import Counter
from typing import List, Dict, Any
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('collection.log'),
        logging.StreamHandler()
    ]
)

class MovieDataCollector:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.collections = []
        
    def add_collection(self, name: str, args: List[str], description: str = ""):
        """Add a collection configuration"""
        self.collections.append({
            "name": name,
            "args": args,
            "description": description,
            "output_file": f"{name}.json"
        })
        
    def run_collection(self, collection: Dict[str, Any]) -> bool:
        """Run a single collection"""
        name = collection["name"]
        args = collection["args"]
        output_file = collection["output_file"]
        
        logging.info(f"Starting collection: {name}")
        if collection.get("description"):
            logging.info(f"Description: {collection['description']}")
            
        cmd = ["python3", "fetch_movies.py"] + args + ["--out", output_file]
        logging.info(f"Running command: {' '.join(cmd)}")
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            duration = time.time() - start_time
            
            # Log collection stats
            if Path(output_file).exists():
                with open(output_file, 'r') as f:
                    data = json.load(f)
                    movies = data.get('movies', [])
                    self.log_collection_stats(name, movies, duration)
                    
            logging.info(f"✓ Completed {name} in {duration:.1f}s")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"✗ Failed {name}: {e}")
            logging.error(f"Error output: {e.stderr}")
            return False
        except Exception as e:
            logging.error(f"✗ Unexpected error in {name}: {e}")
            return False
            
    def log_collection_stats(self, name: str, movies: List[Dict], duration: float):
        """Log statistics about collected movies"""
        if not movies:
            logging.warning(f"No movies collected for {name}")
            return
            
        # Basic stats
        total_movies = len(movies)
        
        # Year analysis
        years = [m.get('year', '') for m in movies if m.get('year') and m.get('year').isdigit()]
        year_range = f"{min(years)}-{max(years)}" if years else "No years"
        
        # Genre analysis
        all_genres = []
        for m in movies:
            all_genres.extend(m.get('genre_tags', []))
        top_genres = Counter(all_genres).most_common(5)
        
        # Director analysis
        directors = [m.get('director', '') for m in movies if m.get('director')]
        unique_directors = len(set(directors))
        
        # IMDB coverage
        imdb_coverage = sum(1 for m in movies if m.get('imdb_id')) / total_movies * 100
        
        logging.info(f"  📊 {name} Stats:")
        logging.info(f"     Movies: {total_movies}")
        logging.info(f"     Year range: {year_range}")
        logging.info(f"     Unique directors: {unique_directors}")
        logging.info(f"     IMDB coverage: {imdb_coverage:.1f}%")
        logging.info(f"     Top genres: {', '.join([f'{g}({c})' for g, c in top_genres])}")
        logging.info(f"     Rate: {total_movies/duration:.1f} movies/sec")
        
    def run_all_collections(self, start_from: int = 0) -> Dict[str, bool]:
        """Run all collections with progress tracking"""
        results = {}
        total = len(self.collections)
        
        logging.info(f"Starting batch collection of {total} datasets...")
        
        for i, collection in enumerate(self.collections[start_from:], start_from):
            logging.info(f"\n{'='*60}")
            logging.info(f"Collection {i+1}/{total}: {collection['name']}")
            logging.info(f"{'='*60}")
            
            success = self.run_collection(collection)
            results[collection['name']] = success
            
            if not success:
                logging.error(f"Collection {collection['name']} failed. Continuing with next...")
                
            # Brief pause between collections
            if i < total - 1:
                time.sleep(2)
                
        # Summary
        successful = sum(results.values())
        logging.info(f"\n{'='*60}")
        logging.info(f"COLLECTION SUMMARY: {successful}/{total} successful")
        logging.info(f"{'='*60}")
        
        for name, success in results.items():
            status = "✓" if success else "✗"
            logging.info(f"{status} {name}")
            
        return results

def setup_phase1_collections(collector: MovieDataCollector):
    """Phase 1: High-Quality Foundation"""
    logging.info("Setting up Phase 1: High-Quality Foundation collections")
    
    collector.add_collection(
        "top_rated_us_500",
        ["--source", "top_rated", "--count", "500", "--region", "US"],
        "Top 500 rated movies from US region (most reliable dataset)"
    )
    
    collector.add_collection(
        "top_rated_global_1000", 
        ["--source", "top_rated", "--count", "1000"],
        "Top 1000 rated movies globally"
    )
    
    collector.add_collection(
        "recent_acclaimed_2020s",
        ["--source", "discover", "--pages", "5", "--since", "2020-01-01", "--max-vote-count", "2000", "--min-vote-count", "50"],
        "Recent critically acclaimed movies (2020s)"
    )

def setup_phase2_collections(collector: MovieDataCollector):
    """Phase 2: Diversity Expansion"""
    logging.info("Setting up Phase 2: Diversity Expansion collections")
    
    collector.add_collection(
        "international_cinema",
        ["--source", "discover", "--pages", "8", "--languages", "es,fr,de,it,ja,ko,zh,hi", "--since", "2010-01-01"],
        "International cinema from multiple languages"
    )
    
    collector.add_collection(
        "indie_art_house",
        ["--source", "discover", "--pages", "10", "--max-vote-count", "1000", "--min-vote-count", "5", "--since", "2015-01-01"],
        "Independent and art-house films"
    )
    
    collector.add_collection(
        "classic_cinema",
        ["--source", "discover", "--pages", "6", "--since", "1950-01-01", "--max-vote-count", "5000", "--min-vote-count", "100"],
        "Classic cinema from 1950s onwards"
    )

def setup_phase3_collections(collector: MovieDataCollector):
    """Phase 3: Niche Collections"""
    logging.info("Setting up Phase 3: Niche Collections")
    
    collector.add_collection(
        "recent_indie",
        ["--source", "discover", "--pages", "6", "--since", "2018-01-01", "--max-vote-count", "800", "--min-vote-count", "10"],
        "Recent independent films"
    )
    
    collector.add_collection(
        "cult_films",
        ["--source", "discover", "--pages", "4", "--since", "1980-01-01", "--max-vote-count", "2000", "--min-vote-count", "20"],
        "Cult and underground films"
    )

def main():
    parser = argparse.ArgumentParser(description="Enhanced movie data collection")
    parser.add_argument("--phase", choices=["1", "2", "3", "all"], default="all", 
                       help="Which phase to run (1=foundation, 2=diversity, 3=niche, all=everything)")
    parser.add_argument("--start-from", type=int, default=0, 
                       help="Start from collection index (for resuming)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be collected without running")
    
    args = parser.parse_args()
    
    collector = MovieDataCollector()
    
    # Setup collections based on phase
    if args.phase in ["1", "all"]:
        setup_phase1_collections(collector)
    if args.phase in ["2", "all"]:
        setup_phase2_collections(collector)
    if args.phase in ["3", "all"]:
        setup_phase3_collections(collector)
    
    if args.dry_run:
        logging.info("DRY RUN - Collections that would be created:")
        for i, collection in enumerate(collector.collections):
            logging.info(f"{i+1}. {collection['name']}: {collection['description']}")
        return
    
    # Run collections
    results = collector.run_all_collections(start_from=args.start_from)
    
    # Final summary
    successful = sum(results.values())
    total = len(results)
    
    if successful == total:
        logging.info(f"\n🎉 All {total} collections completed successfully!")
    else:
        logging.warning(f"\n⚠️  {successful}/{total} collections completed successfully")
        
    logging.info(f"Check collection.log for detailed logs")
    logging.info(f"Next step: Run deduplicate_collections.py to merge and deduplicate")

if __name__ == "__main__":
    main()
