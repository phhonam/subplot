"""
Admin API endpoints for movie database management
"""

import json
import os
import shutil
import glob
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import asyncio

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
import requests

from admin_auth import (
    authenticate_admin, create_access_token, get_current_admin,
    LoginRequest, LoginResponse, AuthStatus, check_auth_status
)

from fetch_movies import (
    get_movie_details_and_credits, hydrate_from_tmdb_list, hydrate_from_csv, 
    hydrate_from_wikipedia, hydrate_from_bfi, hydrate_from_letterboxd,
    tmdb_search_movie, session_with_api_key
)
from main import MovieRecommender
from merge_image_data import merge_image_data

def reload_api_data():
    """Helper function to reload API data with multiple fallback methods"""
    try:
        import time
        
        # Add a small delay to ensure the file write is complete
        time.sleep(1)
        
        # Try direct reload first (more reliable than HTTP request)
        try:
            from api import reload_movie_data
            success = reload_movie_data()
            if success:
                log_admin_operation("api_reload", "Successfully reloaded API data directly", "success")
                return True
            else:
                log_admin_operation("api_reload", "Direct reload failed, trying HTTP request", "warning")
                raise Exception("Direct reload failed")
        except Exception as direct_error:
            # Fallback to HTTP request
            import requests
            response = requests.post("http://127.0.0.1:8003/reload", timeout=30)
            if response.status_code == 200:
                result = response.json()
                log_admin_operation("api_reload", f"Successfully reloaded API data via HTTP: {result.get('count', 'unknown')} movies", "success")
                return True
            else:
                log_admin_operation("api_reload", f"Failed to reload API data: HTTP {response.status_code} - {response.text}", "warning")
                return False
                
    except requests.exceptions.ConnectionError as e:
        log_admin_operation("api_reload", f"Failed to connect to API for reload: {e}", "warning")
        return False
    except requests.exceptions.Timeout as e:
        log_admin_operation("api_reload", f"API reload request timed out: {e}", "warning")
        return False
    except Exception as e:
        log_admin_operation("api_reload", f"Failed to reload API data: {e}", "warning")
        return False

def restart_static_server():
    """Helper function to restart the static file server to clear caches"""
    try:
        import subprocess
        import signal
        
        # Find and kill existing static server processes
        try:
            result = subprocess.run(['pgrep', '-f', 'python.*http.server.*8000'], capture_output=True, text=True)
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid.strip():
                        try:
                            os.kill(int(pid.strip()), signal.SIGTERM)
                            log_admin_operation("static_server_restart", f"Killed existing static server PID {pid.strip()}", "info")
                        except ProcessLookupError:
                            pass  # Process already dead
                        except Exception as e:
                            log_admin_operation("static_server_restart", f"Failed to kill PID {pid.strip()}: {e}", "warning")
        except Exception as e:
            log_admin_operation("static_server_restart", f"Failed to find existing servers: {e}", "warning")
        
        # Wait a moment for processes to terminate
        time.sleep(2)
        
        # Start new static server
        try:
            subprocess.Popen(['python3', '-m', 'http.server', '8000', '--directory', '.'], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)  # Give it a moment to start
            
            # Test if server is responding
            test_response = requests.get("http://localhost:8000/", timeout=5)
            if test_response.status_code == 200:
                log_admin_operation("static_server_restart", "Successfully restarted static server", "success")
                return True
            else:
                log_admin_operation("static_server_restart", f"Static server restarted but not responding properly: {test_response.status_code}", "warning")
                return False
                
        except Exception as e:
            log_admin_operation("static_server_restart", f"Failed to start new static server: {e}", "error")
            return False
            
    except Exception as e:
        log_admin_operation("static_server_restart", f"Failed to restart static server: {e}", "error")
        return False

def full_sync_data():
    """Complete synchronization: reload API data and restart static server"""
    try:
        log_admin_operation("full_sync", "Starting full data synchronization", "info")
        
        # Step 1: Reload API data
        api_success = reload_api_data()
        
        # Step 2: Restart static server
        server_success = restart_static_server()
        
        if api_success and server_success:
            log_admin_operation("full_sync", "Full synchronization completed successfully", "success")
            return True
        else:
            log_admin_operation("full_sync", f"Partial synchronization: API={api_success}, Server={server_success}", "warning")
            return False
            
    except Exception as e:
        log_admin_operation("full_sync", f"Full synchronization failed: {e}", "error")
        return False

# TMDB API helper functions for director scraping
def tmdb_search_person(sess: requests.Session, person_name: str) -> Optional[int]:
    """Search for a person by name and return their TMDB person ID"""
    try:
        params = {
            "query": person_name,
            "include_adult": "false"
        }
        
        response = sess.get("https://api.themoviedb.org/3/search/person", params=params)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        if not results:
            return None
            
        # Find best match (exact name match preferred)
        person_name_lower = person_name.lower()
        for person in results:
            name = person.get("name", "").lower()
            if name == person_name_lower:
                return person["id"]
                
        # If no exact match, take the first result
        return results[0]["id"]
        
    except Exception as e:
        print(f"Error searching for person {person_name}: {e}")
        return None

def get_person_movies(sess: requests.Session, person_id: int) -> List[Dict[str, Any]]:
    """Get all movies directed by a person"""
    try:
        response = sess.get(f"https://api.themoviedb.org/3/person/{person_id}/movie_credits")
        response.raise_for_status()
        data = response.json()
        
        crew_credits = data.get("crew", [])
        
        # Filter for directing credits only
        directed_movies = []
        for credit in crew_credits:
            if credit.get("job") == "Director":
                directed_movies.append(credit)
                
        return directed_movies
        
    except Exception as e:
        print(f"Error fetching movies for person {person_id}: {e}")
        return []

def get_movie_director(sess: requests.Session, tmdb_id: int) -> Optional[str]:
    """Get the actual director of a specific movie"""
    try:
        response = sess.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits")
        response.raise_for_status()
        data = response.json()
        
        crew = data.get("crew", [])
        for person in crew:
            if person.get("job") == "Director":
                return person.get("name", "")
                
        return None
        
    except Exception as e:
        print(f"Error fetching director for movie {tmdb_id}: {e}")
        return None

