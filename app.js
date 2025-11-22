// Use the merged dataset which contains all movie profiles
function getSources() {
  // Always use the API endpoint which filters out hidden movies
  // Use the current domain for the API
  const staticBase = window.location.origin;
  // Add cache-busting parameter to prevent browser caching
  const timestamp = Date.now();
  return [`${staticBase}/api/movies?v=${timestamp}`];
}

// No longer needed - image data is now merged into the main profile file

const state = {
  data: [],            // array of movie objects
  filterTones: new Set(),
  filterThemes: new Set(),
  search: '',
  page: 1,
  pageSize: 24,
  apiBase: '',
  featuredTheme: null, // featured theme configuration
};

const els = {
  datasetSelect: document.getElementById('datasetSelect'), // hidden/unused
  searchInput: document.getElementById('searchInput'),
  searchBtn: document.getElementById('searchBtn'),
  clearBtn: document.getElementById('clearBtn'),
  randomizeBtn: document.getElementById('randomizeBtn'),
  toneFilters: document.getElementById('toneFilters'),
  themeFilters: document.getElementById('themeFilters'),
  cards: document.getElementById('cards'),
  stats: document.getElementById('stats'),
  pagination: document.getElementById('pagination'),
  cardTpl: document.getElementById('cardTpl'),
  // Themed carousels
  themedCarousels: document.getElementById('themedCarousels'),
  allMoviesSection: document.getElementById('allMoviesSection'),
  // Featured theme hero
  featuredThemeHero: document.getElementById('featuredThemeHero'),
  // Logo
  siteLogo: document.querySelector('.site-logo'),
  siteTitle: document.querySelector('.site-header h1'),
  // Modal elements
  modalOverlay: document.getElementById('movieModal'),
  modalTitle: document.getElementById('modalTitle'),
  modalBody: document.getElementById('modalBody'),
  modalClose: document.getElementById('modalClose'),
  // Observability UI
  showObsBtn: document.getElementById('showObsBtn'),
  closeObsBtn: document.getElementById('closeObsBtn'),
  obsPanel: document.getElementById('obsPanel'),
  obsBody: document.getElementById('obsBody'),
  // Favorites UI
  showFavoritesBtn: document.getElementById('showFavoritesBtn'),
  closeFavoritesBtn: document.getElementById('closeFavoritesBtn'),
  favoritesPanel: document.getElementById('favoritesPanel'),
  favoritesContent: document.getElementById('favoritesContent'),
  favoritesCount: document.getElementById('favoritesCount'),
  // Movie Details UI
  movieDetailsPanel: document.getElementById('movieDetailsPanel'),
  movieDetailsContent: document.getElementById('movieDetailsContent'),
  movieDetailsTitle: document.getElementById('movieDetailsTitle'),
  closeMovieDetailsBtn: document.getElementById('closeMovieDetailsBtn'),
  // API tools
  apiBaseInput: document.getElementById('apiBaseInput'),
  testApiBtn: document.getElementById('testApiBtn'),
  apiStatus: document.getElementById('apiStatus'),
  // Admin tools
  adminUsername: document.getElementById('adminUsername'),
  adminPassword: document.getElementById('adminPassword'),
  adminLoginBtn: document.getElementById('adminLoginBtn'),
  openAdminBtn: document.getElementById('openAdminBtn'),
  adminStatus: document.getElementById('adminStatus'),
};

// Global function for manual refresh (can be called from browser console)
window.refreshMovieData = function() {
  console.log('🔄 Manual refresh triggered - reloading movie data...');
  loadAllSources();
};

// Test search function
window.testSearch = function(term) {
  console.log('🧪 Testing search with term:', term);
  state.search = term;
  state.page = 1;
  render();
};

// Test function for themed carousels
window.testThemedCarousels = function() {
  console.log('🧪 Testing themed carousels...');
  console.log('Data loaded:', state.data.length > 0);
  console.log('Themed carousels element:', els.themedCarousels);
  console.log('All Movies section element:', els.allMoviesSection);
  
  if (state.data.length > 0 && shouldRenderCarousels()) {
    renderThemedCarousels();
    showAllMoviesSection();
    console.log('✅ Carousels and "All Movies" section should now be visible on the page');
  } else {
    console.log('❌ Cannot show carousels - either no data loaded or search/filters are active');
  }
};

// Test function for admin carousel settings
window.testAdminCarouselSettings = function() {
  console.log('🧪 Testing admin carousel settings...');
  
  // Check localStorage
  const savedSettings = localStorage.getItem('themeCarouselSettings');
  console.log('📦 Raw localStorage:', savedSettings);
  
  if (savedSettings) {
    const parsed = JSON.parse(savedSettings);
    console.log('📦 Parsed settings:', parsed);
  } else {
    console.log('📦 No saved settings found');
  }
  
  // Test getEnabledCarousels
  const enabled = getEnabledCarousels();
  console.log('🎛️ Enabled carousels result:', enabled);
  
  // Force re-render (only if not searching)
  console.log('🔄 Force re-rendering carousels...');
  if (shouldRenderCarousels()) {
    renderThemedCarousels();
  } else {
    console.log('🚫 Skipping carousel re-render due to active search/filters');
  }
};

// Manual function to set carousel settings for testing
window.setCarouselSettings = function(settings) {
  console.log('🎛️ Manually setting carousel settings:', settings);
  localStorage.setItem('themeCarouselSettings', JSON.stringify(settings));
  console.log('✅ Settings saved to localStorage');
  
  // Force re-render (only if not searching)
  if (shouldRenderCarousels()) {
    renderThemedCarousels();
    console.log('🔄 Carousels re-rendered with new settings');
  } else {
    console.log('🚫 Skipping carousel re-render due to active search/filters');
  }
};

// Simple test function to verify the system is working
window.testCarouselSystem = function() {
  console.log('🧪 Testing carousel system...');
  
  // Check if functions exist
  console.log('Functions available:', {
    testAdminCarouselSettings: typeof testAdminCarouselSettings,
    setCarouselSettings: typeof setCarouselSettings,
    getEnabledCarousels: typeof getEnabledCarousels
  });
  
  // Test localStorage
  const settings = localStorage.getItem('themeCarouselSettings');
  console.log('Current localStorage settings:', settings);
  
  // Test getEnabledCarousels
  try {
    const enabled = getEnabledCarousels();
    console.log('Enabled carousels:', enabled.length);
    return enabled;
  } catch (error) {
    console.error('Error in getEnabledCarousels:', error);
    return null;
  }
};

// Reset to homepage state
function resetToHomepage() {
  console.log('🏠 Resetting to homepage state...');
  
  // Clear search and filters
  els.searchInput.value = '';
  state.search = '';
  state.filterTones.clear();
  state.filterThemes.clear();
  
  // Clear theme example button states
  document.querySelectorAll('.theme-example-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  
  // Clear filter chip states
  document.querySelectorAll('.chip').forEach(chip => {
    chip.classList.remove('active');
  });
  
  // Reset to first page
  state.page = 1;
  
  // Update UI
  updateClearButtonVisibility();
  
  // Re-render to show carousels and all movies
  render();
  
  // Scroll to top of the page
  window.scrollTo({ top: 0, behavior: 'smooth' });
  
  console.log('✅ Homepage state restored');
}

// Themed carousel configuration - will be loaded dynamically
let THEMED_CAROUSELS = [];

// Featured theme data - "Sad & Funny"
const MOCK_FEATURED_THEME = {
  is_enabled: true,
  theme_id: "sad_and_funny",
  theme_title: "Sad & Funny",
  description: "Films that make you laugh and ache at the same time. Dysfunctional families, existential spirals, and bittersweet endings—life's contradictions captured on screen.",
  featured_movies: [
    {
      title: "Little Miss Sunshine",
      backdrop_url: "https://image.tmdb.org/t/p/w1280/vD15pg2cXynxeNIknyuvVH2sPx4.jpg",
      year: "2006",
      director: "Jonathan Dayton"
    },
    {
      title: "Shoplifters",
      backdrop_url: "https://image.tmdb.org/t/p/w1280/Z1JeznJExodyj0iUbL1wgkts88.jpg",
      year: "2018",
      director: "Hirokazu Kore-eda"
    },
    {
      title: "Nashville",
      backdrop_url: "https://image.tmdb.org/t/p/w1280/lHH8o3YWBjoteijAI8yTxG3qqpX.jpg",
      year: "1975",
      director: "Robert Altman"
    },
    {
      title: "Eat Drink Man Woman",
      backdrop_url: "https://image.tmdb.org/t/p/w1280/pdmWjfeeXB6MAgDOypmbx133DLk.jpg",
      year: "1994",
      director: "Ang Lee"
    },
    {
      title: "All About My Mother",
      backdrop_url: "https://image.tmdb.org/t/p/w1280/tilClWjFZeUTGJu0pxgF72fvUmN.jpg",
      year: "1999",
      director: "Pedro Almodóvar"
    },
    {
      title: "Sunset Boulevard",
      backdrop_url: "https://image.tmdb.org/t/p/w1280/p47ihFj4A7EpBjmPHdTj4ipyq1S.jpg",
      year: "1950",
      director: "Billy Wilder"
    }
  ],
  primary_backdrop: "https://image.tmdb.org/t/p/w1280/lHH8o3YWBjoteijAI8yTxG3qqpX.jpg"
};

// Load featured theme data (mock for now)
function loadFeaturedTheme() {
  console.log('🎭 Loading featured theme data...');
  // For now, use mock data. Later this will be an API call
  state.featuredTheme = MOCK_FEATURED_THEME;
  console.log('✅ Featured theme loaded:', state.featuredTheme.theme_title);
}

// Load themes from actual movie data
async function loadThemesFromData() {
  try {
    console.log('🔄 Loading themes from movie data for main app...');
    // Add cache-busting parameter to prevent browser caching
    const timestamp = Date.now();
    const response = await fetch(`/api/movies?v=${timestamp}`);
    const data = await response.json();
    
    // Handle object structure where keys are movie titles
    let movies = [];
    if (Array.isArray(data)) {
      movies = data;
    } else if (typeof data === 'object' && !Array.isArray(data)) {
      movies = Object.values(data);
    }
    
    console.log('🎬 Movies loaded for themes:', movies.length);
    
    // Extract all unique themes from movies
    const themeMap = new Map();
    
    movies.forEach(movie => {
      const themes = [];
      
      if (movie.primary_theme) {
        themes.push(movie.primary_theme);
      }
      if (movie.secondary_theme) {
        themes.push(movie.secondary_theme);
      }
      
      themes.forEach(theme => {
        if (theme && typeof theme === 'string' && theme !== 'none') {
          const readableTheme = theme.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          const themeId = theme.toLowerCase().replace(/_/g, '-');
          
          if (themeMap.has(themeId)) {
            themeMap.get(themeId).count++;
          } else {
            themeMap.set(themeId, {
              id: themeId,
              title: readableTheme,
              theme: readableTheme,
              count: 1,
              limit: 10
            });
          }
        }
      });
    });
    
    // Convert to array and filter themes with 10+ movies
    THEMED_CAROUSELS = Array.from(themeMap.values())
      .filter(theme => theme.count >= 10)
      .sort((a, b) => b.count - a.count);
    
    console.log('🎭 Loaded themes for main app:', THEMED_CAROUSELS);
    return THEMED_CAROUSELS;
  } catch (error) {
    console.error('❌ Error loading themes for main app:', error);
    
    // Fallback to hardcoded themes
    THEMED_CAROUSELS = [
      { id: 'found-family', title: 'Found Family', theme: 'Found Family', limit: 10 },
      { id: 'identity-crisis', title: 'Identity Crisis', theme: 'Identity Crisis', limit: 10 },
      { id: 'forbidden-love', title: 'Forbidden Love', theme: 'Forbidden Love', limit: 10 },
      { id: 'underdog-triumph', title: 'Underdog Triumph', theme: 'Underdog Triumph', limit: 10 },
      { id: 'coming-of-age', title: 'Coming Of Age', theme: 'Coming Of Age', limit: 10 }
    ];
    
    return THEMED_CAROUSELS;
  }
}

// Get enabled carousels from admin settings
function getEnabledCarousels() {
  // If THEMED_CAROUSELS is empty, return empty array
  if (!THEMED_CAROUSELS || THEMED_CAROUSELS.length === 0) {
    console.log('🎛️ No themes loaded yet');
    return [];
  }
  
  // Create default settings for all loaded themes (all enabled by default)
  const defaultSettings = {};
  THEMED_CAROUSELS.forEach(theme => {
    defaultSettings[theme.id] = true;
  });
  
  const defaultOrder = THEMED_CAROUSELS.map(c => c.id);
  
  const savedSettings = JSON.parse(localStorage.getItem('themeCarouselSettings') || '{}');
  const savedOrder = JSON.parse(localStorage.getItem('themeOrder') || '[]');
  
  const settings = { ...defaultSettings, ...savedSettings };
  const order = savedOrder.length > 0 ? savedOrder : defaultOrder;
  
  console.log('🎛️ Admin carousel settings:', settings);
  console.log('🎛️ Theme order:', order);
  console.log('🎛️ Available carousels:', THEMED_CAROUSELS.map(c => c.id));
  
  // Filter enabled carousels and sort by saved order
  const enabledCarousels = THEMED_CAROUSELS
    .filter(carousel => settings[carousel.id])
    .sort((a, b) => {
      const aIndex = order.indexOf(a.id);
      const bIndex = order.indexOf(b.id);
      return aIndex - bIndex;
    });
  
  console.log('🎛️ Enabled carousels (ordered):', enabledCarousels.map(c => c.id));
  
  return enabledCarousels;
}

// Centralized function to check if carousels should be rendered
function shouldRenderCarousels() {
  const shouldRender = !state.search && state.filterTones.size === 0 && state.filterThemes.size === 0;
  console.log('🔍 shouldRenderCarousels() called. Search:', state.search, 'Tones:', state.filterTones.size, 'Themes:', state.filterThemes.size, 'Result:', shouldRender);
  return shouldRender;
}

// Render themed carousels
function renderThemedCarousels() {
  console.log('🎠 renderThemedCarousels() called. Stack trace:', new Error().stack);
  
  if (!els.themedCarousels || state.data.length === 0) {
    console.log('🚫 Cannot render carousels: themedCarousels element or data not available');
    return;
  }
  
  // Don't render carousels if there's an active search or filters
  if (!shouldRenderCarousels()) {
    console.log('🚫 Skipping carousel render due to active search/filters. Search:', state.search, 'Tones:', state.filterTones.size, 'Themes:', state.filterThemes.size);
    // Clear any existing content as an extra safeguard
    if (els.themedCarousels) {
      els.themedCarousels.innerHTML = '';
    }
    return;
  }
  
  console.log('🎠 Rendering themed carousels...');
  els.themedCarousels.innerHTML = '';
  
  const enabledCarousels = getEnabledCarousels();
  console.log(`🎠 Found ${enabledCarousels.length} enabled carousels`);
  
  if (enabledCarousels.length === 0) {
    console.log('🚫 No enabled carousels found');
    return;
  }
  
  enabledCarousels.forEach(carouselConfig => {
    const movies = getMoviesByTheme(carouselConfig.theme, carouselConfig.limit);
    console.log(`🎬 Found ${movies.length} movies for theme: ${carouselConfig.theme}`);
    if (movies.length === 0) return;
    
    const carouselElement = createCarouselElement(carouselConfig, movies);
    els.themedCarousels.appendChild(carouselElement);
  });
  
  console.log('✅ Themed carousels rendered');
}

// Render featured theme hero section
function renderFeaturedThemeHero() {
  console.log('🎭 renderFeaturedThemeHero() called');
  
  if (!els.featuredThemeHero || !state.featuredTheme || !state.featuredTheme.is_enabled) {
    console.log('🚫 Cannot render featured theme: element not found or disabled');
    if (els.featuredThemeHero) {
      els.featuredThemeHero.innerHTML = '';
    }
    return;
  }
  
  // Don't render if there's an active search or filters
  if (!shouldRenderCarousels()) {
    console.log('🚫 Skipping featured theme render due to active search/filters');
    if (els.featuredThemeHero) {
      els.featuredThemeHero.innerHTML = '';
    }
    return;
  }
  
  const theme = state.featuredTheme;
  console.log('🎭 Rendering featured theme:', theme.theme_title);
  
  // Create movie shots HTML with visible info
  const movieShots = theme.featured_movies.map(movie => `
    <div class="featured-movie-shot" data-movie-title="${escapeHtml(movie.title)}">
      <div class="featured-movie-image" style="background-image: url('${movie.backdrop_url}')"></div>
      <div class="featured-movie-info">
        <h4 class="featured-movie-title">${movie.title}</h4>
        <div class="featured-movie-meta">${movie.director} • ${movie.year}</div>
      </div>
    </div>
  `).join('');
  
  // Create the hero HTML with side-by-side layout
  const heroHTML = `
    <div class="featured-theme-container">
      <div class="featured-theme-content">
        <div class="featured-theme-badge">Our Picks</div>
        <h1 class="featured-theme-title">${theme.theme_title}</h1>
        <p class="featured-theme-description">${theme.description}</p>
      </div>
      <div class="featured-theme-movies">
        <div class="featured-theme-shots">
          ${movieShots}
        </div>
      </div>
    </div>
  `;
  
  els.featuredThemeHero.innerHTML = heroHTML;

  // Add click event listeners to featured movie cards
  const featuredMovieCards = els.featuredThemeHero.querySelectorAll('.featured-movie-shot');
  featuredMovieCards.forEach(card => {
    const movieTitle = card.getAttribute('data-movie-title');
    if (movieTitle) {
      // Find the movie in the data and show its details
      const movie = state.data.find(m => escapeHtml(m.title) === movieTitle);
      if (movie) {
        card.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
          showMovieDetailsPanel(movie);
        });
        
        // Add cursor pointer style
        card.style.cursor = 'pointer';
      }
    }
  });

  console.log('✅ Featured theme hero rendered');
}


