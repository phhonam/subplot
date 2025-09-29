#!/usr/bin/env python3
"""
Simple YouTube Trailer Scraper

A simplified version that focuses on reliability and ease of use.
This version uses direct YouTube search URLs and basic HTML parsing.

Usage:
    python simple_trailer_scraper.py --input movie_profiles_merged.json --limit 5
"""

import json
import time
import logging
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SimpleTrailerScraper:
    """Simple YouTube trailer scraper using direct search"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def search_trailer(self, movie_title: str, year: Optional[int] = None) -> Dict[str, Any]:
        """
        Search for a movie trailer on YouTube
        
        Returns:
            Dict with trailer information or error
        """
        result = {
            'movie_title': movie_title,
            'trailer_url': None,
            'video_id': None,
            'title': None,
            'channel': None,
            'duration': None,
            'view_count': None,
            'confidence': 0.0,
            'error': None
        }
        
        try:
            # Build search query
            query_parts = [movie_title]
            if year:
                query_parts.append(str(year))
            query_parts.append("trailer")
            
            query = " ".join(query_parts)
            search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
            
            logging.info(f"Searching: {query}")
            
            # Make request
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for video links in the page
            video_links = []
            
            # Method 1: Look for watch links
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/watch?v=' in href:
                    video_id = href.split('/watch?v=')[1].split('&')[0]
                    title = link.get('title', '').strip()
                    if title and video_id not in [v['video_id'] for v in video_links]:
                        video_links.append({
                            'video_id': video_id,
                            'title': title,
                            'url': f"https://www.youtube.com/watch?v={video_id}"
                        })
            
            # Method 2: Look for video containers (alternative approach)
            if not video_links:
                # Try to find video containers with different selectors
                containers = soup.find_all(['div', 'article'], class_=re.compile(r'video|result|item'))
                for container in containers:
                    link = container.find('a', href=True)
                    if link and '/watch?v=' in link.get('href', ''):
                        href = link.get('href', '')
                        video_id = href.split('/watch?v=')[1].split('&')[0]
                        title = link.get('title', '') or link.get_text().strip()
                        if title and video_id not in [v['video_id'] for v in video_links]:
                            video_links.append({
                                'video_id': video_id,
                                'title': title,
                                'url': f"https://www.youtube.com/watch?v={video_id}"
                            })
            
            # Find best match
            if video_links:
                best_match = self._find_best_match(movie_title, video_links, year)
                if best_match:
                    result.update({
                        'trailer_url': best_match['url'],
                        'video_id': best_match['video_id'],
                        'title': best_match['title'],
                        'confidence': best_match['confidence']
                    })
                    logging.info(f"Found trailer: {best_match['title']}")
                else:
                    result['error'] = "No suitable trailer found"
            else:
                result['error'] = "No videos found on search page"
                
        except Exception as e:
            result['error'] = str(e)
            logging.error(f"Error searching for '{movie_title}': {e}")
        
        return result
    
    def _find_best_match(self, movie_title: str, video_links: List[Dict], year: Optional[int] = None) -> Optional[Dict]:
        """Find the best trailer match from video links"""
        if not video_links:
            return None
        
        # Score each video
        scored_videos = []
        for video in video_links:
            score = self._calculate_score(movie_title, video['title'], year)
            video['confidence'] = score
            scored_videos.append(video)
        
        # Sort by score (highest first)
        scored_videos.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Return the best match if it meets minimum threshold
        if scored_videos and scored_videos[0]['confidence'] > 0.3:
            return scored_videos[0]
        
        return None
    
    def _calculate_score(self, movie_title: str, video_title: str, year: Optional[int] = None) -> float:
        """Calculate confidence score for a video match"""
        score = 0.0
        
        # Normalize titles
        movie_norm = self._normalize_title(movie_title)
        video_norm = self._normalize_title(video_title)
        
        # Check for trailer keywords
        trailer_keywords = ['trailer', 'official trailer', 'teaser', 'preview']
        has_trailer_keyword = any(keyword in video_norm for keyword in trailer_keywords)
        
        if has_trailer_keyword:
            score += 0.4
        
        # Check title similarity
        movie_words = set(movie_norm.split())
        video_words = set(video_norm.split())
        
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
        movie_words -= common_words
        video_words -= common_words
        
        if movie_words and video_words:
            word_overlap = len(movie_words.intersection(video_words))
            word_similarity = word_overlap / max(len(movie_words), len(video_words))
            score += word_similarity * 0.4
        
        # Check for year match
        if year:
            year_str = str(year)
            if year_str in video_title:
                score += 0.2
        
        # Penalize certain keywords
        negative_keywords = ['review', 'reaction', 'analysis', 'breakdown', 'explained', 'ending', 'spoiler']
        if any(keyword in video_norm for keyword in negative_keywords):
            score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        normalized = re.sub(r'[^\w\s]', ' ', title.lower())
        normalized = ' '.join(normalized.split())
        return normalized

def extract_year_from_title(title: str) -> Optional[int]:
    """Extract year from movie title if present"""
    # Look for year in parentheses at the end
    year_match = re.search(r'\((\d{4})\)$', title)
    if year_match:
        return int(year_match.group(1))
    
    # Look for year in the title
    year_match = re.search(r'\b(19|20)\d{2}\b', title)
    if year_match:
        return int(year_match.group(0))
    
    return None

def main():
    parser = argparse.ArgumentParser(description='Simple YouTube trailer scraper')
    parser.add_argument('--input', '-i', default='movie_profiles_merged.json', 
                       help='Input movie data file')
    parser.add_argument('--output', '-o', default='movies_with_trailers_simple.json',
                       help='Output file for movies with trailers')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of movies to process')
    parser.add_argument('--start', type=int, default=0, help='Start from this movie index')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests (seconds)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed')
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found.")
        return
    
    # Load movie data
    print(f"Loading movie data from {args.input}")
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            movie_data = json.load(f)
    except Exception as e:
        print(f"Error loading movie data: {e}")
        return
    
    print(f"Loaded {len(movie_data)} movies")
    
    # Initialize scraper
    scraper = SimpleTrailerScraper()
    
    # Get movies to process
    movies = list(movie_data.items())
    if args.limit:
        movies = movies[args.start:args.start + args.limit]
    else:
        movies = movies[args.start:]
    
    print(f"Processing {len(movies)} movies")
    
    if args.dry_run:
        print("\nDRY RUN - Movies that would be processed:")
        for i, (title, data) in enumerate(movies):
            year = extract_year_from_title(title)
            print(f"{i+1:3d}. {title} ({year})")
        return
    
    # Process movies
    processed = 0
    found = 0
    
    for i, (title, data) in enumerate(movies):
        print(f"\n[{i+1}/{len(movies)}] Processing: {title}")
        
        # Extract year
        year = extract_year_from_title(title)
        if year:
            print(f"  Year: {year}")
        
        # Search for trailer
        result = scraper.search_trailer(title, year)
        
        # Add results to movie data
        if result['trailer_url']:
            data['trailer_url'] = result['trailer_url']
            data['trailer_video_id'] = result['video_id']
            data['trailer_title'] = result['title']
            data['trailer_confidence'] = result['confidence']
            data['trailer_found_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"  ✓ Found trailer: {result['trailer_url']}")
            print(f"    Title: {result['title']}")
            print(f"    Confidence: {result['confidence']:.2f}")
            found += 1
        else:
            data['trailer_error'] = result['error']
            data['trailer_searched_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"  ✗ No trailer found: {result['error']}")
        
        processed += 1
        
        # Save progress every 5 movies
        if processed % 5 == 0:
            print(f"\nSaving progress... ({processed} processed, {found} found)")
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(movie_data, f, indent=2, ensure_ascii=False)
        
        # Rate limiting
        if args.delay > 0:
            time.sleep(args.delay)
    
    # Final save
    print(f"\nSaving final results to {args.output}")
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(movie_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nCompleted!")
    print(f"Processed: {processed} movies")
    print(f"Found trailers: {found} movies")
    print(f"Success rate: {found/processed*100:.1f}%" if processed > 0 else "0%")
    print(f"Results saved to: {args.output}")

if __name__ == "__main__":
    main()