# Initialize router
admin_router = APIRouter(prefix="/admin", tags=["admin"])

# Data models
class MovieVisibilityRequest(BaseModel):
    titles: List[str]

class DirectorScrapeRequest(BaseModel):
    director: str
    includeShorts: bool = True
    includeTV: bool = True
    includeDocumentaries: bool = True

class TMDBListRequest(BaseModel):
    list_id: str
    description: Optional[str] = None

class CustomCollectionRequest(BaseModel):
    source: str  # 'csv', 'wikipedia', 'letterboxd'
    data: str    # file content or URL

class MoviePreviewRequest(BaseModel):
    title: str
    tmdb_id: Optional[str] = None

# Global state for admin operations
admin_state = {
    'pipeline': [],
    'staging': [],
    'hidden_movies': set(),
    'operation_logs': []
}

def log_admin_operation(operation: str, details: str, level: str = "info"):
    """Log admin operations"""
    timestamp = datetime.now().isoformat()
    log_entry = {
        'timestamp': timestamp,
        'operation': operation,
        'details': details,
        'level': level
    }
    admin_state['operation_logs'].append(log_entry)
    
    # Keep only last 1000 logs
    if len(admin_state['operation_logs']) > 1000:
        admin_state['operation_logs'] = admin_state['operation_logs'][-1000:]

def load_hidden_movies():
    """Load list of hidden movies from file"""
    hidden_file = Path("hidden_movies.json")
    if hidden_file.exists():
        try:
            with open(hidden_file, 'r') as f:
                data = json.load(f)
                admin_state['hidden_movies'] = set(data.get('hidden', []))
        except Exception as e:
            log_admin_operation("load_hidden", f"Failed to load hidden movies: {e}", "error")

def save_hidden_movies():
    """Save list of hidden movies to file"""
    hidden_file = Path("hidden_movies.json")
    try:
        with open(hidden_file, 'w') as f:
            json.dump({'hidden': list(admin_state['hidden_movies'])}, f, indent=2)
        log_admin_operation("save_hidden", f"Saved {len(admin_state['hidden_movies'])} hidden movies")
    except Exception as e:
        log_admin_operation("save_hidden", f"Failed to save hidden movies: {e}", "error")

def get_movie_data() -> Dict[str, Any]:
    """Load current movie data"""
    try:
        with open("movie_profiles_merged.json", 'r') as f:
            return json.load(f)
    except Exception as e:
        log_admin_operation("load_movies", f"Failed to load movie data: {e}", "error")
        return {}

def cleanup_old_backups(keep_count: int = 5):
    """Clean up old backup files, keeping only the most recent ones"""
    try:
        # Ensure backups directory exists
        os.makedirs("backups", exist_ok=True)
        
        backup_files = glob.glob("backups/movie_profiles_merged_backup_*.json")
        if len(backup_files) > keep_count:
            # Sort by modification time (newest first)
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            # Remove old backups
            for old_backup in backup_files[keep_count:]:
                os.remove(old_backup)
                log_admin_operation("cleanup", f"Removed old backup: {old_backup}")
                
            log_admin_operation("cleanup", f"Cleaned up {len(backup_files) - keep_count} old backup files")
    except Exception as e:
        log_admin_operation("cleanup", f"Failed to cleanup old backups: {e}", "error")