// Show "All Movies" section
function showAllMoviesSection() {
  if (els.allMoviesSection) {
    els.allMoviesSection.style.display = 'block';
  }
}

// Hide "All Movies" section
function hideAllMoviesSection() {
  if (els.allMoviesSection) {
    els.allMoviesSection.style.display = 'none';
  }
}

// Randomize movies in a specific carousel
function randomizeCarouselMovies(theme) {
  console.log(`🎲 Randomizing movies for theme: ${theme}`);
  
  // Find all movies for this theme
  const allThemeMovies = state.data.filter(movie => {
    const themes = movie.themes || [];
    return themes.some(t => t.toLowerCase() === theme.toLowerCase());
  });
  
  if (allThemeMovies.length === 0) {
    console.log(`❌ No movies found for theme: ${theme}`);
    return;
  }
  
  // Shuffle and take first 10
  const shuffled = [...allThemeMovies].sort(() => Math.random() - 0.5);
  const randomMovies = shuffled.slice(0, 10);
  
  // Find the carousel scroll container for this theme
  const carouselScroll = document.querySelector(`.carousel-scroll[data-theme="${theme}"]`);
  if (carouselScroll) {
    // Clear existing content first
    carouselScroll.innerHTML = '';
    
    // Update the carousel with new random movies
    carouselScroll.innerHTML = randomMovies.map(movie => createCarouselCard(movie)).join('');
    console.log(`✅ Randomized ${randomMovies.length} movies for theme: ${theme}`);
  } else {
    console.log(`❌ Carousel container not found for theme: ${theme}`);
  }
}

// Get movies by theme
function getMoviesByTheme(theme, limit) {
  const matchingMovies = state.data.filter(movie => {
    // Helper function to normalize theme for comparison
    const normalizeTheme = (themeStr) => {
      if (!themeStr) return '';
      return themeStr.replace(/_/g, ' ').toLowerCase();
    };
    
    // Check both primary and secondary themes (exclude "none" secondary themes)
    const primaryMatch = movie.primary_theme && 
      normalizeTheme(movie.primary_theme) === normalizeTheme(theme);
    const secondaryMatch = movie.secondary_theme && 
      movie.secondary_theme !== 'none' &&
      normalizeTheme(movie.secondary_theme) === normalizeTheme(theme);
    
    return primaryMatch || secondaryMatch;
  });
  
  console.log(`🎬 Theme matching debug for "${theme}":`, {
    totalMovies: state.data.length,
    matchingMovies: matchingMovies.length,
    sampleMatches: matchingMovies.slice(0, 3).map(m => ({
      title: m.title,
      primary: m.primary_theme,
      secondary: m.secondary_theme
    }))
  });
  
  // Randomize the order and return limited results
  return [...matchingMovies]
    .sort(() => Math.random() - 0.5)
    .slice(0, limit);
}

// Create carousel element
function createCarouselElement(config, movies) {
  const carousel = document.createElement('div');
  carousel.className = 'themed-carousel';
  carousel.innerHTML = `
    <div class="carousel-header">
      <h3 class="carousel-title">${config.title}</h3>
      <div class="carousel-actions">
        <button class="carousel-randomize" data-theme="${config.theme}" title="Randomize movies in this theme">
          <svg class="randomize-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
            <path d="M21 3v5h-5"></path>
            <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
            <path d="M3 21v-5h5"></path>
          </svg>
          Random
        </button>
        <button class="carousel-see-all" data-theme="${config.theme}">See All</button>
      </div>
    </div>
    <div class="carousel-container">
      <div class="carousel-scroll" data-theme="${config.theme}">
        ${movies.map(movie => createCarouselCard(movie)).join('')}
      </div>
    </div>
  `;
  
  // Add click handlers to carousel cards
  const carouselCards = carousel.querySelectorAll('.carousel-card');
  carouselCards.forEach((card, index) => {
    const movie = movies[index];
    if (movie) {
      card.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        showMovieDetailsPanel(movie);
      });
      
      // Add cursor pointer style
      card.style.cursor = 'pointer';
    }
  });
  
  return carousel;
}

// Create individual carousel card
function createCarouselCard(movie) {
  const posterUrl = movie.poster_url || movie.backdrop_url || '';
  const director = movie.director || '';
  const year = movie.year || movie.release_year || '';
  // Escape HTML to prevent attribute breaking
  const escapedTitle = escapeHtml(movie.title);
  
  return `
    <div class="carousel-card" data-movie-title="${escapedTitle}">
      <div class="carousel-card-poster" style="background-image: url('${posterUrl}')"></div>
      <div class="carousel-card-content">
        <h4 class="carousel-card-title">${movie.title}</h4>
        <div class="carousel-card-subtitle">${director}${year ? ` • ${year}` : ''}</div>
      </div>
    </div>
  `;
}

// Force cache clear and style refresh
window.forceStyleRefresh = function() {
  console.log('🔄 Force refreshing styles...');
  // Reload CSS
  const links = document.querySelectorAll('link[rel="stylesheet"]');
  links.forEach(link => {
    const href = link.href.split('?')[0];
    link.href = href + '?v=' + Date.now();
  });
  // Force re-render of all cards
  setTimeout(() => {
    document.querySelectorAll('.card').forEach(card => {
      handleTagOverflow(card);
    });
  }, 100);
};

// Force refresh everything (CSS, JS, and page)
window.forceFullRefresh = function() {
  console.log('🔄 Force refreshing everything...');
  // Reload CSS
  const links = document.querySelectorAll('link[rel="stylesheet"]');
  links.forEach(link => {
    const href = link.href.split('?')[0];
    link.href = href + '?v=' + Date.now();
  });
  // Reload JS
  const scripts = document.querySelectorAll('script[src]');
  scripts.forEach(script => {
    if (script.src.includes('app.js')) {
      const src = script.src.split('?')[0];
      script.src = src + '?v=' + Date.now();
    }
  });
  console.log('✅ Cache-busting parameters updated. Please refresh the page manually.');
};

// Debug function to check featured theme scroll setup
window.debugFeaturedThemeScroll = function() {
  console.log('🔍 Debugging featured theme scroll setup...');
  
  const hero = document.querySelector('.featured-theme-hero');
  const container = document.querySelector('.featured-theme-container');
  const movies = document.querySelector('.featured-theme-movies');
  const shots = document.querySelector('.featured-theme-shots');
  
  console.log('Elements found:', {
    hero: !!hero,
    container: !!container,
    movies: !!movies,
    shots: !!shots
  });
  
  if (hero) {
    console.log('Hero element HTML:', hero.innerHTML.substring(0, 200) + '...');
    const heroStyle = window.getComputedStyle(hero);
    console.log('Hero computed styles:', {
      display: heroStyle.display,
      visibility: heroStyle.visibility,
      height: heroStyle.height,
      overflow: heroStyle.overflow,
      position: heroStyle.position
    });
  }
  
  if (shots) {
    const computedStyle = window.getComputedStyle(shots);
    console.log('Featured theme shots computed styles:', {
      display: computedStyle.display,
      overflowX: computedStyle.overflowX,
      overflowY: computedStyle.overflowY,
      flexWrap: computedStyle.flexWrap,
      width: computedStyle.width,
      maxWidth: computedStyle.maxWidth
    });
    
    const movieShots = shots.querySelectorAll('.featured-movie-shot');
    console.log('Movie shots found:', movieShots.length);
    
    movieShots.forEach((shot, index) => {
      const shotStyle = window.getComputedStyle(shot);
      console.log(`Movie shot ${index + 1}:`, {
        width: shotStyle.width,
        minWidth: shotStyle.minWidth,
        flexShrink: shotStyle.flexShrink
      });
    });
  }
  
  console.log('Screen width:', window.innerWidth);
  console.log('Current breakpoint:', window.innerWidth <= 1199 ? 'Medium/Small' : 'Large');
  console.log('State data length:', state.data.length);
  console.log('Should render carousels:', shouldRenderCarousels());
  console.log('Featured theme state:', state.featuredTheme);
};

