#!/usr/bin/env python3
"""
Deduplicate and merge multiple movie collections with intelligent merging strategies.
This script combines movies from different sources while preserving the best data from each.
"""

import json
import logging
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any, Set, Tuple
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deduplication.log'),
        logging.StreamHandler()
    ]
)

class MovieDeduplicator:
    def __init__(self):
        self.movies_by_imdb: Dict[str, Dict] = {}
        self.movies_by_title_year: Dict[str, Dict] = {}
        self.movies_by_tmdb: Dict[str, Dict] = {}
        self.duplicate_groups: List[List[Dict]] = []
        self.merge_stats = {
            'total_processed': 0,
            'unique_imdb': 0,
            'unique_title_year': 0,
            'duplicates_found': 0,
            'merges_performed': 0
        }
        
    def normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        if not title:
            return ""
        return title.lower().strip()
        
    def normalize_year(self, year: str) -> str:
        """Normalize year for comparison"""
        if not year:
            return ""
        # Extract 4-digit year
        import re
        match = re.search(r'\b(19\d{2}|20\d{2})\b', str(year))
        return match.group(1) if match else ""
        
    def create_movie_key(self, movie: Dict) -> Tuple[str, str, str]:
        """Create normalized keys for a movie"""
        title = self.normalize_title(movie.get('title', ''))
        year = self.normalize_year(movie.get('year', ''))
        imdb_id = movie.get('imdb_id', '').strip()
        tmdb_id = str(movie.get('tmdb_id', '')).strip()
        
        return title, year, imdb_id, tmdb_id
        
    def load_collection(self, file_path: str) -> List[Dict]:
        """Load a movie collection from JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                movies = data.get('movies', [])
                logging.info(f"Loaded {len(movies)} movies from {file_path}")
                return movies
        except Exception as e:
            logging.error(f"Failed to load {file_path}: {e}")
            return []
            
    def calculate_data_richness(self, movie: Dict) -> int:
        """Calculate a score for how rich/complete the movie data is"""
        score = 0
        
        # Basic fields
        if movie.get('title'): score += 1
        if movie.get('year'): score += 1
        if movie.get('director'): score += 1
        if movie.get('plot_summary'): score += 2  # Plot is valuable
        
        # IDs (very important for deduplication)
        if movie.get('imdb_id'): score += 3
        if movie.get('tmdb_id'): score += 2
        
        # Genres and metadata
        if movie.get('genre_tags'): score += len(movie['genre_tags'])
        if movie.get('critic_reviews'): score += len(movie['critic_reviews'])
        if movie.get('user_reviews'): score += len(movie['user_reviews'])
        
        # Visual style and other metadata
        if movie.get('visual_style'): score += 1
        
        return score
        
    def merge_movie_data(self, existing: Dict, new: Dict) -> Dict:
        """Intelligently merge two movie records, preferring richer data"""
        merged = existing.copy()
        
        # Always prefer non-empty values, and longer strings for text fields
        text_fields = ['title', 'director', 'plot_summary', 'visual_style']
        for field in text_fields:
            existing_val = existing.get(field, '')
            new_val = new.get(field, '')
            
            if new_val and (not existing_val or len(str(new_val)) > len(str(existing_val))):
                merged[field] = new_val
                
        # For lists, merge and deduplicate
        list_fields = ['genre_tags', 'critic_reviews', 'user_reviews']
        for field in list_fields:
            existing_list = existing.get(field, [])
            new_list = new.get(field, [])
            
            if new_list:
                # Combine and deduplicate
                combined = list(set(existing_list + new_list))
                merged[field] = combined
                
        # For IDs, prefer the one that exists
        id_fields = ['imdb_id', 'tmdb_id']
        for field in id_fields:
            if new.get(field) and not existing.get(field):
                merged[field] = new[field]
                
        # For year, prefer the more specific one
        if new.get('year') and existing.get('year'):
            # If one is more specific (has month/day), prefer it
            new_year = str(new['year'])
            existing_year = str(existing['year'])
            
            if len(new_year) > len(existing_year) or (len(new_year) == len(existing_year) and new_year > existing_year):
                merged['year'] = new['year']
                
        return merged
        
    def add_movie(self, movie: Dict, source: str = "unknown") -> bool:
        """Add a movie to the deduplication system"""
        self.merge_stats['total_processed'] += 1
        
        title, year, imdb_id, tmdb_id = self.create_movie_key(movie)
        
        # Add source tracking
        movie['_source'] = source
        
        # Primary deduplication by IMDb ID
        if imdb_id:
            if imdb_id in self.movies_by_imdb:
                # Merge with existing
                existing = self.movies_by_imdb[imdb_id]
                merged = self.merge_movie_data(existing, movie)
                self.movies_by_imdb[imdb_id] = merged
                self.merge_stats['merges_performed'] += 1
                logging.debug(f"Merged by IMDb ID: {title} ({year})")
            else:
                self.movies_by_imdb[imdb_id] = movie
                self.merge_stats['unique_imdb'] += 1
            return True
            
        # Secondary deduplication by TMDB ID
        if tmdb_id and tmdb_id != 'None':
            if tmdb_id in self.movies_by_tmdb:
                existing = self.movies_by_tmdb[tmdb_id]
                merged = self.merge_movie_data(existing, movie)
                self.movies_by_tmdb[tmdb_id] = merged
                self.merge_stats['merges_performed'] += 1
                logging.debug(f"Merged by TMDB ID: {title} ({year})")
            else:
                self.movies_by_tmdb[tmdb_id] = movie
            return True
            
        # Fallback deduplication by title + year
        if title and year:
            key = f"{title}_{year}"
            if key in self.movies_by_title_year:
                existing = self.movies_by_title_year[key]
                merged = self.merge_movie_data(existing, movie)
                self.movies_by_title_year[key] = merged
                self.merge_stats['merges_performed'] += 1
                logging.debug(f"Merged by title+year: {title} ({year})")
            else:
                self.movies_by_title_year[key] = movie
                self.merge_stats['unique_title_year'] += 1
            return True
            
        # If no good key, add as-is (shouldn't happen often)
        logging.warning(f"Movie with no good deduplication key: {title} ({year})")
        return False
        
    def process_collections(self, file_paths: List[str]) -> List[Dict]:
        """Process multiple collections and return deduplicated movies"""
        logging.info(f"Processing {len(file_paths)} collections...")
        
        for file_path in file_paths:
            if not Path(file_path).exists():
                logging.warning(f"File not found: {file_path}")
                continue
                
            source = Path(file_path).stem
            movies = self.load_collection(file_path)
            
            for movie in movies:
                self.add_movie(movie, source)
                
        # Combine all deduplication methods
        all_movies = []
        
        # Add movies from IMDb deduplication (highest priority)
        for movie in self.movies_by_imdb.values():
            all_movies.append(movie)
            
        # Add movies from TMDB deduplication (medium priority)
        for movie in self.movies_by_tmdb.values():
            if not movie.get('imdb_id'):  # Only if not already added via IMDb
                all_movies.append(movie)
                
        # Add movies from title+year deduplication (lowest priority)
        for movie in self.movies_by_title_year.values():
            if not movie.get('imdb_id') and not movie.get('tmdb_id'):  # Only if not already added
                all_movies.append(movie)
                
        self.merge_stats['duplicates_found'] = (
            self.merge_stats['total_processed'] - len(all_movies)
        )
        
        return all_movies
        
    def generate_report(self, movies: List[Dict]) -> Dict[str, Any]:
        """Generate a detailed report about the deduplication process"""
        if not movies:
            return {}
            
        # Basic stats
        total_movies = len(movies)
        
        # Year analysis
        years = [m.get('year', '') for m in movies if m.get('year')]
        year_counter = Counter(years)
        
        # Genre analysis
        all_genres = []
        for m in movies:
            all_genres.extend(m.get('genre_tags', []))
        genre_counter = Counter(all_genres)
        
        # Director analysis
        directors = [m.get('director', '') for m in movies if m.get('director')]
        director_counter = Counter(directors)
        
        # Source analysis
        sources = [m.get('_source', 'unknown') for m in movies]
        source_counter = Counter(sources)
        
        # ID coverage
        imdb_coverage = sum(1 for m in movies if m.get('imdb_id')) / total_movies * 100
        tmdb_coverage = sum(1 for m in movies if m.get('tmdb_id')) / total_movies * 100
        
        # Data completeness
        has_plot = sum(1 for m in movies if m.get('plot_summary')) / total_movies * 100
        has_director = sum(1 for m in movies if m.get('director')) / total_movies * 100
        
        report = {
            'total_movies': total_movies,
            'deduplication_stats': self.merge_stats,
            'year_distribution': dict(year_counter.most_common(10)),
            'top_genres': dict(genre_counter.most_common(15)),
            'top_directors': dict(director_counter.most_common(10)),
            'source_distribution': dict(source_counter),
            'data_quality': {
                'imdb_coverage': imdb_coverage,
                'tmdb_coverage': tmdb_coverage,
                'has_plot': has_plot,
                'has_director': has_director
            }
        }
        
        return report
        
    def save_results(self, movies: List[Dict], output_file: str, report: Dict[str, Any]):
        """Save deduplicated movies and report"""
        # Save movies
        output_data = {'movies': movies}
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        # Save report
        report_file = output_file.replace('.json', '_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        logging.info(f"Saved {len(movies)} movies to {output_file}")
        logging.info(f"Saved report to {report_file}")

def find_collection_files(directory: str = ".") -> List[str]:
    """Find all collection JSON files in the directory"""
    directory = Path(directory)
    pattern = "*.json"
    
    # Look for collection files (exclude existing profile files and reports)
    exclude_patterns = [
        "movie_profiles",
        "report",
        "user_ratings",
        "mock_movie_data"
    ]
    
    files = []
    for file_path in directory.glob(pattern):
        if not any(pattern in file_path.name for pattern in exclude_patterns):
            files.append(str(file_path))
            
    return sorted(files)

def main():
    parser = argparse.ArgumentParser(description="Deduplicate and merge movie collections")
    parser.add_argument("--files", nargs="+", help="Specific files to process")
    parser.add_argument("--directory", default=".", help="Directory to search for collection files")
    parser.add_argument("--output", default="merged_movie_data.json", help="Output file name")
    parser.add_argument("--auto-find", action="store_true", help="Automatically find collection files")
    
    args = parser.parse_args()
    
    # Determine which files to process
    if args.files:
        file_paths = args.files
    elif args.auto_find:
        file_paths = find_collection_files(args.directory)
    else:
        # Default: look for common collection patterns
        file_paths = find_collection_files(args.directory)
        
    if not file_paths:
        logging.error("No collection files found to process")
        return
        
    logging.info(f"Found {len(file_paths)} collection files to process:")
    for file_path in file_paths:
        logging.info(f"  - {file_path}")
        
    # Process collections
    deduplicator = MovieDeduplicator()
    movies = deduplicator.process_collections(file_paths)
    
    # Generate report
    report = deduplicator.generate_report(movies)
    
    # Print summary
    logging.info(f"\n{'='*60}")
    logging.info("DEDUPLICATION SUMMARY")
    logging.info(f"{'='*60}")
    logging.info(f"Total movies processed: {deduplicator.merge_stats['total_processed']}")
    logging.info(f"Unique movies after deduplication: {len(movies)}")
    logging.info(f"Duplicates removed: {deduplicator.merge_stats['duplicates_found']}")
    logging.info(f"Merges performed: {deduplicator.merge_stats['merges_performed']}")
    
    if report:
        logging.info(f"\nData Quality:")
        quality = report['data_quality']
        logging.info(f"  IMDB coverage: {quality['imdb_coverage']:.1f}%")
        logging.info(f"  TMDB coverage: {quality['tmdb_coverage']:.1f}%")
        logging.info(f"  Has plot summary: {quality['has_plot']:.1f}%")
        logging.info(f"  Has director: {quality['has_director']:.1f}%")
        
        logging.info(f"\nTop genres:")
        for genre, count in list(report['top_genres'].items())[:5]:
            logging.info(f"  {genre}: {count}")
            
    # Save results
    deduplicator.save_results(movies, args.output, report)
    
    logging.info(f"\n✓ Deduplication complete! Check {args.output} for results.")

if __name__ == "__main__":
    main()
