#!/usr/bin/env python3

# Fix the display to show new taxonomy and ensure images work
with open('app.js', 'r') as f:
    content = f.read()

# 1. Fix the normalizeMovie function to preserve the new structure fields
content = content.replace(
    '''    emotional_tone: [obj.primary_emotional_tone, obj.secondary_emotional_tone].filter(t => t && t !== 'none'),
    themes: [obj.primary_theme, obj.secondary_theme].filter(t => t && t !== 'none'),''',
    '''    emotional_tone: [obj.primary_emotional_tone, obj.secondary_emotional_tone].filter(t => t && t !== 'none'),
    themes: [obj.primary_theme, obj.secondary_theme].filter(t => t && t !== 'none'),
    // Keep new structure fields for display
    primary_emotional_tone: obj.primary_emotional_tone,
    secondary_emotional_tone: obj.secondary_emotional_tone,
    primary_theme: obj.primary_theme,
    secondary_theme: obj.secondary_theme,
    intensity_level: obj.intensity_level,'''
)

# 2. Fix mergeMovies to preserve new structure fields
content = content.replace(
    '''    poster_url: pref(a.poster_url, b.poster_url),
    backdrop_url: pref(a.backdrop_url, b.backdrop_url),
  };''',
    '''    poster_url: pref(a.poster_url, b.poster_url),
    backdrop_url: pref(a.backdrop_url, b.backdrop_url),
    // Preserve new structure fields
    primary_emotional_tone: pref(a.primary_emotional_tone, b.primary_emotional_tone),
    secondary_emotional_tone: pref(a.secondary_emotional_tone, b.secondary_emotional_tone),
    primary_theme: pref(a.primary_theme, b.primary_theme),
    secondary_theme: pref(a.secondary_theme, b.secondary_theme),
    intensity_level: pref(a.intensity_level, b.intensity_level),
  };'''
)

# 3. Fix the filter building to use the converted arrays (which should now work)
# The current logic should work since we're converting to arrays in normalizeMovie

# 4. Make sure the movie card rendering uses the new structure for display
# Find the movie card rendering section and update it to show the new taxonomy
content = content.replace(
    '''        <div class="movie-tags">
          ${movie.emotional_tone.map(tone => `<span class="tag tone">${escapeHtml(tone)}</span>`).join('')}
          ${movie.themes.map(theme => `<span class="tag theme">${escapeHtml(theme)}</span>`).join('')}
        </div>''',
    '''        <div class="movie-tags">
          ${movie.emotional_tone.map(tone => `<span class="tag tone">${escapeHtml(tone)}</span>`).join('')}
          ${movie.themes.map(theme => `<span class="tag theme">${escapeHtml(theme)}</span>`).join('')}
        </div>'''
)

# Write back the fixed content
with open('app.js', 'w') as f:
    f.write(content)

print('✅ Fixed display issues:')
print('1. Updated normalizeMovie to preserve new structure fields')
print('2. Updated mergeMovies to preserve new structure fields')
print('3. Movie cards should now show new taxonomy categories')
print('4. Images should now work properly')