// Force re-render featured theme
window.forceRenderFeaturedTheme = function() {
  console.log('🔄 Force re-rendering featured theme...');
  if (state.featuredTheme && state.featuredTheme.is_enabled) {
    renderFeaturedThemeHero();
    console.log('✅ Featured theme re-rendered');
  } else {
    console.log('❌ No featured theme to render');
  }
};


// Test different screen sizes for horizontal scroll
window.testScreenSizes = function() {
  console.log('🖥️ Testing screen sizes for horizontal scroll...');
  
  const sizes = [
    { width: 480, name: 'Small Mobile' },
    { width: 768, name: 'Mobile' },
    { width: 1024, name: 'Tablet' },
    { width: 1200, name: 'Desktop' },
    { width: 1600, name: 'Large Desktop' }
  ];
  
  sizes.forEach(size => {
    console.log(`\n📱 ${size.name} (${size.width}px):`);
    
    // Temporarily set window width for testing
    const originalWidth = window.innerWidth;
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: size.width,
    });
    
    // Trigger resize event
    window.dispatchEvent(new Event('resize'));
    
    // Check which breakpoint would apply
    let breakpoint = 'Large (≥1200px)';
    if (size.width < 480) breakpoint = 'Extra Small (<480px)';
    else if (size.width < 768) breakpoint = 'Small Mobile (480px-767px)';
    else if (size.width < 1200) breakpoint = 'Medium (768px-1199px)';
    else if (size.width < 1600) breakpoint = 'Large (1200px-1599px)';
    else breakpoint = 'Extra Large (≥1600px)';
    
    console.log(`  Breakpoint: ${breakpoint}`);
    
    // Restore original width
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalWidth,
    });
  });
  
  console.log('\n🔄 Restored original screen size');
};

// Debug function to check flex-wrap behavior
window.debugFlexWrap = function() {
  console.log('🔍 Debugging flex-wrap behavior...');
  
  const shots = document.querySelector('.featured-theme-shots');
  if (shots) {
    const computedStyle = window.getComputedStyle(shots);
    console.log('Featured theme shots flex properties:', {
      display: computedStyle.display,
      flexWrap: computedStyle.flexWrap,
      flexDirection: computedStyle.flexDirection,
      overflowX: computedStyle.overflowX,
      overflowY: computedStyle.overflowY,
      width: computedStyle.width,
      maxWidth: computedStyle.maxWidth
    });
    
    const movieShots = shots.querySelectorAll('.featured-movie-shot');
    console.log('Movie shots count:', movieShots.length);
    
    movieShots.forEach((shot, index) => {
      const shotStyle = window.getComputedStyle(shot);
      console.log(`Movie shot ${index + 1}:`, {
        width: shotStyle.width,
        minWidth: shotStyle.minWidth,
        flexShrink: shotStyle.flexShrink,
        flexWrap: shotStyle.flexWrap
      });
    });
    
    // Check if any shots are wrapping
    const containerRect = shots.getBoundingClientRect();
    let totalWidth = 0;
    movieShots.forEach((shot, index) => {
      const shotRect = shot.getBoundingClientRect();
      totalWidth += shotRect.width + (index > 0 ? 20 : 0); // 20px gap
    });
    
    console.log('Container width:', containerRect.width);
    console.log('Total content width:', totalWidth);
    console.log('Should scroll:', totalWidth > containerRect.width);
  }
};

// Debug function to test horizontal scroll
window.testHorizontalScroll = function() {
  console.log('🔄 Testing horizontal scroll...');
  
  const shots = document.querySelector('.featured-theme-shots');
  if (shots) {
    console.log('Scroll properties:', {
      scrollWidth: shots.scrollWidth,
      clientWidth: shots.clientWidth,
      scrollLeft: shots.scrollLeft,
      canScroll: shots.scrollWidth > shots.clientWidth
    });
    
    // Test scroll
    const originalScrollLeft = shots.scrollLeft;
    shots.scrollLeft = 100;
    console.log('After setting scrollLeft to 100:', shots.scrollLeft);
    shots.scrollLeft = originalScrollLeft;
    
    // Test touch scroll
    console.log('Touch scroll test - try swiping on the container');
  }
};

// Toggle between overflow hidden and horizontal scroll
window.toggleTagScrollMode = function() {
  const tagRows = document.querySelectorAll('.tags-row');
  tagRows.forEach(row => {
    if (row.classList.contains('scrollable')) {
      row.classList.remove('scrollable');
      row.style.overflow = 'hidden';
      console.log('Switched to overflow hidden mode');
    } else {
      row.classList.add('scrollable');
      row.style.overflow = 'auto';
      console.log('Switched to horizontal scroll mode');
    }
  });
};

// Manual trigger for tag overflow handling
window.manualTagOverflow = function() {
  console.log('Manually triggering tag overflow handling...');
  document.querySelectorAll('.card').forEach((card, index) => {
    console.log(`Manual processing card ${index + 1}`);
    handleTagOverflow(card);
  });
};

// Simple test: show +X more for any card with more than 3 tags
window.testTagOverflow = function() {
  console.log('Testing simple tag overflow...');
  document.querySelectorAll('.card').forEach((card, index) => {
    const tagRow = card.querySelector('.tags-row');
    if (!tagRow) return;
    
    const tags = tagRow.querySelectorAll('.tag');
    console.log(`Card ${index + 1}: ${tags.length} tags`);
    
    if (tags.length > 3) {
      // Remove existing more indicator
      const existingMore = tagRow.querySelector('.tag-more');
      if (existingMore) existingMore.remove();
      
      // Hide tags beyond the first 3
      tags.forEach((tag, tagIndex) => {
        if (tagIndex >= 3) {
          tag.classList.add('hidden');
        }
      });
      
      // Add +X more indicator
      const moreIndicator = document.createElement('span');
      moreIndicator.className = 'tag-more';
      moreIndicator.textContent = `+${tags.length - 3} more`;
      moreIndicator.style.cursor = 'pointer';
      moreIndicator.style.background = '#ff6b6b';
      moreIndicator.style.color = 'white';
      moreIndicator.style.padding = '4px 8px';
      moreIndicator.style.borderRadius = '4px';
      moreIndicator.style.fontSize = '11px';
      moreIndicator.style.display = 'inline-flex';
      moreIndicator.style.alignItems = 'center';
      moreIndicator.style.marginLeft = '4px';
      tagRow.appendChild(moreIndicator);
      
      console.log(`Added +${tags.length - 3} more indicator to card ${index + 1}`);
    }
  });
};

// Debug function to inspect tag structure
window.debugTagStructure = function() {
  console.log('🔍 Debugging tag structure...');
  document.querySelectorAll('.card').forEach((card, cardIndex) => {
    const tagRow = card.querySelector('.tags-row');
    if (!tagRow) {
      console.log(`Card ${cardIndex + 1}: No tag row found`);
      return;
    }
    
    console.log(`Card ${cardIndex + 1} structure:`, {
      tagRow: tagRow,
      tagRowChildren: tagRow.children,
      tagsContainers: tagRow.querySelectorAll('.tags'),
      allTags: tagRow.querySelectorAll('.tag'),
      tagCount: tagRow.querySelectorAll('.tag').length
    });
    
    // Log each tag
    const tags = tagRow.querySelectorAll('.tag');
    tags.forEach((tag, tagIndex) => {
      console.log(`  Tag ${tagIndex + 1}: "${tag.textContent}"`);
    });
  });
};

// Force tag overflow solution - more aggressive approach
window.forceTagOverflow = function() {
  console.log('🚀 Force applying tag overflow solution...');
  
  document.querySelectorAll('.card').forEach((card, cardIndex) => {
    const tagRow = card.querySelector('.tags-row');
    if (!tagRow) {
      console.log(`Card ${cardIndex + 1}: No tag row found`);
      return;
    }
    
    // Get all tags
    const tags = tagRow.querySelectorAll('.tag');
    console.log(`Card ${cardIndex + 1}: Found ${tags.length} tags`);
    
    if (tags.length > 3) {
      // Remove any existing more indicators
      const existingMore = tagRow.querySelector('.tag-more');
      if (existingMore) {
        existingMore.remove();
      }
      
      // Hide tags beyond first 3
      tags.forEach((tag, tagIndex) => {
        if (tagIndex >= 3) {
          tag.style.display = 'none';
        }
      });
      
      // Create a very visible +X more indicator
      const indicator = document.createElement('span');
      indicator.className = 'tag-more';
      indicator.textContent = `+${tags.length - 3} MORE`;
      indicator.style.cssText = `
        display: inline-flex !important;
        background: #ff0000 !important;
        color: white !important;
        padding: 6px 12px !important;
        border-radius: 8px !important;
        font-size: 12px !important;
        font-weight: bold !important;
        margin-left: 8px !important;
        cursor: pointer !important;
        align-items: center !important;
        flex-shrink: 0 !important;
        white-space: nowrap !important;
        border: 2px solid #cc0000 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
        z-index: 9999 !important;
        position: relative !important;
      `;
      
      // Add click handler
      indicator.addEventListener('click', (e) => {
        e.stopPropagation();
        const isExpanded = indicator.textContent.includes('LESS');
        
        if (isExpanded) {
          // Collapse
          tags.forEach((tag, tagIndex) => {
            if (tagIndex >= 3) {
              tag.style.display = 'none';
            }
          });
          indicator.textContent = `+${tags.length - 3} MORE`;
        } else {
          // Expand
          tags.forEach(tag => tag.style.display = '');
          indicator.textContent = 'LESS';
        }
      });
      
      tagRow.appendChild(indicator);
      console.log(`✅ Added BRIGHT RED +${tags.length - 3} MORE indicator to card ${cardIndex + 1}`);
    }
  });
  
  console.log('🎉 Force tag overflow completed!');
};

// Simple immediate test - just add a visible indicator to any card
window.testSimpleTagOverflow = function() {
  console.log('🧪 Simple test - adding visible indicators to all cards...');
  
  document.querySelectorAll('.card').forEach((card, cardIndex) => {
    const tagRow = card.querySelector('.tags-row');
    if (!tagRow) {
      console.log(`Card ${cardIndex + 1}: No tag row found`);
      return;
    }
    
    // Remove any existing test indicators
    const existingTest = tagRow.querySelector('.test-indicator');
    if (existingTest) {
      existingTest.remove();
    }
    
    // Add a simple test indicator
    const testIndicator = document.createElement('div');
    testIndicator.className = 'test-indicator';
    testIndicator.textContent = `TEST ${cardIndex + 1}`;
    testIndicator.style.cssText = `
      display: inline-block !important;
      background: #00ff00 !important;
      color: black !important;
      padding: 8px 12px !important;
      border-radius: 8px !important;
      font-size: 14px !important;
      font-weight: bold !important;
      margin-left: 8px !important;
      border: 2px solid #00cc00 !important;
    `;
    
    tagRow.appendChild(testIndicator);
    console.log(`✅ Added TEST ${cardIndex + 1} indicator to card ${cardIndex + 1}`);
  });
  
  console.log('✅ Simple test completed. You should see green "TEST X" indicators on all cards.');
};

// Test horizontal scrolling
window.testTagScrolling = function() {
  console.log('🧪 Testing horizontal tag scrolling...');
  enableTagScrolling();
  console.log('✅ Horizontal scrolling enabled! Try scrolling horizontally on tag rows.');
};

// Manual test function for tag overflow
window.testTagOverflowClean = function() {
  console.log('🧪 Testing clean tag overflow solution...');
  debugTagStructure();
  handleTagOverflowClean();
  console.log('✅ Tag overflow test completed. Check cards with more than 3 tags.');
};

