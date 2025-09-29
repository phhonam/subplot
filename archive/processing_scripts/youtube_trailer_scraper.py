#!/usr/bin/env python3
"""
YouTube Trailer Scraper for Movie Recommender

This script searches for YouTube trailer links for movies in your collection.
It supports both YouTube Data API (recommended) and web scraping fallback methods.

Requirements:
- For API method: pip install google-api-python-client
- For web scraping: pip install requests beautifulsoup4
- For rate limiting: pip install ratelimit

Usage:
    python youtube_trailer_scraper.py --input movie_profiles_merged.json --output movies_with_trailers.json
    python youtube_trailer_scraper.py --input movie_profiles_merged.json --method api --api-key YOUR_YOUTUBE_API_KEY
"""

import json
import time
import logging
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import quote_plus, urlparse, parse_qs
import requests
from dataclasses import dataclass
from datetime import datetime

# Optional imports for enhanced functionality
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False
    print("YouTube Data API not available. Install with: pip install google-api-python-client")

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    print("BeautifulSoup not available. Install with: pip install beautifulsoup4")

try:
    from ratelimit import limits, sleep_and_retry
    RATELIMIT_AVAILABLE = True
except ImportError:
    RATELIMIT_AVAILABLE = False
    print("Rate limiting not available. Install with: pip install ratelimit")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_scraper.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class TrailerResult:
    """Container for trailer search results"""
    movie_title: str
    trailer_url: Optional[str] = None
    video_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[str] = None
    view_count: Optional[int] = None
    published_date: Optional[str] = None
    channel: Optional[str] = None
    confidence_score: float = 0.0
    search_method: str = "unknown"
    error: Optional[str] = None

