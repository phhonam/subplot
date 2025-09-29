#!/usr/bin/env python3
"""
Enrichment Pipeline for Movie Database
Handles the processing of scraped movies through enrichment and profile generation
"""

import json
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime

from main import MovieRecommender
from fetch_movies import get_movie_details_and_credits, enrich_with_omdb
from merge_image_data import merge_image_data

class EnrichmentPipeline:
    def __init__(self, llm_provider="openai"):
        self.llm_provider = llm_provider
        self.tmdb_api_key = os.environ.get("TMDB_API_KEY")
        self.omdb_api_key = os.environ.get("OMDB_API_KEY")
        
        if not self.tmdb_api_key:
            raise ValueError("TMDB_API_KEY environment variable is required")
        
        self.session = requests.Session()
        self.session.params = {'api_key': self.tmdb_api_key}
        
        self.recommender = MovieRecommender(llm_provider)
        
    def enrich_movie_metadata(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich movie with additional metadata from TMDB and OMDb"""
        try:
            tmdb_id = movie.get('tmdb_id')
            if not tmdb_id:
                print(f"⚠️  No TMDB ID for {movie.get('title', 'Unknown')}")
                return movie
            
            # Get detailed movie information from TMDB
            detailed_movie = get_movie_details_and_credits(self.session, tmdb_id)
            
            # Merge the data
            enriched_movie = movie.copy()
            enriched_movie.update({
                'title': detailed_movie.get('title', movie.get('title', '')),
                'year': detailed_movie.get('year', movie.get('year', '')),
                'director': detailed_movie.get('director', movie.get('director', '')),
                'genre_tags': detailed_movie.get('genre_tags', movie.get('genre_tags', [])),
                'plot_summary': detailed_movie.get('plot_summary', movie.get('plot_summary', '')),
                'imdb_id': detailed_movie.get('imdb_id', movie.get('imdb_id')),
                'tmdb_id': tmdb_id,
                'poster_url': detailed_movie.get('poster_url', movie.get('poster_url')),
                'backdrop_url': detailed_movie.get('backdrop_url', movie.get('backdrop_url')),
                'runtime': detailed_movie.get('runtime', movie.get('runtime')),
                'vote_average': detailed_movie.get('vote_average', movie.get('vote_average')),
                'vote_count': detailed_movie.get('vote_count', movie.get('vote_count'))
            })
            
            # Enrich with OMDb if available
            if self.omdb_api_key:
                enriched_movie = enrich_with_omdb(enriched_movie, self.omdb_api_key)
            
            print(f"✅ Enriched metadata for {enriched_movie['title']}")
            return enriched_movie
            
        except Exception as e:
            print(f"❌ Failed to enrich metadata for {movie.get('title', 'Unknown')}: {e}")
            return movie
    
    def add_movie_images(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """Add poster and backdrop images from TMDB"""
        try:
            tmdb_id = movie.get('tmdb_id')
            if not tmdb_id:
                print(f"⚠️  No TMDB ID for {movie.get('title', 'Unknown')}")
                return movie
            
            # Get images from TMDB
            images_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/images"
            response = self.session.get(images_url)
            
            if response.status_code == 200:
                images_data = response.json()
                
                # Get best poster
                posters = images_data.get('posters', [])
                if posters:
                    # Prefer English posters, then highest vote average
                    english_posters = [p for p in posters if p.get('iso_639_1') == 'en']
                    if english_posters:
                        best_poster = max(english_posters, key=lambda x: x.get('vote_average', 0))
                    else:
                        best_poster = max(posters, key=lambda x: x.get('vote_average', 0))
                    
                    movie['poster_url'] = f"https://image.tmdb.org/t/p/w500{best_poster['file_path']}"
                
                # Get best backdrop
                backdrops = images_data.get('backdrops', [])
                if backdrops:
                    # Prefer English backdrops, then highest vote average
                    english_backdrops = [b for b in backdrops if b.get('iso_639_1') == 'en']
                    if english_backdrops:
                        best_backdrop = max(english_backdrops, key=lambda x: x.get('vote_average', 0))
                    else:
                        best_backdrop = max(backdrops, key=lambda x: x.get('vote_average', 0))
                    
                    movie['backdrop_url'] = f"https://image.tmdb.org/t/p/w1280{best_backdrop['file_path']}"
                
                print(f"✅ Added images for {movie['title']}")
            else:
                print(f"⚠️  Failed to get images for {movie.get('title', 'Unknown')}: HTTP {response.status_code}")
            
            return movie
            
        except Exception as e:
            print(f"❌ Failed to add images for {movie.get('title', 'Unknown')}: {e}")
            return movie
    
    def generate_movie_profile(self, movie: Dict[str, Any]) -> Dict[str, Any]:
        """Generate LLM profile for movie"""
        try:
            if not movie.get('plot_summary'):
                print(f"⚠️  No plot summary for {movie.get('title', 'Unknown')}, skipping profile generation")
                return movie
            
            # Generate profile using the existing system
            profile = self.recommender.profile_generator.generate_profile(movie)
            
            # Convert profile to dictionary and merge with movie data
            profile_dict = {
                'primary_emotional_tone': profile.primary_emotional_tone,
                'secondary_emotional_tone': profile.secondary_emotional_tone,
                'primary_theme': profile.primary_theme,
                'secondary_theme': profile.secondary_theme,
                'intensity_level': profile.intensity_level,
                'pacing_style': profile.pacing_style,
                'visual_aesthetic': profile.visual_aesthetic,
                'target_audience': profile.target_audience,
                'similar_films': profile.similar_films,
                'cultural_context': profile.cultural_context,
                'narrative_structure': profile.narrative_structure,
                'energy_level': profile.energy_level,
                'discussion_topics': profile.discussion_topics,
                'card_description': profile.card_description,
                'profile_text': profile.profile_text
            }
            
            # Merge profile with movie data
            enriched_movie = movie.copy()
            enriched_movie.update(profile_dict)
            
            print(f"✅ Generated profile for {enriched_movie['title']}")
            return enriched_movie
            
        except Exception as e:
            print(f"❌ Failed to generate profile for {movie.get('title', 'Unknown')}: {e}")
            return movie
    
    def process_movie(self, movie: Dict[str, Any], steps: List[str] = None) -> Dict[str, Any]:
        """Process a single movie through the enrichment pipeline"""
        if steps is None:
            steps = ['metadata', 'images', 'profile']
        
        print(f"\n🎬 Processing: {movie.get('title', 'Unknown')}")
        
        processed_movie = movie.copy()
        
        if 'metadata' in steps:
            processed_movie = self.enrich_movie_metadata(processed_movie)
        
        if 'images' in steps:
            processed_movie = self.add_movie_images(processed_movie)
        
        if 'profile' in steps:
            processed_movie = self.generate_movie_profile(processed_movie)
        
        return processed_movie
    
    def process_batch(self, movies: List[Dict[str, Any]], steps: List[str] = None) -> List[Dict[str, Any]]:
        """Process a batch of movies through the enrichment pipeline"""
        print(f"\n🚀 Starting batch processing of {len(movies)} movies")
        
        processed_movies = []
        
        for i, movie in enumerate(movies, 1):
            print(f"\n[{i}/{len(movies)}] Processing: {movie.get('title', 'Unknown')}")
            
            try:
                processed_movie = self.process_movie(movie, steps)
                processed_movies.append(processed_movie)
                
                # Add delay to be respectful to APIs
                if i < len(movies):
                    import time
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"❌ Failed to process {movie.get('title', 'Unknown')}: {e}")
                processed_movies.append(movie)  # Keep original if processing fails
        
        print(f"\n✅ Batch processing completed: {len(processed_movies)} movies processed")
        return processed_movies
    
    def merge_to_main_database(self, new_movies: List[Dict[str, Any]], backup: bool = True) -> int:
        """Merge processed movies into the main database"""
        try:
            # Load current database
            db_file = Path("movie_profiles_merged.json")
            if not db_file.exists():
                print("❌ Main database file not found")
                return 0
            
            with open(db_file, 'r') as f:
                current_db = json.load(f)
            
            # Create backup if requested (disabled by default to prevent excessive backups)
            if backup:
                # Ensure backups directory exists
                os.makedirs("backups", exist_ok=True)
                
                backup_file = f"backups/movie_profiles_merged_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_file, 'w') as f:
                    json.dump(current_db, f, indent=2, ensure_ascii=False)
                print(f"💾 Created backup: {backup_file}")
            
            # Merge new movies
            merged_count = 0
            for movie in new_movies:
                title = movie.get('title', '')
                if title:
                    current_db[title] = movie
                    merged_count += 1
            
            # Save updated database
            with open(db_file, 'w') as f:
                json.dump(current_db, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Merged {merged_count} movies into main database")
            return merged_count
            
        except Exception as e:
            print(f"❌ Failed to merge to main database: {e}")
            return 0

def main():
    """Example usage of the enrichment pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Movie Enrichment Pipeline')
    parser.add_argument('--input', required=True, help='Input JSON file with movies to process')
    parser.add_argument('--output', help='Output JSON file (default: input_file_enriched.json)')
    parser.add_argument('--steps', nargs='+', choices=['metadata', 'images', 'profile'], 
                       default=['metadata', 'images', 'profile'], help='Enrichment steps to run')
    parser.add_argument('--merge', action='store_true', help='Merge results to main database')
    parser.add_argument('--provider', default='openai', choices=['openai', 'anthropic', 'ollama'],
                       help='LLM provider for profile generation')
    
    args = parser.parse_args()
    
    # Load input movies
    with open(args.input, 'r') as f:
        if args.input.endswith('.json'):
            data = json.load(f)
            movies = data.get('movies', []) if isinstance(data, dict) else data
        else:
            raise ValueError("Input file must be JSON")
    
    print(f"📁 Loaded {len(movies)} movies from {args.input}")
    
    # Initialize pipeline
    pipeline = EnrichmentPipeline(args.provider)
    
    # Process movies
    processed_movies = pipeline.process_batch(movies, args.steps)
    
    # Save results
    output_file = args.output or args.input.replace('.json', '_enriched.json')
    with open(output_file, 'w') as f:
        json.dump(processed_movies, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved enriched movies to {output_file}")
    
    # Merge to main database if requested
    if args.merge:
        merged_count = pipeline.merge_to_main_database(processed_movies)
        print(f"🔄 Merged {merged_count} movies to main database")

if __name__ == "__main__":
    main()