// Enable horizontal scrolling for tags
window.enableTagScrolling = function() {
  console.log('Enabling horizontal tag scrolling...');
  
  document.querySelectorAll('.card').forEach((card, cardIndex) => {
    const tagRow = card.querySelector('.tags-row');
    if (!tagRow) {
      console.log(`Card ${cardIndex + 1}: No tag row found`);
      return;
    }
    
    // Remove any existing more indicators
    const existingMore = tagRow.querySelector('.tag-more');
    if (existingMore) {
      existingMore.remove();
    }
    
    // Reset all tags to visible
    const tags = tagRow.querySelectorAll('.tag');
    tags.forEach(tag => {
      tag.style.display = '';
      tag.classList.remove('hidden');
    });
    
    // Enable horizontal scrolling
    tagRow.classList.add('scrollable');
    tagRow.style.overflowX = 'auto';
    tagRow.style.overflowY = 'hidden';
    
    console.log(`✅ Enabled horizontal scrolling for card ${cardIndex + 1} with ${tags.length} tags`);
  });
  
  console.log('🎉 Horizontal tag scrolling enabled for all cards!');
};

// Add keyboard shortcut for manual refresh (Ctrl+Shift+R or Cmd+Shift+R)
document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'R') {
    e.preventDefault();
    console.log('🔄 Manual refresh triggered via keyboard shortcut');
    window.refreshMovieData();
  }
});

// Handle tag overflow on window resize
const debouncedHandleResize = debounce(() => {
  document.querySelectorAll('.card').forEach(card => {
    handleTagOverflow(card);
  });
}, 150);

window.addEventListener('resize', debouncedHandleResize);

init();

async function init() {
  console.log('🎬 Initializing app...');
  console.log('🎬 Checking elements:', {
    showFavoritesBtn: !!els.showFavoritesBtn,
    favoritesPanel: !!els.favoritesPanel,
    favoritesCount: !!els.favoritesCount,
    favoritesContent: !!els.favoritesContent
  });
  
  // Hide dataset selector if present
  if (els.datasetSelect) els.datasetSelect.closest('label')?.setAttribute('style', 'display:none');

  bindEvents();
  // Modal close controls
  if (els.modalClose) els.modalClose.addEventListener('click', closeModal);
  if (els.modalOverlay) els.modalOverlay.addEventListener('click', (e) => {
    if (e.target === els.modalOverlay) closeModal();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal();
      // Also close favorites panel if it's open
      if (els.favoritesPanel && !els.favoritesPanel.classList.contains('hidden')) {
        hideFavoritesPanel();
      }
    }
  });
  
  // Load featured theme data
  loadFeaturedTheme();
  
  await loadAllSources();
}

// Normalize an API base URL by ensuring scheme and removing trailing slash
function normalizeBase(val) {
  let v = (val || '').trim();
  if (!v) return '';
  if (!/^https?:\/\//i.test(v)) {
    if (v.startsWith('//')) v = 'http:' + v; else v = 'http://' + v;
  }
  v = v.replace(/\/$/, '');
  return v;
}