class YouTubeTrailerScraper:
    """Main scraper class for finding YouTube movie trailers"""
    
    def __init__(self, api_key: Optional[str] = None, method: str = "api"):
        self.api_key = api_key
        self.method = method.lower()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # YouTube API service
        self.youtube_service = None
        if self.method == "api" and api_key and YOUTUBE_API_AVAILABLE:
            try:
                self.youtube_service = build('youtube', 'v3', developerKey=api_key)
                logging.info("YouTube Data API initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize YouTube API: {e}")
                self.method = "scrape"  # Fallback to scraping
        
        # Rate limiting decorators
        if RATELIMIT_AVAILABLE:
            self.api_search = sleep_and_retry(limits(calls=100, period=100)(self._api_search))
            self.scrape_search = sleep_and_retry(limits(calls=10, period=60)(self._scrape_search))
        else:
            self.api_search = self._api_search
            self.scrape_search = self._scrape_search
    
    def search_trailer(self, movie_title: str, year: Optional[int] = None) -> TrailerResult:
        """
        Search for a movie trailer on YouTube
        
        Args:
            movie_title: The title of the movie
            year: Optional release year for better search accuracy
            
        Returns:
            TrailerResult object with search results
        """
        result = TrailerResult(movie_title=movie_title)
        
        try:
            if self.method == "api" and self.youtube_service:
                result = self.api_search(movie_title, year)
            else:
                result = self.scrape_search(movie_title, year)
                
        except Exception as e:
            result.error = str(e)
            logging.error(f"Error searching for trailer '{movie_title}': {e}")
        
        return result
    
    def _api_search(self, movie_title: str, year: Optional[int] = None) -> TrailerResult:
        """Search using YouTube Data API"""
        result = TrailerResult(movie_title=movie_title, search_method="api")
        
        # Build search query
        query = self._build_search_query(movie_title, year, include_trailer=True)
        
        try:
            # Search for videos
            search_response = self.youtube_service.search().list(
                q=query,
                part='id,snippet',
                type='video',
                maxResults=10,
                order='relevance',
                videoDuration='short',  # Prefer shorter videos (trailers)
                videoDefinition='high'  # Prefer HD videos
            ).execute()
            
            # Get video details
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            if not video_ids:
                result.error = "No videos found"
                return result
            
            # Get detailed video information
            videos_response = self.youtube_service.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids)
            ).execute()
            
            # Find best trailer match
            best_match = self._find_best_trailer_match(
                movie_title, 
                videos_response.get('items', []),
                year
            )
            
            if best_match:
                result.trailer_url = f"https://www.youtube.com/watch?v={best_match['id']}"
                result.video_id = best_match['id']
                result.title = best_match['snippet']['title']
                result.description = best_match['snippet']['description']
                result.published_date = best_match['snippet']['publishedAt']
                result.channel = best_match['snippet']['channelTitle']
                result.duration = best_match['contentDetails']['duration']
                result.view_count = int(best_match['statistics'].get('viewCount', 0))
                result.confidence_score = self._calculate_confidence_score(
                    movie_title, best_match['snippet']['title'], year
                )
            else:
                result.error = "No suitable trailer found"
                
        except HttpError as e:
            result.error = f"YouTube API error: {e}"
            logging.error(f"YouTube API error for '{movie_title}': {e}")
        except Exception as e:
            result.error = f"API search error: {e}"
            logging.error(f"API search error for '{movie_title}': {e}")
        
        return result
    
    def _scrape_search(self, movie_title: str, year: Optional[int] = None) -> TrailerResult:
        """Search using web scraping (fallback method)"""
        result = TrailerResult(movie_title=movie_title, search_method="scrape")
        
        if not BEAUTIFULSOUP_AVAILABLE:
            result.error = "BeautifulSoup not available for web scraping"
            return result
        
        try:
            # Build search URL
            query = self._build_search_query(movie_title, year, include_trailer=True)
            search_url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
            
            # Make request
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract video data from page
            video_data = self._extract_video_data_from_page(soup)
            
            if not video_data:
                result.error = "No videos found on search page"
                return result
            
            # Find best trailer match
            best_match = self._find_best_trailer_match_scraped(
                movie_title, video_data, year
            )
            
            if best_match:
                result.trailer_url = best_match['url']
                result.video_id = best_match['video_id']
                result.title = best_match['title']
                result.description = best_match.get('description', '')
                result.duration = best_match.get('duration', '')
                result.view_count = best_match.get('view_count', 0)
                result.channel = best_match.get('channel', '')
                result.confidence_score = self._calculate_confidence_score(
                    movie_title, best_match['title'], year
                )
            else:
                result.error = "No suitable trailer found"
                
        except Exception as e:
            result.error = f"Scraping error: {e}"
            logging.error(f"Scraping error for '{movie_title}': {e}")
        
        return result
    
    def _build_search_query(self, movie_title: str, year: Optional[int] = None, include_trailer: bool = True) -> str:
        """Build optimized search query for YouTube"""
        query_parts = [movie_title]
        
        if year:
            query_parts.append(str(year))
        
        if include_trailer:
            query_parts.append("trailer")
        
        return " ".join(query_parts)
    
    def _find_best_trailer_match(self, movie_title: str, videos: List[Dict], year: Optional[int] = None) -> Optional[Dict]:
        """Find the best trailer match from API results"""
        if not videos:
            return None
        
        # Score each video
        scored_videos = []
        for video in videos:
            score = self._calculate_confidence_score(
                movie_title, 
                video['snippet']['title'], 
                year
            )
            scored_videos.append((score, video))
        
        # Sort by score (highest first)
        scored_videos.sort(key=lambda x: x[0], reverse=True)
        
        # Return the best match if it meets minimum threshold
        if scored_videos and scored_videos[0][0] > 0.3:
            return scored_videos[0][1]
        
        return None
    
    def _find_best_trailer_match_scraped(self, movie_title: str, videos: List[Dict], year: Optional[int] = None) -> Optional[Dict]:
        """Find the best trailer match from scraped results"""
        return self._find_best_trailer_match(movie_title, videos, year)
    
    def _calculate_confidence_score(self, movie_title: str, video_title: str, year: Optional[int] = None) -> float:
        """Calculate confidence score for a video match"""
        score = 0.0
        
        # Normalize titles for comparison
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
        
        # Penalize certain keywords that suggest it's not a trailer
        negative_keywords = ['review', 'reaction', 'analysis', 'breakdown', 'explained', 'ending', 'spoiler']
        if any(keyword in video_norm for keyword in negative_keywords):
            score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        # Remove special characters and convert to lowercase
        normalized = re.sub(r'[^\w\s]', ' ', title.lower())
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        return normalized
    
    def _extract_video_data_from_page(self, soup) -> List[Dict]:
        """Extract video data from YouTube search page HTML"""
        videos = []
        
        # This is a simplified extraction - YouTube's HTML structure changes frequently
        # In practice, you might need to use more sophisticated parsing or browser automation
        
        # Look for video containers (this selector may need updates)
        video_containers = soup.find_all('div', {'class': 'ytd-video-renderer'})
        
        for container in video_containers[:10]:  # Limit to first 10 results
            try:
                # Extract video ID from link
                link_elem = container.find('a', {'id': 'video-title'})
                if not link_elem:
                    continue
                
                href = link_elem.get('href', '')
                if '/watch?v=' in href:
                    video_id = href.split('/watch?v=')[1].split('&')[0]
                else:
                    continue
                
                # Extract title
                title = link_elem.get('title', '').strip()
                
                # Extract channel
                channel_elem = container.find('a', {'class': 'yt-simple-endpoint'})
                channel = channel_elem.get_text().strip() if channel_elem else ''
                
                # Extract duration (if available)
                duration_elem = container.find('span', {'class': 'style-scope ytd-thumbnail-overlay-time-status-renderer'})
                duration = duration_elem.get_text().strip() if duration_elem else ''
                
                # Extract view count (if available)
                view_elem = container.find('span', {'class': 'style-scope ytd-video-meta-block'})
                view_count = 0
                if view_elem:
                    view_text = view_elem.get_text()
                    # Parse view count (e.g., "1.2M views")
                    view_match = re.search(r'([\d,\.]+[KMB]?)\s*views?', view_text)
                    if view_match:
                        view_str = view_match.group(1)
                        view_count = self._parse_view_count(view_str)
                
                videos.append({
                    'video_id': video_id,
                    'title': title,
                    'channel': channel,
                    'duration': duration,
                    'view_count': view_count,
                    'url': f"https://www.youtube.com/watch?v={video_id}"
                })
                
            except Exception as e:
                logging.debug(f"Error extracting video data: {e}")
                continue
        
        return videos
    
    def _parse_view_count(self, view_str: str) -> int:
        """Parse view count string to integer"""
        try:
            view_str = view_str.replace(',', '')
            if 'K' in view_str:
                return int(float(view_str.replace('K', '')) * 1000)
            elif 'M' in view_str:
                return int(float(view_str.replace('M', '')) * 1000000)
            elif 'B' in view_str:
                return int(float(view_str.replace('B', '')) * 1000000000)
            else:
                return int(view_str)
        except:
            return 0

