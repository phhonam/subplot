# Archive Folder

This folder contains files that were moved from the main project directory for better organization. These files are no longer needed for the core functionality of the movie recommender application.

## Folder Structure

### `test_scripts/`
Contains test scripts and debug files that were used during development:
- `test_backdrops.py` - Test script for backdrop images
- `test_data.html` - Test HTML file
- `test_frontend_data.py` - Test script for frontend data
- `test_maborosi_rendering.py` - Test script for specific movie rendering
- `test_poster_fetching.py` - Test script for poster fetching
- `debug_koreeda_loading.py` - Debug script for Koreeda movies
- `debug_missing_movies.py` - Debug script for missing movies
- `demo_poster_integration.py` - Demo script for poster integration
- `example_youtube_usage.py` - Example usage script

### `fix_scripts/`
Contains one-time fix scripts that were used to resolve specific issues:
- `fix_display.py` - One-time fix for display issues
- `fix_images.py` - One-time fix for images
- `fix_issues.py` - One-time fix for issues
- `fix_koreeda_loading.py` - One-time fix for Koreeda loading
- `fix_maborosi_data.py` - One-time fix for specific movie data
- `fix_sources.py` - One-time fix for sources
- `fix_title_matching.py` - One-time fix for title matching
- `final_fix.py` - Final one-time fix

### `logs/`
Contains log files from various processes:
- `collection.log` - Collection process log
- `deduplication.log` - Deduplication process log
- `director_collection.log` - Director collection log
- `director_integration.log` - Director integration log
- `director_profiles.log` - Director profiles log
- `youtube_scraper.log` - YouTube scraper log

### `intermediate_data/`
Contains outdated and intermediate JSON files that were replaced by final versions:
- `mock_movie_data.json` - Mock data for testing
- `scraped_movie_data.json` - Intermediate scraped data
- `movie_profiles_scraped.json` - Intermediate scraped profiles
- `movie_profiles_afi100_2007.json` - Specific collection subset
- `movie_profiles_top_rated_us.json` - Specific collection subset
- `movie_profiles_updated.json` - Intermediate update file
- `movie_profiles_with_images.json` - Intermediate file with images
- `movie_profiles_with_trailers.json` - Intermediate file with trailers
- `merged_movie_data.json` - Intermediate merged data
- `merged_movie_data_updated.json` - Intermediate updated data
- `merged_movie_data_with_images.json` - Intermediate data with images
- `merged_movie_data_with_posters.json` - Intermediate data with posters
- `merged_movie_data_report.json` - Report file
- `movies_with_trailers_simple.json` - Intermediate trailers data
- `koreeda_profiles.json` - Specific director subset
- `koreeda.json` - Specific director data
- `villeneuve_profiles.json` - Specific director subset
- `villeneuve_movies.json` - Specific director data
- `director_movie_profiles.json` - Director-specific profiles

### `processing_scripts/`
Contains one-time processing scripts that were used to build the final dataset:
- `collect_more_data.py` - Data collection script
- `convert_enhanced_data.py` - Data conversion script
- `deduplicate_collections.py` - Deduplication script
- `deduplicate_collections_fixed.py` - Fixed deduplication script
- `director_data_integrator.py` - Director data integration
- `director_movie_collector.py` - Director movie collection
- `director_profile_generator.py` - Director profile generation
- `enhance_movies_with_images.py` - Image enhancement script
- `enhance_movies_with_posters.py` - Poster enhancement script
- `enrich_profiles_with_movie_data.py` - Profile enrichment script
- `generate_movie_profiles.py` - Profile generation script
- `manual_trailer_adder.py` - Manual trailer addition
- `merge_koreeda_final.py` - Final Koreeda merge
- `merge_profiles_with_images.py` - Profile-image merge
- `run_trailer_scraper.py` - Trailer scraper runner
- `simple_trailer_scraper.py` - Simple trailer scraper
- `trailer_url_finder.py` - Trailer URL finder
- `update_app.py` - App update script
- `youtube_trailer_scraper.py` - YouTube trailer scraper

### `backups/`
Contains backup files:
- `movie_profiles_merged_backup.json` - Backup of merged profiles

## Current Essential Files

The following files remain in the main directory as they are essential for the application:

### Core Application Files:
- `main.py` - Main application logic
- `api.py` - API server
- `app.js` - Frontend JavaScript
- `index.html` - Main HTML file
- `styles.css` - CSS styles
- `user_taste_profile.py` - User taste profiling
- `interactive_recommender.py` - Interactive recommender
- `update_api.py` - API update script

### Essential Data Files:
- `movie_profiles_merged.json` - Main merged movie profiles (1,243 movies)
- `merged_movie_data_final.json` - Final merged movie data (1,243 movies)
- `movie_profiles_complete.json` - Complete movie profiles
- `user_ratings.json` - User ratings data

### Collection Data (Reference):
- `afi100_2007.json`
- `bfi_greatest.json`
- `diverse_2000s.json`
- `french_films.json`
- `international_cinema.json`
- `japanese_films.json`
- `korean_films.json`
- `recent_acclaimed_2020s.json`
- `spanish_films.json`
- `top_rated_global_1000.json`
- `top_rated_us_500.json`
- `top_rated_us.json`

### Documentation:
- `POSTER_INTEGRATION_GUIDE.md`
- `TRAILER_SCRAPER_SUMMARY.md`
- `YOUTUBE_TRAILER_SCRAPER_README.md`
- `requirements_youtube.txt`

## Summary

**Total files moved**: 60+ files
**Main directory cleanup**: Complete
**Project organization**: Significantly improved

The project is now much cleaner and more organized, with only essential files remaining in the main directory.