function bindEvents() {
  // Only update state on input; do not execute search yet
  els.searchInput.addEventListener('input', () => {
    state.search = els.searchInput.value.trim().toLowerCase();
    updateClearButtonVisibility();
  });

  // Execute search on button click
  if (els.searchBtn) {
    els.searchBtn.addEventListener('click', () => {
      // Update search state from input value
      state.search = els.searchInput.value.trim().toLowerCase();
      console.log('🔍 Search button clicked, search term:', state.search);
      state.page = 1;
      render();
    });
  }

  // Execute search on Enter key
  els.searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      // Update search state from input value
      state.search = els.searchInput.value.trim().toLowerCase();
      console.log('🔍 Enter key pressed, search term:', state.search);
      state.page = 1;
      render();
    }
  });

  els.clearBtn.addEventListener('click', () => {
    els.searchInput.value = '';
    state.search = '';
    state.filterTones.clear();
    state.filterThemes.clear();
    // Clear theme example button states
    document.querySelectorAll('.theme-example-btn').forEach(btn => {
      btn.classList.remove('active');
    });
    updateClearButtonVisibility();
    state.page = 1;
    render();
  });

  // Randomize button
  if (els.randomizeBtn) {
    els.randomizeBtn.addEventListener('click', () => {
      randomizeMovies();
    });
  }

  // API tools wiring
  if (els.apiBaseInput) {
    // Initialize from localStorage
    try {
      const saved = localStorage.getItem('apiBase');
      if (saved) {
        els.apiBaseInput.value = saved;
        state.apiBase = saved;
      }
    } catch {}
    els.apiBaseInput.addEventListener('change', () => {
      const val = (els.apiBaseInput.value || '');
      const norm = normalizeBase(val);
      state.apiBase = norm;
      try { if (norm) localStorage.setItem('apiBase', norm); else localStorage.removeItem('apiBase'); } catch {}
      if (els.apiStatus) els.apiStatus.textContent = norm ? `Base set to ${norm}` : 'API base cleared';
      els.apiBaseInput.value = norm; // reflect normalization in UI
    });
  }
  if (els.testApiBtn) {
    els.testApiBtn.addEventListener('click', async () => {
      const raw = (els.apiBaseInput?.value || localStorage.getItem('apiBase') || '');
      const base = normalizeBase(raw);
      if (!base) {
        if (els.apiStatus) els.apiStatus.textContent = 'Enter an API base (e.g., http://127.0.0.1:8003)';
        return;
      }
      els.apiBaseInput.value = base;
      if (els.apiStatus) els.apiStatus.textContent = 'Testing…';
      try {
        const res = await fetch(`${base}/health`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        const j = await res.json().catch(()=>({}));
        try { localStorage.setItem('apiBase', base); } catch {}
        if (els.apiStatus) els.apiStatus.textContent = `OK (${j?.profiles ?? 'n/a'} profiles)`;
      } catch (e) {
        if (els.apiStatus) els.apiStatus.textContent = `Failed: ${e.message}. Tip: ensure the URL includes http:// and the server is running.`;
      }
    });
  }

  // Admin login functionality
  if (els.adminLoginBtn) {
    els.adminLoginBtn.addEventListener('click', async () => {
      const username = els.adminUsername?.value?.trim();
      const password = els.adminPassword?.value?.trim();
      const base = normalizeBase(els.apiBaseInput?.value || localStorage.getItem('apiBase') || '');
      
      if (!username || !password) {
        if (els.adminStatus) els.adminStatus.textContent = 'Enter username and password';
        return;
      }
      
      if (!base) {
        if (els.adminStatus) els.adminStatus.textContent = 'Set API base first';
        return;
      }
      
      if (els.adminStatus) els.adminStatus.textContent = 'Logging in...';
      
      try {
        const response = await fetch(`${base}/admin/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            username: username,
            password: password
          })
        });
        
        if (response.ok) {
          const data = await response.json();
          localStorage.setItem('admin_token', data.access_token);
          localStorage.setItem('admin_api_base', base);
          if (els.adminStatus) els.adminStatus.textContent = 'Login successful!';
          
          // Clear password field
          if (els.adminPassword) els.adminPassword.value = '';
        } else {
          const error = await response.json();
          if (els.adminStatus) els.adminStatus.textContent = `Login failed: ${error.detail || 'Invalid credentials'}`;
        }
      } catch (error) {
        if (els.adminStatus) els.adminStatus.textContent = `Connection failed: ${error.message}`;
      }
    });
  }

  // Open admin panel functionality
  if (els.openAdminBtn) {
    els.openAdminBtn.addEventListener('click', () => {
      // Admin panel is served on port 8002
      const adminUrl = 'http://127.0.0.1:8002/admin.html';
      window.open(adminUrl, '_blank');
    });
  }

  // Check admin login status on load
  checkAdminStatus();

  // Observability Dashboard events
  if (els.showObsBtn) {
    els.showObsBtn.addEventListener('click', () => {
      showObsPanel();
    });
  }
  if (els.closeObsBtn) {
    els.closeObsBtn.addEventListener('click', () => {
      hideObsPanel();
    });
  }

  // Favorites panel events
  if (els.showFavoritesBtn) {
    els.showFavoritesBtn.addEventListener('click', () => {
      showFavoritesPanel();
    });
  }
  if (els.closeFavoritesBtn) {
    els.closeFavoritesBtn.addEventListener('click', () => {
      hideFavoritesPanel();
    });
  }
  
  // Movie Details Panel event handlers
  if (els.closeMovieDetailsBtn) {
    els.closeMovieDetailsBtn.addEventListener('click', () => {
      hideMovieDetailsPanel();
    });
  }
  
  // Click outside to close panels
  document.addEventListener('click', (e) => {
    // Close favorites panel
    if (els.favoritesPanel && !els.favoritesPanel.classList.contains('hidden')) {
      const isClickInsidePanel = els.favoritesPanel.contains(e.target);
      const isClickOnFavoritesBtn = els.showFavoritesBtn && els.showFavoritesBtn.contains(e.target);
      
      if (!isClickInsidePanel && !isClickOnFavoritesBtn) {
        hideFavoritesPanel();
      }
    }
    
    // Close movie details panel
    if (els.movieDetailsPanel && !els.movieDetailsPanel.classList.contains('hidden')) {
      const isClickInsidePanel = els.movieDetailsPanel.contains(e.target);
      const isClickOnCarouselCard = e.target.closest('.carousel-card');
      const isClickOnMovieCard = e.target.closest('.card');
      
      if (!isClickInsidePanel && !isClickOnCarouselCard && !isClickOnMovieCard) {
        hideMovieDetailsPanel();
      }
    }
  });


  // Theme example buttons
  document.querySelectorAll('.theme-example-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const theme = btn.getAttribute('data-theme');
      if (state.filterThemes.has(theme)) {
        state.filterThemes.delete(theme);
        btn.classList.remove('active');
      } else {
        state.filterThemes.add(theme);
        btn.classList.add('active');
      }
      state.page = 1;
      render();
    });
  });

  // Logo and title clicks - reset to homepage
  if (els.siteLogo) {
    els.siteLogo.addEventListener('click', resetToHomepage);
  }
  if (els.siteTitle) {
    els.siteTitle.addEventListener('click', resetToHomepage);
  }

  // Carousel card clicks - delegate to themed carousels container
  if (els.themedCarousels) {
    els.themedCarousels.addEventListener('click', (e) => {
      const carouselCard = e.target.closest('.carousel-card');
      if (carouselCard) {
        const movieTitle = carouselCard.getAttribute('data-movie-title');
        if (movieTitle) {
          // Find the movie in the data and show its modal
          // Compare with escaped titles since data-movie-title is escaped
          const movie = state.data.find(m => escapeHtml(m.title) === movieTitle);
          if (movie) {
            showMovieDetailsPanel(movie);
          }
        }
        return;
      }
      
      // Handle "Randomize" button clicks
      if (e.target.classList.contains('carousel-randomize') || e.target.closest('.carousel-randomize')) {
        const button = e.target.classList.contains('carousel-randomize') ? e.target : e.target.closest('.carousel-randomize');
        const theme = button.getAttribute('data-theme');
        if (theme) {
          randomizeCarouselMovies(theme);
        }
        return;
      }
      
      // Handle "See All" button clicks
      if (e.target.classList.contains('carousel-see-all')) {
        const theme = e.target.getAttribute('data-theme');
        if (theme) {
          // Clear existing filters and search
          els.searchInput.value = '';
          state.search = '';
          state.filterTones.clear();
          state.filterThemes.clear();
          
          // Clear theme example button states
          document.querySelectorAll('.theme-example-btn').forEach(btn => {
            btn.classList.remove('active');
          });
          
          // Clear filter chip states
          document.querySelectorAll('.chip').forEach(chip => {
            chip.classList.remove('active');
          });
          
          // Set the theme filter
          state.filterThemes.add(theme);
          
          // Activate the corresponding theme example button
          const themeBtn = document.querySelector(`[data-theme="${theme}"]`);
          if (themeBtn) {
            themeBtn.classList.add('active');
          }
          
          updateClearButtonVisibility();
          state.page = 1;
          render();
        }
      }
    });
  }
}

function updateClearButtonVisibility() {
  if (els.clearBtn) {
    const hasValue = els.searchInput.value.trim().length > 0;
    els.clearBtn.style.display = hasValue ? 'flex' : 'none';
  }
}

function randomizeMovies() {
  // Clear any existing filters and search
  els.searchInput.value = '';
  state.search = '';
  state.filterTones.clear();
  state.filterThemes.clear();
  
  // Clear theme example button states
  document.querySelectorAll('.theme-example-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  
  // Clear filter chip states
  document.querySelectorAll('.chip').forEach(chip => {
    chip.classList.remove('active');
  });
  
  updateClearButtonVisibility();
  
  // Shuffle the data array and render
  const shuffled = [...state.data].sort(() => Math.random() - 0.5);
  state.data = shuffled;
  state.page = 1;
  render();
}

async function loadAllSources() {
  els.stats.textContent = 'Loading…';
  els.cards.innerHTML = '';

  const merged = new Map(); // key: normalized title -> movie object
  const errors = [];

  for (const path of getSources()) {
    try {
      const res = await fetch(path);
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const raw = await res.json();

      // Source data is expected to be an object keyed by title
      let processedCount = 0;
      let skippedCount = 0;
      for (const obj of Object.values(raw)) {
        const m = normalizeMovie(obj);
        const key = makeKey(m.title);
        
        // Skip movies with invalid titles
        if (!m.title || m.title.trim() === '' || m.title === 'Untitled') {
          skippedCount++;
          console.log(`⚠️ Skipped movie with invalid title:`, obj);
          continue;
        }
        
        // Image data is now included in the main profile file
        if (m.director && m.director.toLowerCase().includes('almodovar')) {
          console.log(`✅ Loaded Pedro Almodóvar movie: ${m.title}:`, {
            poster: m.poster_url, 
            backdrop: m.backdrop_url,
            director: m.director,
            year: m.year
          });
        }
        
        if (!merged.has(key)) {
          merged.set(key, m);
        } else {
          merged.set(key, mergeMovies(merged.get(key), m));
        }
        processedCount++;
      }
      console.log(`📁 Processed ${processedCount} movies, skipped ${skippedCount} from ${path}`);
    } catch (e) {
      // Don't fail the whole load because one file is missing/unavailable
      errors.push(`${path}: ${e.message}`);
      console.warn('Failed to load', path, e);
    }
  }

  state.data = Array.from(merged.values()).sort((a, b) => a.title.localeCompare(b.title));
  
  // Debug: log data loading statistics
  console.log(`📊 Data Loading Stats:`, {
    rawDataCount: Object.keys(merged).length,
    finalDataCount: state.data.length,
    mergedKeysCount: merged.size,
    arrayFromMergedCount: Array.from(merged.values()).length
  });
  
  console.log('🔍 Data loaded successfully! Total movies:', state.data.length);
  
  // Debug: log Pedro Almodóvar movies count
  const almodovarMovies = state.data.filter(m => m.director && m.director.toLowerCase().includes('almodovar'));
  console.log(`🎬 Loaded ${state.data.length} total movies, ${almodovarMovies.length} Pedro Almodóvar movies:`, 
    almodovarMovies.map(m => m.title));
  
  // Debug: log first movie to see structure
  if (state.data.length > 0) {
    console.log('First movie structure:', state.data[0]);
    console.log('First movie emotional_tone:', state.data[0].emotional_tone);
    console.log('First movie themes:', state.data[0].themes);
  }

  // Build filter chips from the merged data
  const tones = new Set();
  const themes = new Set();
  for (const m of state.data) {
    // Handle both old and new structures
    if (m.emotional_tone && Array.isArray(m.emotional_tone)) {
      // Old structure: array of tones
      m.emotional_tone.forEach(t => tones.add(t));
    } else {
      // New structure: primary/secondary tones
      if (m.primary_emotional_tone) {
        const formatted = formatEmotionalTone(m.primary_emotional_tone);
        if (formatted) tones.add(formatted);
      }
      if (m.secondary_emotional_tone && m.secondary_emotional_tone !== 'none') {
        const formatted = formatEmotionalTone(m.secondary_emotional_tone);
        if (formatted) tones.add(formatted);
      }
    }
    
    if (m.themes && Array.isArray(m.themes)) {
      // Old structure: array of themes
      m.themes.forEach(t => themes.add(t));
    } else {
      // New structure: primary/secondary themes
      if (m.primary_theme) themes.add(formatTheme(m.primary_theme));
      if (m.secondary_theme && m.secondary_theme !== 'none') themes.add(formatTheme(m.secondary_theme));
    }
  }
  renderChips(els.toneFilters, [...tones].sort(), state.filterTones);
  renderChips(els.themeFilters, [...themes].sort(), state.filterThemes);

  els.searchInput.value = '';
  state.search = '';
  state.filterTones.clear();
  state.filterThemes.clear();
  state.page = 1;

  updateClearButtonVisibility();
  render();

  if (errors.length) {
    console.info('Some sources failed to load:', errors.join(' | '));
  }
}

// Convert underscore-separated theme names to human-readable format
function formatTheme(theme) {
  if (!theme || theme === 'none') return null;
  return theme
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Clean and validate emotional tones - filter out theme-like values
function formatEmotionalTone(tone) {
  if (!tone || tone === 'none') return null;
  
  // List of valid emotional tones (add more as needed)
  const validTones = new Set([
    'dramatic', 'dark', 'romantic', 'contemplative', 'melancholic', 'tense', 
    'uplifting', 'comedic', 'intense', 'mysterious', 'suspenseful', 'thrilling',
    'heartwarming', 'poignant', 'nostalgic', 'reflective', 'energetic', 'epic',
    'heroic', 'inspirational', 'lighthearted', 'whimsical', 'surreal', 'mystical',
    'transformative', 'action-packed', 'adventurous', 'psychological', 'existential'
  ]);
  
  // If it's a valid tone, return it
  if (validTones.has(tone.toLowerCase())) {
    return tone.charAt(0).toUpperCase() + tone.slice(1);
  }
  
  // If it contains underscores, it's likely a theme - convert to readable format but mark as theme
  if (tone.includes('_')) {
    return null; // Don't include theme-like values in emotional tones
  }
  
  // For other values, capitalize and return
  return tone.charAt(0).toUpperCase() + tone.slice(1);
}

function normalizeMovie(obj) {
  // Helper function to convert TMDB paths to full URLs
  const convertTmdbPath = (path, size = 'w500') => {
    if (!path) return '';
    if (path.startsWith('http')) return path; // Already a full URL
    if (path.startsWith('/')) return `https://image.tmdb.org/t/p/${size}${path}`;
    return path;
  };

  return {
    title: String(obj.title || obj.Title || 'Untitled'),
    emotional_tone: [formatEmotionalTone(obj.primary_emotional_tone), formatEmotionalTone(obj.secondary_emotional_tone)].filter(t => t && t !== 'none'),
    themes: [formatTheme(obj.primary_theme), formatTheme(obj.secondary_theme)].filter(t => t && t !== 'none'),
    // Keep new structure fields for display
    primary_emotional_tone: obj.primary_emotional_tone,
    secondary_emotional_tone: obj.secondary_emotional_tone,
    primary_theme: obj.primary_theme,
    secondary_theme: obj.secondary_theme,
    intensity_level: obj.intensity_level,
    pacing_style: String(obj.pacing_style ?? ''),
    visual_aesthetic: String(obj.visual_aesthetic ?? ''),
    target_audience: String(obj.target_audience ?? ''),
    similar_films: toArray(obj.similar_films),
    cultural_context: toArray(obj.cultural_context),
    narrative_structure: String(obj.narrative_structure ?? ''),
    energy_level: String(obj.energy_level ?? ''),
    discussion_topics: toArray(obj.discussion_topics),
    card_description: String(obj.card_description ?? ''),
    profile_text: String(obj.profile_text ?? ''),
    plot_summary: String(obj.plot_summary ?? ''),
    director: String(obj.director ?? ''),
    year: String(obj.year ?? ''),
    // Handle both poster_url/poster_path and backdrop_url/backdrop_path
    backdrop_url: convertTmdbPath(obj.backdrop_url || obj.backdrop_path, 'w1280'),
    poster_url: convertTmdbPath(obj.poster_url || obj.poster_path, 'w500'),
  };
}

function mergeMovies(a, b) {
  // Merge arrays as unique unions
  const union = (arr1, arr2) => {
    const s = new Set([...(arr1 || []), ...(arr2 || [])].filter(Boolean).map(x => String(x)));
    return [...s];
  };
  // Prefer the longest non-empty string (heuristic for richer content)
  const pref = (x, y) => {
    const sx = String(x ?? '').trim();
    const sy = String(y ?? '').trim();
    if (!sx) return sy;
    if (!sy) return sx;
    return sy.length > sx.length ? sy : sx;
  };

  // Helper function to convert TMDB paths to full URLs (same as in normalizeMovie)
  const convertTmdbPath = (path, size = 'w500') => {
    if (!path) return '';
    if (path.startsWith('http')) return path; // Already a full URL
    if (path.startsWith('/')) return `https://image.tmdb.org/t/p/${size}${path}`;
    return path;
  };

  return {
    title: pref(a.title, b.title),
    emotional_tone: union(a.emotional_tone, b.emotional_tone),
    themes: union(a.themes, b.themes),
    pacing_style: pref(a.pacing_style, b.pacing_style),
    visual_aesthetic: pref(a.visual_aesthetic, b.visual_aesthetic),
    target_audience: pref(a.target_audience, b.target_audience),
    similar_films: union(a.similar_films, b.similar_films),
    cultural_context: union(a.cultural_context, b.cultural_context),
    narrative_structure: pref(a.narrative_structure, b.narrative_structure),
    energy_level: pref(a.energy_level, b.energy_level),
    discussion_topics: union(a.discussion_topics, b.discussion_topics),
    card_description: pref(a.card_description, b.card_description),
    profile_text: pref(a.profile_text, b.profile_text),
    plot_summary: pref(a.plot_summary, b.plot_summary),
    director: pref(a.director, b.director),
    year: pref(a.year, b.year),
    poster_url: convertTmdbPath(pref(a.poster_url, b.poster_url), 'w500'),
    backdrop_url: convertTmdbPath(pref(a.backdrop_url, b.backdrop_url), 'w1280'),
    // Preserve new structure fields
    primary_emotional_tone: pref(a.primary_emotional_tone, b.primary_emotional_tone),
    secondary_emotional_tone: pref(a.secondary_emotional_tone, b.secondary_emotional_tone),
    primary_theme: pref(a.primary_theme, b.primary_theme),
    secondary_theme: pref(a.secondary_theme, b.secondary_theme),
    intensity_level: pref(a.intensity_level, b.intensity_level),
  };
}

function makeKey(title) {
  return String(title || '')
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '') // strip diacritics
    .replace(/\s+/g, ' ')             // collapse spaces
    .trim();
}

function renderChips(container, items, setRef) {
  container.innerHTML = '';
  for (const label of items) {
    const chip = document.createElement('span');
    chip.className = 'chip';
    chip.textContent = label;
    chip.addEventListener('click', () => {
      if (setRef.has(label)) setRef.delete(label); else setRef.add(label);
      chip.classList.toggle('active');
      state.page = 1;
      render();
    });
    container.appendChild(chip);
  }
}

function syncThemeExampleButtons() {
  document.querySelectorAll('.theme-example-btn').forEach(btn => {
    const theme = btn.getAttribute('data-theme');
    if (state.filterThemes.has(theme)) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });
}

async function render() {
  const rawBase = (state.apiBase || els.apiBaseInput?.value || localStorage.getItem('apiBase') || '');
  const base = normalizeBase(rawBase);
  const useApi = !!base && !!state.search;
  if (useApi) {
    await renderUsingApi(base);
  } else {
    renderLocal();
  }
  syncThemeExampleButtons();
  
  // Update favorites count to ensure it's displayed correctly after any render
  updateFavoritesCount();
}

function renderLocal() {
  console.log('🔍 renderLocal called with search term:', state.search);
  console.log('🔍 Total data available:', state.data.length);
  const filtered = applyFilters(state.data);
  const total = filtered.length;
  console.log('🔍 Filtered results:', total);

  // Pagination
  const pages = Math.max(1, Math.ceil(total / state.pageSize));
  if (state.page > pages) state.page = pages;
  const start = (state.page - 1) * state.pageSize;
  const slice = filtered.slice(start, start + state.pageSize);

  // Stats
  els.stats.textContent = `${total} result${total === 1 ? '' : 's'} | page ${state.page}/${pages} | dataset: merged profiles`;

  // Render featured theme hero, themed carousels and "All Movies" section (only on first page and when no search/filters are active)
  if (state.page === 1 && shouldRenderCarousels()) {
    renderFeaturedThemeHero();
    renderThemedCarousels();
    showAllMoviesSection();
  } else {
    // Hide featured theme hero, carousels and "All Movies" section when searching or filtering
    if (els.featuredThemeHero) {
      els.featuredThemeHero.innerHTML = '';
    }
    if (els.themedCarousels) {
      els.themedCarousels.innerHTML = '';
    }
    hideAllMoviesSection();
    
    // Show search results in the carousel area when searching
    if (state.search && els.themedCarousels) {
      console.log('🔍 Creating search results header for:', state.search, 'with', total, 'results');
      console.log('🔍 themedCarousels element:', els.themedCarousels);
      console.log('🔍 themedCarousels current content before setting:', els.themedCarousels.innerHTML);
      els.themedCarousels.innerHTML = `
        <div class="search-results-header">
          <h2>Search Results for "${state.search}"</h2>
          <p>Found ${total} result${total === 1 ? '' : 's'}</p>
        </div>
      `;
      console.log('🔍 Search results header created. Content after setting:', els.themedCarousels.innerHTML);
      
      // Add a safeguard to prevent carousels from overriding search results
      setTimeout(() => {
        if (state.search && els.themedCarousels && !els.themedCarousels.innerHTML.includes('search-results-header')) {
          console.log('🚨 WARNING: Search results were overridden! Re-creating...');
          els.themedCarousels.innerHTML = `
            <div class="search-results-header">
              <h2>Search Results for "${state.search}"</h2>
              <p>Found ${total} result${total === 1 ? '' : 's'}</p>
            </div>
          `;
        }
      }, 100);
    } else {
      console.log('🔍 Not creating search header. Search:', state.search, 'themedCarousels:', !!els.themedCarousels);
    }
  }

  // Cards
  els.cards.innerHTML = '';
  for (const movie of slice) {
    els.cards.appendChild(renderCard(movie));
  }
  
  console.log('🔍 Rendered', slice.length, 'cards in main cards container');
  
  // Enable horizontal scrolling for tags
  setTimeout(() => {
    console.log('Enabling horizontal tag scrolling for all cards');
    enableTagScrolling();
  }, 500);

  // Pagination controls
  renderPagination(pages);
}

async function renderUsingApi(base) {
  try {
    els.stats.textContent = 'Searching…';
    els.cards.innerHTML = '';
    els.pagination.innerHTML = '';
    const url = `${base}/search?q=${encodeURIComponent(state.search)}&limit=${state.pageSize}&mode=hybrid`;
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const data = await res.json();
    const results = data?.results || [];
    const applied = data?.applied_filters || {};
    const dbg = data?.debug || {};
    // Map results to local profiles by title if available
    const byKey = new Map(state.data.map(m => [makeKey(m.title), m]));
    
    // Debug: Log some local data keys for Pedro Almodóvar movies
    console.log('🔍 Local data keys for Pedro Almodóvar movies:', 
      Array.from(byKey.keys()).filter(key => key.includes('pain') || key.includes('glory') || key.includes('parallel') || key.includes('mothers'))
    );
    
    const movies = results.map(r => {
      const localKey = makeKey(r.title);
      const m = byKey.get(localKey) || normalizeMovie({ title: r.title });
      const clone = { ...m };
      
      // Debug logging for Pedro Almodóvar movies
      if (r.title && r.title.toLowerCase().includes('pain') && r.title.toLowerCase().includes('glory')) {
        console.log('🔍 Debugging Pain and Glory:', {
          title: r.title,
          foundInLocalData: !!byKey.get(makeKey(r.title)),
          originalBackdropUrl: m.backdrop_url,
          originalPosterUrl: m.poster_url,
          cloneBackdropUrl: clone.backdrop_url,
          clonePosterUrl: clone.poster_url
        });
      }
      
      // Prefer backend-provided explanation; fall back to composing from badges + snippet
      const badges = (r.badges || []).map(x => String(x));
      
      // Only set _why if there's no existing card_description or profile_text
      const hasExistingDescription = (clone.card_description && String(clone.card_description).trim()) || 
                                   (clone.profile_text && String(clone.profile_text).trim());
      
      if (!hasExistingDescription) {
        // Prefer prettified explanation if provided by backend
        if (r.why_pretty) {
          clone._why = String(r.why_pretty);
        } else if (r.why) {
          clone._why = String(r.why);
        } else {
          const whyParts = [];
          if (badges.length) whyParts.push(`Badges: ${badges.join(' • ')}`);
          if (r.snippet) whyParts.push(`Why: ${String(r.snippet)}`);
          // provenance if present
          const pv = [];
          if (r.debug?.kw_rank) pv.push(`kw#${r.debug.kw_rank}`);
          if (r.debug?.vec_rank) pv.push(`vec#${r.debug.vec_rank}`);
          if (pv.length) whyParts.push(`Via: ${pv.join(', ')}`);
          clone._why = whyParts.join(' — ');
        }
      }
      // Also surface badges among themes for visibility
      if (Array.isArray(clone.themes)) {
        clone.themes = [...new Set([...(badges), ...clone.themes])];
      }
      return clone;
    });

    const semTxt = (dbg && typeof dbg.semantic_enabled !== 'undefined') ? (dbg.semantic_enabled ? ' | semantic: on' : ' | semantic: off') : '';
    els.stats.textContent = `${results.length} result${results.length === 1 ? '' : 's'} | via API${semTxt}` + (Object.keys(applied).length ? ` | filters: ${JSON.stringify(applied)}` : '');
    
    // Hide carousels and "All Movies" section when searching via API
    if (els.themedCarousels) {
      els.themedCarousels.innerHTML = '';
    }
    hideAllMoviesSection();
    
    // Show search results in the carousel area when searching via API
    if (state.search && els.themedCarousels) {
      console.log('🔍 Creating search results header for API search:', state.search, 'with', results.length, 'results');
      els.themedCarousels.innerHTML = `
        <div class="search-results-header">
          <h2>Search Results for "${state.search}"</h2>
          <p>Found ${results.length} result${results.length === 1 ? '' : 's'}</p>
        </div>
      `;
    }
    
    els.cards.innerHTML = '';
    for (const m of movies) {
      els.cards.appendChild(renderCard(m));
    }
    
    // Enable horizontal scrolling for tags
    setTimeout(() => {
      console.log('Enabling horizontal tag scrolling for API cards');
      enableTagScrolling();
    }, 500);
    // No pagination for API mode (server already limited)
    els.pagination.innerHTML = '';
  } catch (e) {
    if (els.apiStatus) els.apiStatus.textContent = `Search failed, falling back to local: ${e.message}`;
    // Fallback to local render
    renderLocal();
  }
}

function renderCard(m) {
  const node = els.cardTpl.content.firstElementChild.cloneNode(true);
  node.querySelector('.title').textContent = m.title;
  
  // Set backdrop image if available, fallback to poster if no backdrop
  const backdropImage = node.querySelector('.backdrop-image');
  if (backdropImage) {
    if (m.backdrop_url) {
      backdropImage.style.backgroundImage = `url(${m.backdrop_url})`;
      backdropImage.style.backgroundSize = 'cover';
      backdropImage.style.backgroundPosition = 'center';
      console.log(`🎬 Set backdrop for ${m.title}:`, m.backdrop_url);
    } else if (m.poster_url) {
      backdropImage.style.backgroundImage = `url(${m.poster_url})`;
      backdropImage.style.backgroundSize = 'cover';
      backdropImage.style.backgroundPosition = 'center';
      console.log(`🎬 Set poster fallback for ${m.title}:`, m.poster_url);
    } else {
      console.log(`❌ No images available for ${m.title}`);
    }
  }
  
  // Set director and year in the dedicated subtitle element
  const subtitleElement = node.querySelector('.movie-subtitle');
  const directorYear = [];
  if (m.director) directorYear.push(m.director);
  if (m.year) directorYear.push(m.year);
  
  if (subtitleElement) {
    if (directorYear.length > 0) {
      subtitleElement.textContent = directorYear.join(' • ');
    } else {
      subtitleElement.textContent = '';
    }
  }
  
  // Profile preview: show full card description (fallback to profile text, then _why)
  const previewSrc = (m.card_description && String(m.card_description).trim()) || (m.profile_text && String(m.profile_text).trim()) || (m._why && String(m._why).trim()) || '';
  const preview = previewSrc; // Show full length without truncation
  setField(node, 'why', preview);
  setField(node, 'pacing_style', m.pacing_style);
  setField(node, 'energy_level', m.energy_level);
  // Still set fields for potential use (even if hidden in card)
  setField(node, 'visual_aesthetic', m.visual_aesthetic);
  setField(node, 'target_audience', m.target_audience);
  setField(node, 'narrative_structure', m.narrative_structure);
  setField(node, 'profile_text', m.profile_text);
  setList(node, 'emotional_tone', m.emotional_tone, 'tag');
  setList(node, 'themes', m.themes, 'tag');
  setList(node, 'similar_films', m.similar_films, 'tag');
  setList(node, 'cultural_context', m.cultural_context, 'li');
  setList(node, 'discussion_topics', m.discussion_topics, 'li');
  // Remove the More button
  const moreBtn = node.querySelector('.more-btn');
  if (moreBtn) {
    moreBtn.remove();
  }
  
  // Add click handler to the entire card to open movie details panel
  node.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    showMovieDetailsPanel(m);
  });
  
  // Add cursor pointer style
  node.style.cursor = 'pointer';
  
  return node;
}

function renderPagination(pages) {
  const nav = els.pagination;
  nav.innerHTML = '';
  const mkBtn = (label, page, disabled = false, active = false) => {
    const b = document.createElement('button');
    b.textContent = label;
    if (disabled) b.disabled = true;
    if (active) b.classList.add('active');
    b.addEventListener('click', () => { state.page = page; render(); });
    return b;
  };

  nav.appendChild(mkBtn('⟨ Prev', Math.max(1, state.page - 1), state.page === 1));

  const maxButtons = 7; // show limited page numbers
  const start = Math.max(1, state.page - Math.floor(maxButtons / 2));
  const end = Math.min(pages, start + maxButtons - 1);
  const realStart = Math.max(1, end - maxButtons + 1);
  for (let p = realStart; p <= end; p++) {
    nav.appendChild(mkBtn(String(p), p, false, p === state.page));
  }

  nav.appendChild(mkBtn('Next ⟩', Math.min(pages, state.page + 1), state.page === pages));
}

function applyFilters(arr) {
  const q = state.search;
  const toneSet = state.filterTones;
  const themeSet = state.filterThemes;

  console.log('🔍 applyFilters called with search term:', q);

  return arr.filter(m => {
    // Search
    if (q) {
      const hay = [
        m.title,
        m.pacing_style,
        m.energy_level,
        m.visual_aesthetic,
        m.target_audience,
        m.narrative_structure,
        m.profile_text,
        ...m.emotional_tone,
        ...m.themes,
        ...m.similar_films,
        ...m.cultural_context,
        ...m.discussion_topics,
      ].join(' ').toLowerCase();
      
      const matches = hay.includes(q);
      if (matches) {
        console.log('🔍 Found match for:', m.title, 'with search term:', q);
      }
      if (!matches) return false;
    }

    // Tone filter: require all selected tones (AND)
    if (toneSet.size) {
      for (const t of toneSet) if (!m.emotional_tone.includes(t)) return false;
    }

    // Theme filter: require all selected themes (AND)
    if (themeSet.size) {
      for (const t of themeSet) if (!m.themes.includes(t)) return false;
    }

    return true;
  });
}

function setField(node, field, value) {
  const el = node.querySelector(`[data-field="${field}"]`);
  if (el) el.textContent = value || '';
}
function setList(node, field, items, kind) {
  const elements = node.querySelectorAll(`[data-list="${field}"]`);
  if (elements.length === 0) return;
  
  // Set the same content on all matching elements
  for (const el of elements) {
    el.innerHTML = '';
    for (const item of items || []) {
      if (!item) continue;
      if (kind === 'li') {
        const li = document.createElement('li');
        li.textContent = item;
        if (el.tagName !== 'UL' && el.classList.contains('bullets')) {
          const ul = document.createElement('ul');
          ul.appendChild(li);
          el.appendChild(ul);
        } else {
          el.appendChild(li);
        }
      } else {
        const span = document.createElement('span');
        span.className = 'tag';
        // Capitalize the first letter of the tag
        span.textContent = item.charAt(0).toUpperCase() + item.slice(1);
        el.appendChild(span);
      }
    }
  }
  
  // Handle smart tag overflow for the main tag row
  if (field === 'emotional_tone' || field === 'themes') {
    console.log(`Setting up tag overflow for field: ${field}`);
    setTimeout(() => {
      console.log('Calling handleTagOverflow after timeout');
      handleTagOverflow(node);
    }, 200);
  }
}

function toArray(v) {
  if (!v) return [];
  if (Array.isArray(v)) return v.filter(Boolean).map(x => String(x));
  return [String(v)];
}

// Handle smart tag overflow for single-row layout
function handleTagOverflow(cardNode) {
  const tagRow = cardNode.querySelector('.tags-row');
  if (!tagRow) {
    console.log('No tag row found');
    return;
  }
  
  const tags = tagRow.querySelectorAll('.tag');
  if (tags.length === 0) {
    console.log('No tags found');
    return;
  }
  
  console.log(`Handling tag overflow for ${tags.length} tags`);
  
  // Ensure tags are rendered and have dimensions
  if (tags[0].offsetWidth === 0) {
    // Tags not yet rendered, retry after a short delay
    setTimeout(() => handleTagOverflow(cardNode), 50);
    return;
  }
  
  // Remove any existing "more" indicator
  const existingMore = tagRow.querySelector('.tag-more');
  if (existingMore) existingMore.remove();
  
  // Reset all tags to visible
  tags.forEach(tag => {
    tag.classList.remove('hidden');
    tag.style.display = '';
  });
  
  // Check if tags overflow by measuring actual content
  const containerWidth = tagRow.offsetWidth;
  let totalContentWidth = 0;
  
  // Calculate total width of all tags
  tags.forEach((tag, index) => {
    const tagWidth = tag.offsetWidth;
    const gap = index > 0 ? 4 : 0; // CSS gap
    totalContentWidth += tagWidth + gap;
  });
  
  console.log(`Container width: ${containerWidth}, Content width: ${totalContentWidth}`);
  
  if (totalContentWidth <= containerWidth) {
    console.log('No overflow detected');
    return; // No overflow, all tags fit
  }
  
  // Calculate how many tags we can fit with "+X more" indicator
  let visibleCount = 0;
  let totalWidth = 0;
  const gap = 4; // CSS gap value
  const moreIndicatorWidth = 80; // Reserve space for "+X more" indicator
  
  for (let i = 0; i < tags.length; i++) {
    const tag = tags[i];
    const tagWidth = tag.offsetWidth;
    const currentGap = i > 0 ? gap : 0;
    
    // Check if adding this tag would exceed container width (reserving space for "+X more")
    if (totalWidth + tagWidth + currentGap + moreIndicatorWidth > containerWidth) {
      break;
    }
    
    totalWidth += tagWidth + currentGap;
    visibleCount++;
  }
  
  // Hide overflow tags
  const hiddenCount = tags.length - visibleCount;
  console.log(`Visible count: ${visibleCount}, Hidden count: ${hiddenCount}`);
  
  if (hiddenCount > 0) {
    console.log('Hiding overflow tags and adding +X more indicator');
    for (let i = visibleCount; i < tags.length; i++) {
      tags[i].classList.add('hidden');
    }
    
    // Add "+X more" indicator
    const moreIndicator = document.createElement('span');
    moreIndicator.className = 'tag-more';
    moreIndicator.textContent = `+${hiddenCount} more`;
    moreIndicator.title = `Show ${hiddenCount} more tags`;
    moreIndicator.style.cursor = 'pointer';
    console.log('Created +X more indicator:', moreIndicator.textContent);
    
    // Add click handler to temporarily show all tags
    moreIndicator.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleAllTags(tagRow, tags, hiddenCount);
    });
    
    tagRow.appendChild(moreIndicator);
  }
}

