# Movie Database Admin Interface

A comprehensive admin interface for managing your movie recommendation database, including observability, movie management, scraping, enrichment, and publishing capabilities.

## Features

### 🎯 Core Functionality

1. **Observability Dashboard**
   - Movie count statistics and data completeness metrics
   - System health monitoring
   - Data quality visualization with progress bars
   - Real-time status updates

2. **Movie Management**
   - Hide/show movies with bulk operations
   - Filter by data quality (missing poster, plot, director, profile)
   - Search and filter movies by title, director, year
   - Bulk enrichment and profile regeneration

3. **Scraping Interface**
   - Director-based movie scraping from TMDB
   - TMDB list scraping
   - Custom collection imports (CSV, Wikipedia, Letterboxd)
   - Preview and selection of scraped movies

4. **Enrichment Pipeline**
   - Metadata enrichment from TMDB and OMDb
   - Image addition (posters and backdrops)
   - LLM profile generation
   - Batch processing with progress tracking

5. **Merge & Publish System**
   - Staging area for new movies
   - Conflict detection and resolution
   - Backup creation before merging
   - Incremental database updates

6. **Authentication & Security**
   - JWT-based authentication
   - Secure admin login
   - Session management
   - API endpoint protection

## Installation & Setup

### Prerequisites

1. **Environment Variables**
   ```bash
   # Required for scraping and enrichment
   export TMDB_API_KEY="your_tmdb_api_key"
   export OMDB_API_KEY="your_omdb_api_key"  # Optional but recommended
   
   # Admin authentication (optional, defaults provided)
   export ADMIN_USERNAME="admin"
   export ADMIN_PASSWORD_HASH="your_password_hash"  # SHA-256 hash
   export ADMIN_JWT_SECRET="your_jwt_secret"  # Random string
   ```

2. **Dependencies**
   ```bash
   pip install fastapi uvicorn requests python-jose[cryptography] passlib[bcrypt] python-multipart
   ```

### Running the Admin Interface

1. **Start the API Server**
   ```bash
   uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access the Admin Interface**
   - Open `admin_login.html` in your browser
   - Default credentials: `admin` / `admin123`
   - Or access directly at `admin.html` (will redirect to login if not authenticated)

## Usage Guide

### Dashboard

The dashboard provides an overview of your movie database:
- **Total Movies**: Complete count of movies in database
- **Complete Profiles**: Movies with full LLM-generated profiles
- **With Images**: Movies that have poster/backdrop URLs
- **Hidden Movies**: Movies currently hidden from public view

Progress bars show data completeness percentages.

### Movie Management

1. **Filtering Movies**
   - Use the search box to find movies by title, director, or year
   - Filter by status: Complete, Partial, Missing Data, Hidden
   - Filter by data quality issues: No Poster, No Plot, No Director, No Profile

2. **Bulk Operations**
   - Select movies using checkboxes
   - Hide/Show selected movies
   - Enrich selected movies with missing data
   - Regenerate profiles for selected movies

### Scraping New Movies

1. **Director-based Scraping**
   - Enter director name (e.g., "Christopher Nolan")
   - Choose inclusion options (shorts, TV movies, documentaries)
   - Review scraped movies and select which to add

2. **TMDB List Scraping**
   - Enter TMDB list ID
   - Add optional description
   - Scrape entire lists (e.g., AFI Top 100)

3. **Custom Collections**
   - Upload CSV files with movie data
   - Import from Wikipedia movie lists
   - Import from Letterboxd lists

### Enrichment Pipeline

1. **Add to Pipeline**
   - Select scraped movies to process
   - Choose enrichment steps: Metadata, Images, Profile Generation
   - Monitor progress in real-time

2. **Batch Processing**
   - Process multiple movies simultaneously
   - Automatic API rate limiting
   - Error handling and retry logic

### Merge & Publish

1. **Review Staging**
   - Check movies ready for merge
   - Identify potential conflicts
   - Review data quality

2. **Merge to Main Database**
   - Create automatic backups
   - Merge new movies with existing data
   - Handle duplicate detection

## API Endpoints

### Authentication
- `POST /admin/auth/login` - Admin login
- `GET /admin/auth/status` - Check authentication status

### Dashboard
- `GET /admin/dashboard` - Get dashboard statistics

### Movie Management
- `GET /admin/movies` - Get all movies with admin metadata
- `POST /admin/movies/hide` - Hide selected movies
- `POST /admin/movies/show` - Show selected movies

### Scraping
- `POST /admin/scrape/director` - Scrape movies by director
- `POST /admin/scrape/tmdb-list` - Scrape TMDB list
- `POST /admin/scrape/custom` - Scrape custom collection

### Pipeline
- `GET /admin/pipeline` - Get pipeline status
- `POST /admin/pipeline/add` - Add movies to staging
- `POST /admin/enrichment/start` - Start enrichment pipeline

### System
- `GET /admin/logs` - Get operation logs
- `POST /admin/backup` - Create database backup
- `GET /admin/health` - Health check

## File Structure

```
movie-recommender/
├── admin.html              # Main admin interface
├── admin_login.html        # Login page
├── admin.js               # Admin interface JavaScript
├── admin_api.py           # Admin API endpoints
├── admin_auth.py          # Authentication system
├── enrichment_pipeline.py # Enrichment processing
├── movie_profiles_merged.json  # Main database
├── hidden_movies.json     # Hidden movies list
└── backups/               # Automatic backups
```

## Security Considerations

1. **Authentication**
   - Change default admin credentials
   - Use strong JWT secrets
   - Implement session timeouts

2. **API Security**
   - All admin endpoints require authentication
   - Rate limiting on scraping operations
   - Input validation and sanitization

3. **Data Protection**
   - Automatic backups before major operations
   - Version control for database changes
   - Audit logging for all operations

## Troubleshooting

### Common Issues

1. **Authentication Failures**
   - Check JWT secret configuration
   - Verify admin credentials
   - Clear browser localStorage

2. **API Connection Issues**
   - Verify API server is running
   - Check CORS configuration
   - Validate API base URL

3. **Scraping Failures**
   - Verify TMDB API key
   - Check rate limiting
   - Review network connectivity

4. **Enrichment Issues**
   - Check LLM provider configuration
   - Verify API keys and quotas
   - Review error logs

### Logs and Debugging

- Check browser console for JavaScript errors
- Review API server logs
- Use the admin logs page for operation history
- Enable debug mode in browser developer tools

## Advanced Configuration

### Custom LLM Providers

The system supports multiple LLM providers for profile generation:
- OpenAI (default)
- Anthropic
- Ollama (local)

Configure in `enrichment_pipeline.py` or via environment variables.

### Database Customization

Modify the movie schema in `admin_api.py` to add custom fields or change data structure.

### UI Customization

The admin interface uses CSS custom properties for easy theming. Modify `admin.html` styles for custom branding.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This admin interface is part of the Subplotly movie recommendation system.