def save_movie_data(data: Dict[str, Any], create_backup: bool = False):
    """Save movie data with optional backup"""
    try:
        # Create backup only if requested
        if create_backup:
            # Ensure backups directory exists
            os.makedirs("backups", exist_ok=True)
            
            backup_file = f"backups/movie_profiles_merged_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy("movie_profiles_merged.json", backup_file)
            log_admin_operation("save_movies", f"Saved {len(data)} movies with backup {backup_file}")
            
            # Clean up old backups after creating a new one
            cleanup_old_backups()
        else:
            log_admin_operation("save_movies", f"Saved {len(data)} movies")
        
        # Save new data
        with open("movie_profiles_merged.json", 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
    except Exception as e:
        log_admin_operation("save_movies", f"Failed to save movie data: {e}", "error")
        raise HTTPException(status_code=500, detail=f"Failed to save movie data: {e}")

@admin_router.post("/auth/login")
async def admin_login(request: LoginRequest):
    """Admin login endpoint"""
    try:
        if authenticate_admin(request.username, request.password):
            access_token = create_access_token(request.username)
            log_admin_operation("login", f"Admin {request.username} logged in successfully")
            return LoginResponse(access_token=access_token)
        else:
            log_admin_operation("login", f"Failed login attempt for {request.username}", "error")
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        log_admin_operation("login", f"Login error: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/auth/status")
async def get_auth_status(token: Optional[str] = None):
    """Get authentication status"""
    return check_auth_status(token)

@admin_router.get("/dashboard")
async def get_dashboard_stats(current_admin: dict = Depends(get_current_admin)):
    """Get dashboard statistics"""
    try:
        movies = get_movie_data()
        load_hidden_movies()
        
        total_movies = len(movies)
        hidden_movies = len(admin_state['hidden_movies'])
        visible_movies = total_movies - hidden_movies
        
        # Calculate completeness metrics
        complete_profiles = 0
        with_images = 0
        metadata_complete = 0
        
        for title, movie in movies.items():
            if title in admin_state['hidden_movies']:
                continue
                
            # Check profile completeness
            if (movie.get('profile_text') and 
                movie.get('primary_emotional_tone') and 
                movie.get('primary_theme')):
                complete_profiles += 1
            
            # Check image availability
            if movie.get('poster_url') or movie.get('backdrop_url'):
                with_images += 1
            
            # Check metadata completeness
            if (movie.get('director') and 
                movie.get('year') and 
                movie.get('genre_tags')):
                metadata_complete += 1
        
        return {
            'totalMovies': total_movies,
            'visibleMovies': visible_movies,
            'hiddenMovies': hidden_movies,
            'completeProfiles': complete_profiles,
            'withImages': with_images,
            'metadataComplete': metadata_complete,
            'lastUpdated': datetime.now().isoformat()
        }
        
    except Exception as e:
        log_admin_operation("dashboard", f"Failed to get dashboard stats: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/movies")
async def get_movies(current_admin: dict = Depends(get_current_admin)):
    """Get all movies with admin metadata"""
    try:
        movies = get_movie_data()
        load_hidden_movies()
        
        print(f"get_movies: Loaded {len(movies)} movies, {len(admin_state['hidden_movies'])} hidden")
        
        movie_list = []
        hidden_count = 0
        for title, movie in movies.items():
            movie_data = movie.copy()
            is_hidden = title in admin_state['hidden_movies']
            movie_data['hidden'] = is_hidden
            movie_data['title'] = title  # Ensure title is set
            movie_list.append(movie_data)
            if is_hidden:
                hidden_count += 1
        
        print(f"get_movies: Returning {len(movie_list)} movies, {hidden_count} marked as hidden")
        return {'movies': movie_list}
        
    except Exception as e:
        log_admin_operation("get_movies", f"Failed to get movies: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/movies/hide")
async def hide_movies(request: MovieVisibilityRequest, current_admin: dict = Depends(get_current_admin)):
    """Hide selected movies"""
    try:
        # Debug logging
        print(f"Hide request received: {request.titles}")
        print(f"Admin state before load: {len(admin_state['hidden_movies'])} hidden movies")
        
        load_hidden_movies()
        print(f"Admin state after load: {len(admin_state['hidden_movies'])} hidden movies")
        
        for title in request.titles:
            print(f"Adding '{title}' to hidden movies")
            admin_state['hidden_movies'].add(title)
        
        print(f"Admin state after adding: {len(admin_state['hidden_movies'])} hidden movies")
        
        save_hidden_movies()
        log_admin_operation("hide_movies", f"Hidden {len(request.titles)} movies: {request.titles}")
        
        return {'message': f'Successfully hid {len(request.titles)} movies', 'hidden_count': len(admin_state['hidden_movies'])}
        
    except Exception as e:
        log_admin_operation("hide_movies", f"Failed to hide movies: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/movies/show")
async def show_movies(request: MovieVisibilityRequest, current_admin: dict = Depends(get_current_admin)):
    """Show selected movies"""
    try:
        # Debug logging
        print(f"Show request received: {request.titles}")
        print(f"Admin state before load: {len(admin_state['hidden_movies'])} hidden movies")
        
        load_hidden_movies()
        print(f"Admin state after load: {len(admin_state['hidden_movies'])} hidden movies")
        
        for title in request.titles:
            print(f"Removing '{title}' from hidden movies")
            admin_state['hidden_movies'].discard(title)
        
        print(f"Admin state after removing: {len(admin_state['hidden_movies'])} hidden movies")
        
        save_hidden_movies()
        log_admin_operation("show_movies", f"Showed {len(request.titles)} movies: {request.titles}")
        
        return {'message': f'Successfully showed {len(request.titles)} movies', 'hidden_count': len(admin_state['hidden_movies'])}
        
    except Exception as e:
        log_admin_operation("show_movies", f"Failed to show movies: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/movies/preview")
async def preview_movie(request: MoviePreviewRequest, current_admin: dict = Depends(get_current_admin)):
    """Get detailed movie information for preview"""
    try:
        movies = get_movie_data()
        
        # First, try to find the movie in our existing database
        movie = movies.get(request.title)
        
        if movie:
            # Movie exists in our database, return it
            log_admin_operation("preview_movie", f"Found existing movie: {request.title}")
            return movie
        
        # If not found and we have a TMDB ID, try to get fresh data from TMDB
        if request.tmdb_id:
            try:
                tmdb_api_key = os.environ.get("TMDB_API_KEY")
                if tmdb_api_key:
                    sess = requests.Session()
                    sess.params = {'api_key': tmdb_api_key}
                    
                    # Get detailed movie information from TMDB
                    response = sess.get(f"https://api.themoviedb.org/3/movie/{request.tmdb_id}")
                    if response.status_code == 200:
                        tmdb_data = response.json()
                        
                        # Get movie credits for director information
                        credits_response = sess.get(f"https://api.themoviedb.org/3/movie/{request.tmdb_id}/credits")
                        director = "Unknown"
                        if credits_response.status_code == 200:
                            credits_data = credits_response.json()
                            crew = credits_data.get('crew', [])
                            for person in crew:
                                if person.get('job') == 'Director':
                                    director = person.get('name', 'Unknown')
                                    break
                        
                        # Format the movie data for preview
                        movie_data = {
                            'title': tmdb_data.get('title', request.title),
                            'year': tmdb_data.get('release_date', '')[:4] if tmdb_data.get('release_date') else '',
                            'director': director,
                            'tmdb_id': request.tmdb_id,
                            'overview': tmdb_data.get('overview', ''),
                            'plot_summary': tmdb_data.get('overview', ''),
                            'runtime': tmdb_data.get('runtime'),
                            'vote_average': tmdb_data.get('vote_average'),
                            'vote_count': tmdb_data.get('vote_count'),
                            'poster_path': tmdb_data.get('poster_path'),
                            'backdrop_path': tmdb_data.get('backdrop_path'),
                            'genre_ids': tmdb_data.get('genre_ids', []),
                            'adult': tmdb_data.get('adult', False),
                            'original_language': tmdb_data.get('original_language'),
                            'original_title': tmdb_data.get('original_title'),
                            'popularity': tmdb_data.get('popularity'),
                            'production_companies': tmdb_data.get('production_companies', []),
                            'production_countries': tmdb_data.get('production_countries', []),
                            'spoken_languages': tmdb_data.get('spoken_languages', [])
                        }
                        
                        # Add poster URL if available
                        if movie_data.get('poster_path'):
                            movie_data['poster_url'] = f"https://image.tmdb.org/t/p/w500{movie_data['poster_path']}"
                        
                        # Add backdrop URL if available
                        if movie_data.get('backdrop_path'):
                            movie_data['backdrop_url'] = f"https://image.tmdb.org/t/p/w1280{movie_data['backdrop_path']}"
                        
                        log_admin_operation("preview_movie", f"Retrieved fresh TMDB data for: {request.title}")
                        return movie_data
                        
            except Exception as tmdb_error:
                log_admin_operation("preview_movie", f"Failed to get TMDB data for {request.title}: {tmdb_error}", "warning")
        
        # If we can't find the movie anywhere, return basic info
        log_admin_operation("preview_movie", f"Movie not found: {request.title}", "warning")
        return {
            'title': request.title,
            'year': '',
            'director': 'Unknown',
            'tmdb_id': request.tmdb_id or '',
            'overview': 'No information available',
            'plot_summary': 'No information available',
            'runtime': None,
            'vote_average': None,
            'vote_count': None,
            'poster_url': None,
            'backdrop_url': None,
            'genre_ids': [],
            'error': 'Movie not found in database or TMDB'
        }
        
    except Exception as e:
        log_admin_operation("preview_movie", f"Failed to preview movie {request.title}: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/scrape/director")
async def scrape_director_movies(request: DirectorScrapeRequest, current_admin: dict = Depends(get_current_admin)):
    """Scrape movies by director from TMDB"""
    try:
        tmdb_api_key = os.environ.get("TMDB_API_KEY")
        if not tmdb_api_key:
            raise HTTPException(status_code=500, detail="TMDB_API_KEY not configured")
        
        sess = requests.Session()
        sess.params = {'api_key': tmdb_api_key}
        
        # Search for director
        person_id = tmdb_search_person(sess, request.director)
        if not person_id:
            raise HTTPException(status_code=404, detail=f"Director '{request.director}' not found")
        
        # Get director's movies
        movies = get_person_movies(sess, person_id)
        print(f"Found {len(movies)} movies in filmography for {request.director}")
        
        # Filter based on options and deduplicate
        filtered_movies = []
        seen_movies = set()  # Track seen movies by (title, year) tuple
        
        for movie in movies:
            # Get movie details to determine if it's a short, TV movie, or documentary
            title = movie.get('title', '').strip()
            year = movie.get('release_date', '')[:4] if movie.get('release_date') else ''
            
            # Skip movies with empty titles
            if not title:
                continue
            
            # Apply filtering based on user preferences
            # Note: TMDB credits don't always include detailed genre/media_type info
            # So we'll use heuristics and be more permissive
            
            # Check if this might be a short film (runtime < 60 minutes)
            runtime = movie.get('runtime', 0)
            if runtime > 0 and not request.includeShorts and runtime < 60:
                continue
            
            # Check if this might be a TV movie or documentary based on title patterns
            title_lower = title.lower()
            
            # Skip TV movies if not included
            if not request.includeTV:
                tv_indicators = ['tv movie', 'made for tv', 'television movie', 'tv special']
                if any(indicator in title_lower for indicator in tv_indicators):
                    continue
            
            # Skip documentaries if not included
            if not request.includeDocumentaries:
                doc_indicators = ['documentary', 'doc', 'making of', 'behind the scenes', 'tribute', 'biography']
                if any(indicator in title_lower for indicator in doc_indicators):
                    continue
            
            # Create a normalized key for deduplication (case-insensitive, trimmed)
            movie_key = (title.lower().strip(), year)
            
            # Skip if we've already seen this movie
            if movie_key in seen_movies:
                continue
            
            seen_movies.add(movie_key)
            
            # Get actual director information for this movie (for verification)
            actual_director = get_movie_director(sess, movie.get('id'))
            
            # Since we're getting movies from the person's filmography where job="Director",
            # we should trust TMDB's data more. Only skip if we get a completely different director.
            should_include = True
            verification_note = ""
            
            if actual_director:
                # Try exact match first
                if actual_director.lower() == request.director.lower():
                    verification_note = f"✅ Exact match: {actual_director}"
                else:
                    # Try flexible matching for name variations
                    searched_name_parts = request.director.lower().replace(' ', '').replace('.', '').replace('-', '')
                    actual_name_parts = actual_director.lower().replace(' ', '').replace('.', '').replace('-', '')
                    
                    if searched_name_parts == actual_name_parts:
                        verification_note = f"✅ Name variation match: {actual_director}"
                    elif (searched_name_parts in actual_name_parts or 
                          actual_name_parts in searched_name_parts):
                        verification_note = f"✅ Partial name match: {actual_director}"
                    else:
                        # Only exclude if the director names are completely different
                        # and the actual director is clearly not the searched person
                        if len(actual_director.split()) > 1 and len(request.director.split()) > 1:
                            # Both have multiple names, check if any part matches
                            searched_parts = set(request.director.lower().split())
                            actual_parts = set(actual_director.lower().split())
                            if not searched_parts.intersection(actual_parts):
                                should_include = False
                                verification_note = f"❌ Completely different director: {actual_director}"
                            else:
                                verification_note = f"⚠️  Name overlap, including: {actual_director}"
                        else:
                            # Single names or unclear cases - be more permissive
                            verification_note = f"⚠️  Different director but including: {actual_director}"
            else:
                verification_note = "⚠️  No director info, including based on filmography"
            
            if should_include:
                # Add basic movie info
                movie_info = {
                    'title': title,
                    'year': year,
                    'tmdb_id': movie.get('id'),
                    'director': actual_director or request.director,  # Use actual if available, fallback to searched
                    'overview': movie.get('overview', ''),
                    'poster_path': movie.get('poster_path'),
                    'backdrop_path': movie.get('backdrop_path'),
                    'genre_ids': movie.get('genre_ids', []),
                    'vote_average': movie.get('vote_average'),
                    'vote_count': movie.get('vote_count')
                }
                filtered_movies.append(movie_info)
                print(f"Including {title} - {verification_note}")
            else:
                print(f"Skipping {title} - {verification_note}")
                continue
        
        # Sort by year (newest first) and then by title
        filtered_movies.sort(key=lambda x: (x['year'] or '0', x['title']), reverse=True)
        
        log_admin_operation("scrape_director", f"Scraped {len(filtered_movies)} unique movies for {request.director} (shorts: {request.includeShorts}, TV: {request.includeTV}, docs: {request.includeDocumentaries})")
        
        return {'movies': filtered_movies}
        
    except Exception as e:
        log_admin_operation("scrape_director", f"Failed to scrape director: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/scrape/tmdb-list")
async def scrape_tmdb_list(request: TMDBListRequest, current_admin: dict = Depends(get_current_admin)):
    """Scrape movies from TMDB list"""
    try:
        tmdb_api_key = os.environ.get("TMDB_API_KEY")
        omdb_api_key = os.environ.get("OMDB_API_KEY")
        
        if not tmdb_api_key:
            raise HTTPException(status_code=500, detail="TMDB_API_KEY not configured")
        
        sess = requests.Session()
        sess.params = {'api_key': tmdb_api_key}
        
        # Hydrate from TMDB list
        movies = hydrate_from_tmdb_list(sess, request.list_id, omdb_api_key)
        
        log_admin_operation("scrape_tmdb_list", f"Scraped {len(movies)} movies from list {request.list_id}")
        
        return {'movies': movies}
        
    except Exception as e:
        log_admin_operation("scrape_tmdb_list", f"Failed to scrape TMDB list: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/scrape/custom")
async def scrape_custom_collection(request: CustomCollectionRequest, current_admin: dict = Depends(get_current_admin)):
    """Scrape movies from custom source"""
    try:
        tmdb_api_key = os.environ.get("TMDB_API_KEY")
        omdb_api_key = os.environ.get("OMDB_API_KEY")
        
        if not tmdb_api_key:
            raise HTTPException(status_code=500, detail="TMDB_API_KEY not configured")
        
        sess = requests.Session()
        sess.params = {'api_key': tmdb_api_key}
        
        movies = []
        
        if request.source == 'wikipedia':
            movies = hydrate_from_wikipedia(sess, request.data, omdb_api_key)
        elif request.source == 'letterboxd':
            movies = hydrate_from_letterboxd(sess, request.data, omdb_api_key)
        elif request.source == 'bfi':
            movies = hydrate_from_bfi(sess, request.data, omdb_api_key)
        elif request.source == 'csv':
            # Save CSV data to temp file
            temp_csv = Path("temp_collection.csv")
            with open(temp_csv, 'w') as f:
                f.write(request.data)
            movies = hydrate_from_csv(sess, str(temp_csv), omdb_api_key)
            temp_csv.unlink()  # Clean up
        
        log_admin_operation("scrape_custom", f"Scraped {len(movies)} movies from {request.source}")
        
        return {'movies': movies}
        
    except Exception as e:
        log_admin_operation("scrape_custom", f"Failed to scrape custom collection: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/enrichment/start")
async def start_enrichment_pipeline(background_tasks: BackgroundTasks, current_admin: dict = Depends(get_current_admin)):
    """Start enrichment pipeline for movies in staging"""
    try:
        if not admin_state['staging']:
            raise HTTPException(status_code=400, detail="No movies in staging area")
        
        background_tasks.add_task(run_enrichment_pipeline)
        
        log_admin_operation("enrichment_start", f"Started enrichment pipeline for {len(admin_state['staging'])} movies")
        
        return {'message': 'Enrichment pipeline started'}
        
    except Exception as e:
        log_admin_operation("enrichment_start", f"Failed to start enrichment: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/enrichment/metadata")
async def start_metadata_enrichment(background_tasks: BackgroundTasks, current_admin: dict = Depends(get_current_admin)):
    """Start metadata enrichment for movies in staging"""
    try:
        if not admin_state['staging']:
            raise HTTPException(status_code=400, detail="No movies in staging area")
        
        background_tasks.add_task(run_metadata_enrichment_pipeline)
        
        log_admin_operation("metadata_enrichment", f"Started metadata enrichment for {len(admin_state['staging'])} movies")
        
        return {'message': 'Metadata enrichment started'}
        
    except Exception as e:
        log_admin_operation("metadata_enrichment", f"Failed to start metadata enrichment: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/enrichment/images")
async def start_image_enrichment(background_tasks: BackgroundTasks, current_admin: dict = Depends(get_current_admin)):
    """Start image enrichment for movies in staging"""
    try:
        if not admin_state['staging']:
            raise HTTPException(status_code=400, detail="No movies in staging area")
        
        background_tasks.add_task(run_image_enrichment_pipeline)
        
        log_admin_operation("image_enrichment", f"Started image enrichment for {len(admin_state['staging'])} movies")
        
        return {'message': 'Image enrichment started'}
        
    except Exception as e:
        log_admin_operation("image_enrichment", f"Failed to start image enrichment: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/enrichment/profiles")
async def start_profile_enrichment(background_tasks: BackgroundTasks, current_admin: dict = Depends(get_current_admin)):
    """Start profile generation for movies in staging"""
    try:
        if not admin_state['staging']:
            raise HTTPException(status_code=400, detail="No movies in staging area")
        
        background_tasks.add_task(run_profile_enrichment_pipeline)
        
        log_admin_operation("profile_enrichment", f"Started profile generation for {len(admin_state['staging'])} movies")
        
        return {'message': 'Profile generation started'}
        
    except Exception as e:
        log_admin_operation("profile_enrichment", f"Failed to start profile generation: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/enrichment/generate-profiles")
async def generate_profiles_for_movies(background_tasks: BackgroundTasks, current_admin: dict = Depends(get_current_admin)):
    """Generate profiles for movies that don't have them yet"""
    try:
        movies = get_movie_data()
        movies_needing_profiles = []
        
        # Find movies without profiles
        for title, movie in movies.items():
            if not movie.get('profile_text') or not movie.get('primary_emotional_tone'):
                movies_needing_profiles.append(movie)
        
        if not movies_needing_profiles:
            return {'message': 'No movies need profile generation', 'count': 0}
        
        # Add to staging and start profile generation
        admin_state['staging'] = movies_needing_profiles
        background_tasks.add_task(run_profile_generation_pipeline)
        
        log_admin_operation("profile_generation", f"Started profile generation for {len(movies_needing_profiles)} movies")
        
        return {'message': f'Profile generation started for {len(movies_needing_profiles)} movies', 'count': len(movies_needing_profiles)}
        
    except Exception as e:
        log_admin_operation("profile_generation", f"Failed to start profile generation: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

async def run_profile_generation_pipeline():
    """Run profile generation for movies without profiles"""
    try:
        log_admin_operation("profile_generation", "Starting profile generation pipeline", "info")
        
        # Move movies from staging to pipeline
        admin_state['pipeline'] = admin_state['staging'].copy()
        admin_state['staging'] = []
        
        # Import and initialize the enrichment pipeline
        from enrichment_pipeline import EnrichmentPipeline
        pipeline = EnrichmentPipeline("openai")
        
        # Process each movie through profile generation only
        for i, movie in enumerate(admin_state['pipeline']):
            try:
                log_admin_operation("profile_generation", f"Generating profile for {movie['title']} ({i+1}/{len(admin_state['pipeline'])})", "info")
                
                # Run only profile generation
                enriched_movie = pipeline.process_movie(movie, steps=['profile'])
                
                # Update movie in database
                movies = get_movie_data()
                movies[movie['title']] = enriched_movie
                save_movie_data(movies)
                
                log_admin_operation("profile_generation", f"Successfully generated profile for {movie['title']}", "success")
                
            except Exception as e:
                log_admin_operation("profile_generation", f"Failed to generate profile for {movie['title']}: {e}", "error")
        
        admin_state['pipeline'] = []
        log_admin_operation("profile_generation", "Profile generation pipeline completed", "success")
        
    except Exception as e:
        log_admin_operation("profile_generation", f"Profile generation pipeline failed: {e}", "error")

async def run_enrichment_pipeline():
    """Run the enrichment pipeline in background with optimized file I/O"""
    try:
        log_admin_operation("enrichment_pipeline", "Starting enrichment pipeline", "info")
        
        # Move movies from staging to pipeline
        admin_state['pipeline'] = admin_state['staging'].copy()
        admin_state['staging'] = []
        
        # Import and initialize the proper enrichment pipeline
        from enrichment_pipeline import EnrichmentPipeline
        
        # Initialize pipeline with OpenAI (you can make this configurable)
        pipeline = EnrichmentPipeline("openai")
        
        # OPTIMIZATION: Load the database ONCE at the start
        log_admin_operation("enrichment_pipeline", "Loading movie database for batch processing", "info")
        movies = get_movie_data()
        
        # Process each movie through the full enrichment pipeline
        for i, movie in enumerate(admin_state['pipeline']):
            try:
                log_admin_operation("enrichment_pipeline", f"Processing {movie['title']} ({i+1}/{len(admin_state['pipeline'])})", "info")
                
                # Run full enrichment: metadata + images + profile generation
                enriched_movie = pipeline.process_movie(movie, steps=['metadata', 'images', 'profile'])
                
                # Add enriched movie to in-memory database (no file I/O yet)
                movies[movie['title']] = enriched_movie
                
                log_admin_operation("enrichment_pipeline", f"Successfully processed {movie['title']}", "success")
                
            except Exception as e:
                log_admin_operation("enrichment_pipeline", f"Failed to process {movie['title']}: {e}", "error")
                # Still add the original movie to database even if enrichment fails
                movies[movie['title']] = movie
        
        admin_state['pipeline'] = []
        
        # OPTIMIZATION: Save the entire database ONCE at the end
        log_admin_operation("enrichment_pipeline", "Saving enriched movies to database", "info")
        save_movie_data(movies, create_backup=True)
        
        log_admin_operation("enrichment_pipeline", "Enrichment pipeline completed", "success")
        
        # Full sync to include new movies (API reload + server restart)
        full_sync_data()
        
    except Exception as e:
        log_admin_operation("enrichment_pipeline", f"Enrichment pipeline failed: {e}", "error")

async def run_metadata_enrichment_pipeline():
    """Run metadata enrichment for movies in staging with optimized file I/O"""
    try:
        log_admin_operation("metadata_enrichment", "Starting metadata enrichment pipeline", "info")
        
        # Move movies from staging to pipeline
        admin_state['pipeline'] = admin_state['staging'].copy()
        admin_state['staging'] = []
        
        # Import and initialize the enrichment pipeline
        from enrichment_pipeline import EnrichmentPipeline
        pipeline = EnrichmentPipeline("openai")
        
        # OPTIMIZATION: Load the database ONCE at the start
        log_admin_operation("metadata_enrichment", "Loading movie database for batch processing", "info")
        movies = get_movie_data()
        
        # Process each movie through metadata enrichment only
        for i, movie in enumerate(admin_state['pipeline']):
            try:
                log_admin_operation("metadata_enrichment", f"Enriching metadata for {movie['title']} ({i+1}/{len(admin_state['pipeline'])})", "info")
                
                # Run only metadata enrichment
                enriched_movie = pipeline.process_movie(movie, steps=['metadata'])
                
                # Update movie in in-memory database (no file I/O yet)
                movies[movie['title']] = enriched_movie
                
                log_admin_operation("metadata_enrichment", f"Successfully enriched metadata for {movie['title']}", "success")
                
            except Exception as e:
                log_admin_operation("metadata_enrichment", f"Failed to enrich metadata for {movie['title']}: {e}", "error")
        
        admin_state['pipeline'] = []
        
        # OPTIMIZATION: Save the entire database ONCE at the end
        log_admin_operation("metadata_enrichment", "Saving enriched movies to database", "info")
        save_movie_data(movies, create_backup=True)
        
        log_admin_operation("metadata_enrichment", "Metadata enrichment pipeline completed", "success")
        
        # Full sync to include new movies (API reload + server restart)
        full_sync_data()
        
    except Exception as e:
        log_admin_operation("metadata_enrichment", f"Metadata enrichment pipeline failed: {e}", "error")

async def run_image_enrichment_pipeline():
    """Run image enrichment for movies in staging with optimized file I/O"""
    try:
        log_admin_operation("image_enrichment", "Starting image enrichment pipeline", "info")
        
        # Move movies from staging to pipeline
        admin_state['pipeline'] = admin_state['staging'].copy()
        admin_state['staging'] = []
        
        # Import and initialize the enrichment pipeline
        from enrichment_pipeline import EnrichmentPipeline
        pipeline = EnrichmentPipeline("openai")
        
        # OPTIMIZATION: Load the database ONCE at the start
        log_admin_operation("image_enrichment", "Loading movie database for batch processing", "info")
        movies = get_movie_data()
        
        # Process each movie through image enrichment only
        for i, movie in enumerate(admin_state['pipeline']):
            try:
                log_admin_operation("image_enrichment", f"Adding images for {movie['title']} ({i+1}/{len(admin_state['pipeline'])})", "info")
                
                # Run only image enrichment
                enriched_movie = pipeline.process_movie(movie, steps=['images'])
                
                # Update movie in in-memory database (no file I/O yet)
                movies[movie['title']] = enriched_movie
                
                log_admin_operation("image_enrichment", f"Successfully added images for {movie['title']}", "success")
                
            except Exception as e:
                log_admin_operation("image_enrichment", f"Failed to add images for {movie['title']}: {e}", "error")
        
        admin_state['pipeline'] = []
        
        # OPTIMIZATION: Save the entire database ONCE at the end
        log_admin_operation("image_enrichment", "Saving enriched movies to database", "info")
        save_movie_data(movies, create_backup=True)
        
        log_admin_operation("image_enrichment", "Image enrichment pipeline completed", "success")
        
        # Full sync to include new movies (API reload + server restart)
        full_sync_data()
        
    except Exception as e:
        log_admin_operation("image_enrichment", f"Image enrichment pipeline failed: {e}", "error")

async def run_profile_enrichment_pipeline():
    """Run profile generation for movies in staging"""
    try:
        log_admin_operation("profile_enrichment", "Starting profile generation pipeline", "info")
        
        # Move movies from staging to pipeline
        admin_state['pipeline'] = admin_state['staging'].copy()
        admin_state['staging'] = []
        
        # Import and initialize the enrichment pipeline
        from enrichment_pipeline import EnrichmentPipeline
        pipeline = EnrichmentPipeline("openai")
        
        # Process each movie through profile generation only
        for i, movie in enumerate(admin_state['pipeline']):
            try:
                log_admin_operation("profile_enrichment", f"Generating profile for {movie['title']} ({i+1}/{len(admin_state['pipeline'])})", "info")
                
                # Run only profile generation
                enriched_movie = pipeline.process_movie(movie, steps=['profile'])
                
                # Update movie in database
                movies = get_movie_data()
                movies[movie['title']] = enriched_movie
                save_movie_data(movies)
                
                log_admin_operation("profile_enrichment", f"Successfully generated profile for {movie['title']}", "success")
                
            except Exception as e:
                log_admin_operation("profile_enrichment", f"Failed to generate profile for {movie['title']}: {e}", "error")
        
        admin_state['pipeline'] = []
        log_admin_operation("profile_enrichment", "Profile generation pipeline completed", "success")
        
        # Full sync to include new movies (API reload + server restart)
        full_sync_data()
        
    except Exception as e:
        log_admin_operation("profile_enrichment", f"Profile generation pipeline failed: {e}", "error")

@admin_router.get("/pipeline")
async def get_pipeline_status(current_admin: dict = Depends(get_current_admin)):
    """Get current pipeline status"""
    return {
        'pipeline': admin_state['pipeline'],
        'staging': admin_state['staging'],
        'pipelineCount': len(admin_state['pipeline']),
        'stagingCount': len(admin_state['staging'])
    }

@admin_router.post("/pipeline/add")
async def add_to_pipeline(movies: List[Dict[str, Any]], current_admin: dict = Depends(get_current_admin)):
    """Add movies to staging area"""
    try:
        admin_state['staging'].extend(movies)
        
        log_admin_operation("pipeline_add", f"Added {len(movies)} movies to staging")
        
        return {'message': f'Added {len(movies)} movies to staging area'}
        
    except Exception as e:
        log_admin_operation("pipeline_add", f"Failed to add to pipeline: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.get("/logs")
async def get_admin_logs(current_admin: dict = Depends(get_current_admin)):
    """Get admin operation logs"""
    return {'logs': admin_state['operation_logs']}

@admin_router.post("/backup")
async def create_backup(current_admin: dict = Depends(get_current_admin)):
    """Create backup of current database"""
    try:
        # Ensure backups directory exists
        os.makedirs("backups", exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"backups/movie_profiles_merged_backup_{timestamp}.json"
        
        shutil.copy("movie_profiles_merged.json", backup_file)
        
        # Clean up old backups after creating a new one
        cleanup_old_backups()
        
        log_admin_operation("backup", f"Created backup: {backup_file}")
        
        return {'message': f'Backup created: {backup_file}'}
        
    except Exception as e:
        log_admin_operation("backup", f"Failed to create backup: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/cleanup-backups")
async def cleanup_backups(current_admin: dict = Depends(get_current_admin)):
    """Clean up old backup files"""
    try:
        cleanup_old_backups()
        return {'message': 'Old backup files cleaned up successfully'}
        
    except Exception as e:
        log_admin_operation("cleanup", f"Failed to cleanup backups: {e}", "error")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup backups: {e}")

@admin_router.get("/health")
async def health_check(current_admin: dict = Depends(get_current_admin)):
    """Health check endpoint"""
    try:
        # Check if main data file exists and is readable
        movies = get_movie_data()
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'movieCount': len(movies),
            'hiddenCount': len(admin_state['hidden_movies']),
            'pipelineCount': len(admin_state['pipeline']),
            'stagingCount': len(admin_state['staging'])
        }
        
    except Exception as e:
        log_admin_operation("health_check", f"Health check failed: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/sync/reload-api")
async def manual_reload_api(current_admin: dict = Depends(get_current_admin)):
    """Manually reload API data"""
    try:
        success = reload_api_data()
        if success:
            return {'message': 'API data reloaded successfully', 'success': True}
        else:
            return {'message': 'API reload failed - check logs for details', 'success': False}
    except Exception as e:
        log_admin_operation("manual_reload_api", f"Manual API reload failed: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/sync/restart-server")
async def manual_restart_server(current_admin: dict = Depends(get_current_admin)):
    """Manually restart static server"""
    try:
        success = restart_static_server()
        if success:
            return {'message': 'Static server restarted successfully', 'success': True}
        else:
            return {'message': 'Server restart failed - check logs for details', 'success': False}
    except Exception as e:
        log_admin_operation("manual_restart_server", f"Manual server restart failed: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/sync/full")
async def manual_full_sync(current_admin: dict = Depends(get_current_admin)):
    """Manually perform full synchronization (API reload + server restart)"""
    try:
        success = full_sync_data()
        if success:
            return {'message': 'Full synchronization completed successfully', 'success': True}
        else:
            return {'message': 'Full synchronization failed - check logs for details', 'success': False}
    except Exception as e:
        log_admin_operation("manual_full_sync", f"Manual full sync failed: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

@admin_router.post("/director/add-complete")
async def add_director_complete(request: DirectorScrapeRequest, background_tasks: BackgroundTasks, current_admin: dict = Depends(get_current_admin)):
    """One-click director addition: scrape, enrich, and sync automatically"""
    try:
        tmdb_api_key = os.environ.get("TMDB_API_KEY")
        if not tmdb_api_key:
            raise HTTPException(status_code=500, detail="TMDB_API_KEY not configured")
        
        log_admin_operation("director_add_complete", f"Starting complete director addition for {request.director_name}", "info")
        
        # Step 1: Scrape director movies (reuse existing logic)
        with session_with_api_key(tmdb_api_key) as sess:
            person_id = tmdb_search_person(sess, request.director_name)
            if not person_id:
                raise HTTPException(status_code=404, detail=f"Director '{request.director_name}' not found in TMDB")
            
            # Get director movies
            movies = get_person_movies(sess, person_id)
            if not movies:
                raise HTTPException(status_code=404, detail=f"No movies found for director '{request.director_name}'")
            
            # Filter and process movies
            filtered_movies = []
            for movie in movies:
                if movie.get('job') == 'Director':  # Only include movies where they were the director
                    movie_data = get_movie_details_and_credits(sess, movie['id'])
                    if movie_data:
                        filtered_movies.append(movie_data)
            
            if not filtered_movies:
                raise HTTPException(status_code=404, detail=f"No directed movies found for '{request.director_name}'")
        
        log_admin_operation("director_add_complete", f"Scraped {len(filtered_movies)} movies for {request.director_name}", "info")
        
        # Step 2: Add to staging and start enrichment
        admin_state['staging'].extend(filtered_movies)
        log_admin_operation("director_add_complete", f"Added {len(filtered_movies)} movies to staging", "info")
        
        # Step 3: Start enrichment pipeline in background
        background_tasks.add_task(run_complete_enrichment_pipeline)
        
        return {
            'message': f'Successfully initiated complete director addition for {request.director_name}',
            'movies_scraped': len(filtered_movies),
            'director_name': request.director_name,
            'status': 'enrichment_started'
        }
        
    except Exception as e:
        log_admin_operation("director_add_complete", f"Complete director addition failed: {e}", "error")
        raise HTTPException(status_code=500, detail=str(e))

async def run_complete_enrichment_pipeline():
    """Complete enrichment pipeline with automatic sync"""
    try:
        log_admin_operation("complete_enrichment", "Starting complete enrichment pipeline with auto-sync", "info")
        
        if not admin_state['staging']:
            log_admin_operation("complete_enrichment", "No movies in staging area", "warning")
            return
        
        # Move movies from staging to pipeline
        admin_state['pipeline'].extend(admin_state['staging'])
        movies_to_process = admin_state['staging'].copy()
        admin_state['staging'].clear()
        
        log_admin_operation("complete_enrichment", f"Processing {len(movies_to_process)} movies through complete pipeline", "info")
        
        # Process movies through all enrichment steps
        from enrichment_pipeline import EnrichmentPipeline
        pipeline = EnrichmentPipeline()
        
        enriched_movies = []
        for i, movie in enumerate(movies_to_process):
            try:
                log_admin_operation("complete_enrichment", f"Processing movie {i+1}/{len(movies_to_process)}: {movie.get('title', 'Unknown')}", "info")
                
                # Process through all enrichment steps
                enriched_movie = pipeline.process_movie(movie, steps=['metadata', 'images', 'profile'])
                enriched_movies.append(enriched_movie)
                
                # Update progress
                admin_state['pipeline'] = [m for m in admin_state['pipeline'] if m.get('tmdb_id') != movie.get('tmdb_id')]
                
            except Exception as e:
                log_admin_operation("complete_enrichment", f"Failed to process movie {movie.get('title', 'Unknown')}: {e}", "error")
                continue
        
        # Save enriched movies to database
        if enriched_movies:
            movies = get_movie_data()
            for movie in enriched_movies:
                if movie.get('title'):
                    movies[movie['title']] = movie
            
            save_movie_data(movies, create_backup=True)
            log_admin_operation("complete_enrichment", f"Saved {len(enriched_movies)} enriched movies to database", "info")
            
            # Clear pipeline
            admin_state['pipeline'].clear()
            
            # Automatic full sync
            log_admin_operation("complete_enrichment", "Starting automatic synchronization", "info")
            sync_success = full_sync_data()
            
            if sync_success:
                log_admin_operation("complete_enrichment", "Complete enrichment pipeline finished successfully with auto-sync", "success")
            else:
                log_admin_operation("complete_enrichment", "Enrichment completed but sync failed - manual sync required", "warning")
        else:
            log_admin_operation("complete_enrichment", "No movies were successfully enriched", "error")
        
    except Exception as e:
        log_admin_operation("complete_enrichment", f"Complete enrichment pipeline failed: {e}", "error")

# Helper functions for director scraping
def tmdb_search_person(sess: requests.Session, name: str) -> Optional[int]:
    """Search for a person by name in TMDB"""
    try:
        response = sess.get(f"https://api.themoviedb.org/3/search/person", params={
            'query': name,
            'include_adult': False
        })
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            if results:
                return results[0]['id']
        return None
    except Exception:
        return None

def get_person_movies(sess: requests.Session, person_id: int) -> List[Dict[str, Any]]:
    """Get movies for a person from TMDB"""
    try:
        response = sess.get(f"https://api.themoviedb.org/3/person/{person_id}/movie_credits")
        if response.status_code == 200:
            data = response.json()
            return data.get('cast', []) + data.get('crew', [])
        return []
    except Exception:
        return []

# Initialize hidden movies on startup
load_hidden_movies()