// Toggle between showing all tags and the compact view
function toggleAllTags(tagRow, tags, hiddenCount) {
  const moreIndicator = tagRow.querySelector('.tag-more');
  const isExpanded = moreIndicator && moreIndicator.textContent.includes('less');
  
  if (isExpanded) {
    // Collapse back to compact view
    handleTagOverflow(tagRow.closest('.card'));
  } else {
    // Show all tags
    tags.forEach(tag => {
      tag.classList.remove('hidden');
      tag.style.display = '';
    });
    
    if (moreIndicator) {
      moreIndicator.textContent = 'less';
      moreIndicator.title = 'Show fewer tags';
    }
  }
}

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

// ===== Favorites integration =====
state.liked = new Set(JSON.parse(localStorage.getItem('likedTitles') || '[]'));

// Favorites panel functions
function showFavoritesPanel() {
  console.log('🎬 showFavoritesPanel called');
  console.log('🎬 els.favoritesPanel:', els.favoritesPanel);
  if (els.favoritesPanel) {
    els.favoritesPanel.classList.remove('hidden');
    renderFavorites();
    
    // Reset scroll position to top when showing favorites panel
    els.favoritesPanel.scrollTop = 0;
    
    console.log('🎬 Favorites panel shown');
  } else {
    console.error('🎬 Favorites panel element not found!');
  }
}