def load_movie_data(file_path: str) -> Dict[str, Any]:
    """Load movie data from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading movie data from {file_path}: {e}")
        return {}

def save_movie_data(data: Dict[str, Any], file_path: str):
    """Save movie data to JSON file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved movie data to {file_path}")
    except Exception as e:
        logging.error(f"Error saving movie data to {file_path}: {e}")

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
    parser = argparse.ArgumentParser(description='Scrape YouTube trailer links for movies')
    parser.add_argument('--input', '-i', required=True, help='Input JSON file with movie data')
    parser.add_argument('--output', '-o', help='Output JSON file (default: input_with_trailers.json)')
    parser.add_argument('--method', '-m', choices=['api', 'scrape'], default='api', 
                       help='Search method: api (YouTube Data API) or scrape (web scraping)')
    parser.add_argument('--api-key', help='YouTube Data API key (required for api method)')
    parser.add_argument('--limit', '-l', type=int, help='Limit number of movies to process')
    parser.add_argument('--start-index', type=int, default=0, help='Start processing from this index')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests in seconds')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without making requests')
    
    args = parser.parse_args()
    
    # Set output file
    if not args.output:
        input_path = Path(args.input)
        args.output = str(input_path.parent / f"{input_path.stem}_with_trailers.json")
    
    # Load movie data
    logging.info(f"Loading movie data from {args.input}")
    movie_data = load_movie_data(args.input)
    
    if not movie_data:
        logging.error("No movie data loaded. Exiting.")
        return
    
    # Initialize scraper
    scraper = YouTubeTrailerScraper(api_key=args.api_key, method=args.method)
    
    # Process movies
    movies = list(movie_data.items())
    if args.limit:
        movies = movies[args.start_index:args.start_index + args.limit]
    else:
        movies = movies[args.start_index:]
    
    logging.info(f"Processing {len(movies)} movies")
    
    if args.dry_run:
        logging.info("DRY RUN - No actual requests will be made")
        for i, (title, data) in enumerate(movies):
            year = extract_year_from_title(title)
            logging.info(f"{i+1}. {title} ({year})")
        return
    
    # Process each movie
    processed_count = 0
    success_count = 0
    
    for i, (title, data) in enumerate(movies):
        try:
            logging.info(f"Processing {i+1}/{len(movies)}: {title}")
            
            # Extract year if available
            year = extract_year_from_title(title)
            
            # Search for trailer
            result = scraper.search_trailer(title, year)
            
            # Add trailer data to movie
            if result.trailer_url:
                data['trailer_url'] = result.trailer_url
                data['trailer_video_id'] = result.video_id
                data['trailer_title'] = result.title
                data['trailer_channel'] = result.channel
                data['trailer_duration'] = result.duration
                data['trailer_view_count'] = result.view_count
                data['trailer_confidence'] = result.confidence_score
                data['trailer_search_method'] = result.search_method
                data['trailer_found_at'] = datetime.now().isoformat()
                success_count += 1
                logging.info(f"✓ Found trailer: {result.trailer_url}")
            else:
                data['trailer_error'] = result.error
                data['trailer_search_method'] = result.search_method
                data['trailer_searched_at'] = datetime.now().isoformat()
                logging.warning(f"✗ No trailer found: {result.error}")
            
            processed_count += 1
            
            # Save progress periodically
            if processed_count % 10 == 0:
                save_movie_data(movie_data, args.output)
                logging.info(f"Progress saved: {processed_count} processed, {success_count} successful")
            
            # Rate limiting
            if args.delay > 0:
                time.sleep(args.delay)
                
        except KeyboardInterrupt:
            logging.info("Interrupted by user")
            break
        except Exception as e:
            logging.error(f"Error processing {title}: {e}")
            continue
    
    # Final save
    save_movie_data(movie_data, args.output)
    
    logging.info(f"Completed! Processed {processed_count} movies, found {success_count} trailers")
    logging.info(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
