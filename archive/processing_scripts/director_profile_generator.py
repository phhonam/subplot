#!/usr/bin/env python3
"""
Generate movie profiles for director-collected movies.
This script processes the output from director_movie_collector.py
and generates detailed movie profiles using the existing LLM pipeline.
"""

import json
import os
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

# Import the existing movie recommender system
from main import MovieRecommender

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('director_profiles.log'),
        logging.StreamHandler()
    ]
)

class DirectorProfileGenerator:
    def __init__(self, llm_provider: str = "openai"):
        self.recommender = MovieRecommender(llm_provider=llm_provider)
        self.generated_profiles = []
        
    def load_director_movies(self, input_file: str) -> List[Dict[str, Any]]:
        """Load movies collected by director collector"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                movies = data.get('movies', [])
                logging.info(f"Loaded {len(movies)} movies from {input_file}")
                return movies
        except Exception as e:
            logging.error(f"Failed to load {input_file}: {e}")
            return []
            
    def generate_profiles(self, movies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate profiles for the director's movies"""
        if not movies:
            logging.warning("No movies to process")
            return []
            
        logging.info(f"Generating profiles for {len(movies)} movies...")
        
        # Load movies into the recommender system
        self.recommender.movies = movies
        
        # Generate profiles one by one
        profiles = []
        for i, movie in enumerate(movies, 1):
            title = movie.get('title', 'Unknown')
            year = movie.get('year', '')
            logging.info(f"\n[{i}/{len(movies)}] Generating profile for: {title} ({year})")
            
            try:
                profile = self.recommender.profile_generator.generate_profile(movie)
                if profile:
                    # Convert dataclass to dict for JSON serialization
                    profile_dict = {
                        'title': profile.title,
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
                    profiles.append(profile_dict)
                    logging.info(f"  ✓ Profile generated successfully")
                else:
                    logging.warning(f"  ⚠️  Failed to generate profile")
            except Exception as e:
                logging.error(f"  ✗ Error generating profile: {e}")
                
        logging.info(f"\n✓ Generated {len(profiles)} profiles out of {len(movies)} movies")
        return profiles
        
    def save_profiles(self, profiles: List[Dict[str, Any]], output_file: str):
        """Save generated profiles to JSON file"""
        if not profiles:
            logging.warning("No profiles to save")
            return
            
        data = {
            "profiles": profiles,
            "metadata": {
                "total_profiles": len(profiles),
                "source": "director_collection_profiles"
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logging.info(f"✓ Saved {len(profiles)} profiles to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Generate movie profiles for director-collected movies")
    parser.add_argument("--input", "-i", required=True, 
                       help="Input JSON file from director_movie_collector.py")
    parser.add_argument("--output", "-o", default="director_movie_profiles.json",
                       help="Output JSON file for profiles (default: director_movie_profiles.json)")
    parser.add_argument("--provider", choices=["openai", "anthropic", "ollama"], 
                       default="openai", help="LLM provider to use")
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        logging.error(f"Input file not found: {args.input}")
        return
        
    # Initialize generator
    generator = DirectorProfileGenerator(llm_provider=args.provider)
    
    # Load movies
    movies = generator.load_director_movies(args.input)
    if not movies:
        return
        
    # Generate profiles
    profiles = generator.generate_profiles(movies)
    
    # Save profiles
    generator.save_profiles(profiles, args.output)
    
    logging.info(f"\n{'='*60}")
    logging.info("PROFILE GENERATION COMPLETE")
    logging.info(f"{'='*60}")
    logging.info(f"Generated {len(profiles)} profiles from {len(movies)} movies")
    logging.info(f"Profiles saved to: {args.output}")

if __name__ == "__main__":
    main()