function hideFavoritesPanel() {
  if (els.favoritesPanel) {
    els.favoritesPanel.classList.add('hidden');
  }
}

// Movie Details Panel functions
function showMovieDetailsPanel(movie) {
  console.log('🎬 showMovieDetailsPanel called for:', movie.title);
  
  if (!els.movieDetailsPanel) {
    console.error('🎬 Movie details panel element not found!');
    return;
  }
  
  // Update panel title
  if (els.movieDetailsTitle) {
    els.movieDetailsTitle.textContent = movie.title;
  }
  
  // Render movie details content
  renderMovieDetails(movie);
  
  // Show the panel
  els.movieDetailsPanel.classList.remove('hidden');
  
  // Reset scroll position to top when showing a new movie
  if (els.movieDetailsPanel) {
    els.movieDetailsPanel.scrollTop = 0;
  }
  
  console.log('🎬 Movie details panel shown');
}

function hideMovieDetailsPanel() {
  if (els.movieDetailsPanel) {
    els.movieDetailsPanel.classList.add('hidden');
  }
}

function renderMovieDetails(movie) {
  if (!els.movieDetailsContent) {
    console.error('🎬 Movie details content element not found!');
    return;
  }
  
  // Debug logging for plot summary
  console.log('🎬 renderMovieDetails called for:', movie.title);
  console.log('🎬 plot_summary field exists:', 'plot_summary' in movie);
  console.log('🎬 plot_summary has content:', !!movie.plot_summary);
  console.log('🎬 plot_summary value:', movie.plot_summary || 'Empty or missing');
  console.log('🎬 plot_summary length:', movie.plot_summary ? movie.plot_summary.length : 0);
  
  // Get backdrop images (all background shots)
  const backdrops = movie.backdrop_urls || [];
  if (movie.backdrop_url && !backdrops.includes(movie.backdrop_url)) {
    backdrops.unshift(movie.backdrop_url);
  }
  
  // Get themes and emotional tones
  const themes = movie.themes || [];
  const emotionalTones = movie.emotional_tone || [];
  
  // Create the HTML content
  const content = `
    <div class="movie-details-hero">
      <h2 class="movie-details-title">${movie.title}</h2>
      <div class="movie-details-subtitle">
        ${movie.director || ''}${movie.year ? ` • ${movie.year}` : ''}${movie.release_year && movie.year !== movie.release_year ? ` • ${movie.release_year}` : ''}
      </div>
    </div>
    
    ${backdrops.length > 0 ? `
    <div class="movie-details-backdrops">
      <div class="movie-details-backdrop-full">
        ${backdrops.map(backdrop => `
          <div class="movie-details-backdrop-item" style="background-image: url('${backdrop}')"></div>
        `).join('')}
      </div>
    </div>
    ` : ''}
    
    <div class="movie-details-info">
      ${movie.plot_summary ? `
      <div class="movie-details-plot">
        <div class="movie-details-meta-label">Plot Summary</div>
        <div class="movie-details-plot-text">${movie.plot_summary}</div>
      </div>
      <div class="movie-details-divider"></div>
      ` : ''}
      
      <div class="movie-details-profile">
        ${movie.profile_text || 'No profile available.'}
      </div>
      
      <div class="movie-details-meta">
        ${themes.length > 0 ? `
        <div class="movie-details-divider"></div>
        <div class="movie-details-meta-item">
          <div class="movie-details-meta-label">Key Themes</div>
          <ul class="movie-details-bullets">
            ${themes.map(theme => `<li>${theme.charAt(0).toUpperCase() + theme.slice(1).toLowerCase()}</li>`).join('')}
          </ul>
        </div>
        <div class="movie-details-divider"></div>
        ` : ''}
        
        ${emotionalTones.length > 0 ? `
        <div class="movie-details-meta-item">
          <div class="movie-details-meta-label">Emotional Tone</div>
          <ul class="movie-details-bullets">
            ${emotionalTones.map(tone => `<li>${tone.charAt(0).toUpperCase() + tone.slice(1).toLowerCase()}</li>`).join('')}
          </ul>
        </div>
        <div class="movie-details-divider"></div>
        ` : ''}
        
        ${movie.why ? `
        <div class="movie-details-meta-item">
          <div class="movie-details-meta-label">Why Watch</div>
          <ul class="movie-details-bullets">
            <li>${movie.why.charAt(0).toUpperCase() + movie.why.slice(1).toLowerCase()}</li>
          </ul>
        </div>
        <div class="movie-details-divider"></div>
        ` : ''}
        
        ${movie.narrative_structure ? `
        <div class="movie-details-meta-item">
          <div class="movie-details-meta-label">Narrative Structure</div>
          <ul class="movie-details-bullets">
            <li>${movie.narrative_structure.charAt(0).toUpperCase() + movie.narrative_structure.slice(1).toLowerCase()}</li>
          </ul>
        </div>
        <div class="movie-details-divider"></div>
        ` : ''}
        
        ${movie.cultural_context && movie.cultural_context.length > 0 ? `
        <div class="movie-details-meta-item">
          <div class="movie-details-meta-label">Cultural Context</div>
          <ul class="movie-details-bullets">
            ${movie.cultural_context.map(item => `<li>${item.charAt(0).toUpperCase() + item.slice(1).toLowerCase()}</li>`).join('')}
          </ul>
        </div>
        <div class="movie-details-divider"></div>
        ` : ''}
        
        ${movie.discussion_topics && movie.discussion_topics.length > 0 ? `
        <div class="movie-details-meta-item">
          <div class="movie-details-meta-label">Discussion Topics</div>
          <ul class="movie-details-bullets">
            ${movie.discussion_topics.map(topic => `<li>${topic.charAt(0).toUpperCase() + topic.slice(1).toLowerCase()}</li>`).join('')}
          </ul>
        </div>
        ` : ''}
      </div>
    </div>
  `;
  
  els.movieDetailsContent.innerHTML = content;
  console.log('🎬 Movie details rendered for:', movie.title);
  console.log('🎬 Generated HTML contains plot_summary:', content.includes('Plot Summary'));
  console.log('🎬 Full HTML preview:', content.substring(0, 500) + '...');
}

function updateFavoritesCount() {
  console.log('🎬 updateFavoritesCount called, liked size:', state.liked.size);
  console.log('🎬 els.favoritesCount:', els.favoritesCount);
  if (els.favoritesCount) {
    els.favoritesCount.textContent = state.liked.size;
    console.log('🎬 Updated favorites count badge to:', state.liked.size);
  } else {
    console.error('🎬 Favorites count element not found!');
  }
}

function renderFavorites() {
  if (!els.favoritesContent) return;
  
  const likedTitles = [...state.liked];
  
  if (likedTitles.length === 0) {
    els.favoritesContent.innerHTML = `
      <div class="favorites-empty">
        <div class="favorites-empty-icon">♡</div>
        <h4>No favorites yet</h4>
        <p>Like movies by clicking the ♡ button on movie cards to add them to your favorites.</p>
      </div>
    `;
    return;
  }
  
  // Get movie data for liked titles
  const moviesByTitle = new Map(state.data.map(m => [m.title, m]));
  const favoriteMovies = likedTitles
    .map(title => moviesByTitle.get(title))
    .filter(Boolean);
  
  els.favoritesContent.innerHTML = `
    <div class="favorites-list">
      ${favoriteMovies.map(movie => `
        <div class="favorite-item">
          <div class="favorite-poster" style="background-image: url(${movie.poster_url || ''})"></div>
          <div class="favorite-info">
            <h4 class="favorite-title">${escapeHtml(movie.title)}</h4>
            <div class="favorite-meta">${escapeHtml(movie.director || '')}${movie.year ? ` • ${movie.year}` : ''}</div>
            <div class="favorite-themes">
              ${(movie.themes || []).slice(0, 3).map(theme => 
                `<span class="tag">${escapeHtml(theme)}</span>`
              ).join('')}
            </div>
          </div>
          <button class="favorite-remove" onclick="removeFromFavorites('${escapeHtml(movie.title)}')" title="Remove from favorites">✕</button>
        </div>
      `).join('')}
    </div>
  `;
}

