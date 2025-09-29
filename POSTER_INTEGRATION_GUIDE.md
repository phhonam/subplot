# Movie Poster Integration Guide

This guide explains how to add movie posters to your movie recommender system using TMDB's API.

## Overview

Your movie profiles now support poster URLs through the `poster_url` field. This enhancement provides visual appeal and better user experience in your movie recommendation interface.

## Implementation Summary

### ✅ What's Been Done

1. **Enhanced `fetch_movies.py`**: New movie data collection now includes poster URLs automatically
2. **Created `enhance_movies_with_posters.py`**: Script to add poster URLs to existing movie data
3. **Created `test_poster_fetching.py`**: Test script to verify poster fetching works
4. **Updated data schema**: All movie objects now include `poster_url` field

### 🎯 TMDB vs OMDB Decision

**Chosen: TMDB** ✅
- You're already using TMDB extensively
- High-quality poster images in multiple sizes
- Free API with generous rate limits
- Consistent availability and quality
- No additional API calls needed (poster data included in movie details)

**Rejected: OMDB** ❌
- Limited to 1000 requests/day on free tier
- Inconsistent poster quality
- Would require additional API calls

## Usage Instructions

### 1. Test Poster Fetching

First, verify everything works with your API key:

```bash
python test_poster_fetching.py
```

This will test poster fetching with known movies and a sample from your dataset.

### 2. Enhance Existing Movie Data

To add poster URLs to your existing `merged_movie_data.json`:

```bash
python enhance_movies_with_posters.py \
  --input merged_movie_data.json \
  --output merged_movie_data_with_posters.json \
  --size w500
```

**Options:**
- `--size`: Poster size (`w92`, `w154`, `w185`, `w342`, `w500`, `w780`, `original`)
- `--batch-size`: Number of movies to process per batch (default: 50)

### 3. Future Data Collection

New movie data collected with `fetch_movies.py` will automatically include poster URLs.

## Poster URL Format

TMDB poster URLs follow this format:
```
https://image.tmdb.org/t/p/{size}/{poster_path}
```

**Available sizes:**
- `w92`: 92px wide (thumbnail)
- `w154`: 154px wide (small)
- `w185`: 185px wide (medium)
- `w342`: 342px wide (large)
- `w500`: 500px wide (recommended for most uses)
- `w780`: 780px wide (high resolution)
- `original`: Original size (can be very large)

## Data Schema

Your movie objects now include:

```json
{
  "title": "The Godfather",
  "year": "1972",
  "director": "Francis Ford Coppola",
  "genre_tags": ["Drama", "Crime"],
  "plot_summary": "...",
  "visual_style": "",
  "critic_reviews": [],
  "user_reviews": [],
  "imdb_id": "tt0068646",
  "tmdb_id": 238,
  "poster_url": "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg"
}
```

## Rate Limiting & Best Practices

- **Rate limiting**: Script includes 0.25s delay between requests
- **Batch processing**: Processes movies in batches of 50 by default
- **Progress saving**: Saves progress after each batch
- **Error handling**: Continues processing even if some posters fail

## Expected Results

Based on your dataset:
- **~95%+ success rate** for movies with TMDB IDs
- **~15,000+ movies** should get poster URLs
- **Processing time**: ~2-3 hours for full dataset (due to rate limiting)

## Troubleshooting

### No Posters Found
- Check your `TMDB_API_KEY` is valid
- Verify network connectivity
- Some very old or obscure movies may not have posters

### API Rate Limits
- TMDB allows 40 requests per 10 seconds
- Script includes built-in rate limiting
- If you hit limits, wait and resume with `--batch-size 10`

### Missing TMDB IDs
- Movies without `tmdb_id` won't get posters
- Consider using the search functionality to find missing IDs

## Next Steps

1. **Test the implementation**: Run `test_poster_fetching.py`
2. **Enhance your data**: Run `enhance_movies_with_posters.py`
3. **Update your UI**: Modify your frontend to display poster images
4. **Generate new profiles**: Run `generate_movie_profiles.py` on enhanced data

## Frontend Integration Example

```html
<!-- Display movie poster -->
<img src="{{ movie.poster_url }}" 
     alt="{{ movie.title }} poster"
     style="width: 200px; height: 300px; object-fit: cover;"
     onerror="this.src='placeholder-poster.jpg'">
```

```javascript
// Handle missing posters
function displayMoviePoster(movie) {
  const img = document.createElement('img');
  img.src = movie.poster_url || 'placeholder-poster.jpg';
  img.alt = `${movie.title} poster`;
  img.onerror = () => img.src = 'placeholder-poster.jpg';
  return img;
}
```

## Legal Considerations

- **Attribution**: TMDB requires attribution when using their API
- **Terms of Service**: Review TMDB's terms of service
- **Image Usage**: Poster images are for display purposes only

## Support

If you encounter issues:
1. Check the test script output
2. Verify your API key is working
3. Check the collection logs for specific errors
4. Consider reducing batch size if hitting rate limits