function removeFromFavorites(title) {
  state.liked.delete(title);
  saveLikes();
  updateFavoritesCount();
  renderFavorites();
  // Update the like button state in the main cards
  updateLikeButtons();
}

// Make removeFromFavorites globally accessible
window.removeFromFavorites = removeFromFavorites;

// Observability panel functions
function showObsPanel() {
  if (els.obsPanel) {
    els.obsPanel.classList.remove('hidden');
  }
}

function hideObsPanel() {
  if (els.obsPanel) {
    els.obsPanel.classList.add('hidden');
  }
}

function updateLikeButtons() {
  document.querySelectorAll('.like-btn').forEach(btn => {
    const card = btn.closest('.card');
    const titleElement = card.querySelector('.title');
    if (titleElement) {
      const title = titleElement.textContent;
      const isPressed = state.liked.has(title);
      btn.setAttribute('aria-pressed', String(isPressed));
      btn.textContent = isPressed ? '♥ Liked' : '♡ Like';
    }
  });
}

async function apiFetch(path, options = {}) {
  const candidates = [];
  // Allow manual override via global or localStorage
  try { if (window.API_BASE) candidates.push(String(window.API_BASE).replace(/\/$/, '')); } catch {}
  try {
    const lsBase = localStorage.getItem('apiBase');
    if (lsBase) candidates.push(String(lsBase).replace(/\/$/, ''));
  } catch {}
  // Same-origin if served over http(s)
  if (location.protocol === 'http:' || location.protocol === 'https:') {
    candidates.push(location.origin);
  }
  // Localhost fallbacks (try both localhost and 127.0.0.1)
  candidates.push('http://localhost:8001');
  candidates.push('https://localhost:8001');
  candidates.push('http://127.0.0.1:8003');
  candidates.push('https://127.0.0.1:8003');

  const errors = [];
  for (const base of candidates) {
    try {
      const res = await fetch(`${base}${path}`, options);
      if (res.ok) {
        try { localStorage.setItem('apiBase', base); } catch {}
        return res;
      }
      // Non-2xx: record and try next candidate
      errors.push(`${base}: ${res.status} ${res.statusText}`);
      // try next
    } catch (err) {
      errors.push(`${base}: ${err?.message || err}`);
      // try next candidate
    }
  }
  throw new Error('All API endpoints failed: ' + errors.join(' | '));
}


// Utility: persist likes
function saveLikes() {
  localStorage.setItem('likedTitles', JSON.stringify([...state.liked]));
}

// Add like/similar wiring when rendering cards
const _renderCardOrig = renderCard;
renderCard = function(m) {
  const node = _renderCardOrig(m);
  const likeBtn = node.querySelector('.like-btn');
  const similarBtn = node.querySelector('.similar-btn');
  if (likeBtn) {
    const pressed = state.liked.has(m.title);
    likeBtn.setAttribute('aria-pressed', String(pressed));
    likeBtn.textContent = pressed ? '♥ Liked' : '♡ Like';
    likeBtn.addEventListener('click', () => {
      console.log('🎬 Like button clicked for:', m.title);
      if (state.liked.has(m.title)) {
        state.liked.delete(m.title);
        console.log('🎬 Removed from favorites:', m.title);
      } else {
        state.liked.add(m.title);
        console.log('🎬 Added to favorites:', m.title);
      }
      saveLikes();
      const isPressed = state.liked.has(m.title);
      likeBtn.setAttribute('aria-pressed', String(isPressed));
      likeBtn.textContent = isPressed ? '♥ Liked' : '♡ Like';
      // Update favorites count and panel
      updateFavoritesCount();
      console.log('🎬 Updated favorites count:', state.liked.size);
      // If favorites panel is open, re-render it
      if (els.favoritesPanel && !els.favoritesPanel.classList.contains('hidden')) {
        renderFavorites();
      }
    });
  }
  if (similarBtn) {
    similarBtn.addEventListener('click', () => {
      // For now, just show the movie details modal
      openModal(m);
    });
  }
  return node;
}



// Initialize favorites after dataset load
const _loadAllSources = loadAllSources;
loadAllSources = async function(...args) {
  await _loadAllSources(...args);
  console.log('🎬 Data loaded, initializing favorites...');
  updateFavoritesCount();
  console.log('🎬 Initial favorites count set');
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  })[c] || c);
}


// --- Modal and utilities ---
function truncate(str, max) {
  const s = String(str || '').trim();
  if (s.length <= max) return s;
  return s.slice(0, max - 1).trimEnd() + '…';
}

function openModal(m) {
  if (!els.modalOverlay || !els.modalBody || !els.modalTitle) return;
  
  // Debug logging for Pedro Almodóvar movies
  if (m.title && m.title.toLowerCase().includes('pain') && m.title.toLowerCase().includes('glory')) {
    console.log('🔍 Debugging modal for Pain and Glory:', {
      title: m.title,
      director: m.director,
      year: m.year,
      emotional_tone: m.emotional_tone,
      themes: m.themes,
      pacing_style: m.pacing_style,
      energy_level: m.energy_level,
      cultural_context: m.cultural_context,
      discussion_topics: m.discussion_topics,
      profile_text: m.profile_text ? m.profile_text.substring(0, 100) + '...' : null,
      similar_films: m.similar_films
    });
  }
  
  // Build content
  buildModalContent(m);
  els.modalTitle.textContent = m.title || 'Movie';
  els.modalOverlay.classList.add('open');
  els.modalOverlay.setAttribute('aria-hidden', 'false');
  document.documentElement.style.overflow = 'hidden';
}

function closeModal() {
  if (!els.modalOverlay) return;
  els.modalOverlay.classList.remove('open');
  els.modalOverlay.setAttribute('aria-hidden', 'true');
  document.documentElement.style.overflow = '';
}

function buildModalContent(m) {
  const body = els.modalBody;
  body.innerHTML = '';

  // Sections: Tags (mixed), Meta (pacing/energy), Visual/Target, Narrative, Cultural, Discussion, Profile, Similar films
  const mkSection = (title) => {
    const s = document.createElement('section');
    s.className = 'section';
    const h = document.createElement('h4');
    h.textContent = title;
    s.appendChild(h);
    return s;
  };

  // Add director and year info at the top
  if (m.director || m.year) {
    const infoSec = mkSection('Movie Info');
    const info = document.createElement('div');
    info.className = 'meta';
    const infoItems = [];
    if (m.director) infoItems.push(`Director: ${m.director}`);
    if (m.year) infoItems.push(`Year: ${m.year}`);
    info.textContent = infoItems.join(' • ');
    infoSec.appendChild(info);
    body.appendChild(infoSec);
  }

  // Mixed tags
  const tagsSec = mkSection('Tags');
  const tagsWrap = document.createElement('div');
  tagsWrap.className = 'tags';
  const addTag = (t) => { const span = document.createElement('span'); span.className = 'tag'; span.textContent = t.charAt(0).toUpperCase() + t.slice(1); tagsWrap.appendChild(span); };
  (m.emotional_tone || []).forEach(addTag);
  (m.themes || []).forEach(addTag);
  tagsSec.appendChild(tagsWrap);
  body.appendChild(tagsSec);

  // Meta
  const metaSec = mkSection('Meta');
  const meta = document.createElement('div');
  meta.className = 'meta';
  const metaItems = [];
  if (m.pacing_style) metaItems.push(`Pacing: ${m.pacing_style}`);
  if (m.energy_level) metaItems.push(`Energy: ${m.energy_level}`);
  if (m.visual_aesthetic) metaItems.push(`Visual: ${m.visual_aesthetic}`);
  if (m.target_audience) metaItems.push(`Audience: ${m.target_audience}`);
  if (m.narrative_structure) metaItems.push(`Narrative: ${m.narrative_structure}`);
  meta.textContent = metaItems.join(' • ');
  metaSec.appendChild(meta);
  body.appendChild(metaSec);

  // Cultural context
  if (m.cultural_context && m.cultural_context.length) {
    const cSec = mkSection('Cultural context');
    const ul = document.createElement('ul');
    for (const item of m.cultural_context) { const li = document.createElement('li'); li.textContent = item; ul.appendChild(li); }
    cSec.appendChild(ul);
    body.appendChild(cSec);
  }

  // Discussion topics
  if (m.discussion_topics && m.discussion_topics.length) {
    const dSec = mkSection('Discussion topics');
    const ul = document.createElement('ul');
    for (const item of m.discussion_topics) { const li = document.createElement('li'); li.textContent = item; ul.appendChild(li); }
    dSec.appendChild(ul);
    body.appendChild(dSec);
  }

  // Profile
  if (m.profile_text) {
    const pSec = mkSection('Profile');
    const p = document.createElement('p');
    p.textContent = m.profile_text;
    pSec.appendChild(p);
    body.appendChild(pSec);
  }

  // Similar films
  if (m.similar_films && m.similar_films.length) {
    const sSec = mkSection('Similar films');
    const wrap = document.createElement('div'); wrap.className = 'tags';
    for (const t of m.similar_films) { const span = document.createElement('span'); span.className = 'tag'; span.textContent = t.charAt(0).toUpperCase() + t.slice(1); wrap.appendChild(span); }
    sSec.appendChild(wrap);
    body.appendChild(sSec);
  }
}

// Admin status checking function
async function checkAdminStatus() {
  const token = localStorage.getItem('admin_token');
  const base = localStorage.getItem('admin_api_base') || normalizeBase(els.apiBaseInput?.value || localStorage.getItem('apiBase') || '');
  
  if (!token || !base) {
    if (els.adminStatus) els.adminStatus.textContent = 'Not logged in';
    return;
  }
  
  try {
    const response = await fetch(`${base}/admin/auth/status?token=${token}`);
    if (response.ok) {
      const status = await response.json();
      if (status.authenticated) {
        if (els.adminStatus) els.adminStatus.textContent = `Logged in as ${status.username}`;
        // Pre-fill username if available
        if (els.adminUsername && !els.adminUsername.value) {
          els.adminUsername.value = status.username;
        }
      } else {
        localStorage.removeItem('admin_token');
        if (els.adminStatus) els.adminStatus.textContent = 'Session expired';
      }
    } else {
      localStorage.removeItem('admin_token');
      if (els.adminStatus) els.adminStatus.textContent = 'Session invalid';
    }
  } catch (error) {
    if (els.adminStatus) els.adminStatus.textContent = 'Connection failed';
  }
}

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
  console.log('🚀 Initializing movie recommender app...');
  
  // Load themes from data
  await loadThemesFromData();
  
  console.log('🎭 THEMED_CAROUSELS after loading:', THEMED_CAROUSELS);
  console.log('📊 State data length:', state.data.length);
  
  // Re-render carousels with loaded themes (only if not searching)
  if (state.data.length > 0 && shouldRenderCarousels()) {
    console.log('🔄 Re-rendering carousels after theme loading...');
    renderThemedCarousels();
  } else if (state.search) {
    console.log('🔍 Skipping carousel re-render because search is active');
  } else {
    console.log('❌ No data available for carousels');
  }
  
  console.log('✅ App initialization complete');
  
  // Add responsive navigation functionality
  setupResponsiveNavigation();
});

// Responsive navigation functionality
function setupResponsiveNavigation() {
  const filters = document.querySelector('.filters');
  
  if (!filters) return;
  
  // Add click handler for theme toggle on mobile
  const handleThemeToggle = (e) => {
    // Check if we're on mobile and clicked on the theme toggle
    if (window.innerWidth <= 480) {
      const themeToggle = e.target.closest('.filters');
      if (themeToggle && e.target === themeToggle) {
        filters.classList.toggle('show-themes');
        e.preventDefault();
      }
    }
  };
  
  // Add click handler
  filters.addEventListener('click', handleThemeToggle);
  
  // Handle window resize to reset theme visibility
  const handleResize = () => {
    if (window.innerWidth > 480) {
      filters.classList.remove('show-themes');
    }
  };
  
  window.addEventListener('resize', handleResize);
  
  // Close theme dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 480 && 
        filters.classList.contains('show-themes') && 
        !filters.contains(e.target)) {
      filters.classList.remove('show-themes');
    }
  });
}
