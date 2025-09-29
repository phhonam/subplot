#!/usr/bin/env python3

# Fix both issues: missing images and filter categories
with open('app.js', 'r') as f:
    content = f.read()

# 1. Fix mergeMovies function to include image fields
content = content.replace(
    '''    profile_text: pref(a.profile_text, b.profile_text),
    director: pref(a.director, b.director),
    year: pref(a.year, b.year),
  };''',
    '''    profile_text: pref(a.profile_text, b.profile_text),
    director: pref(a.director, b.director),
    year: pref(a.year, b.year),
    poster_url: pref(a.poster_url, b.poster_url),
    backdrop_url: pref(a.backdrop_url, b.backdrop_url),
  };'''
)

# 2. Fix filter building to use the new taxonomy fields
# The current code is trying to access m.primary_emotional_tone but the data might not have these fields
# Let's make it more robust by checking both old and new structures
content = content.replace(
    '''  for (const m of state.data) {
    // Handle new structure: primary_emotional_tone, secondary_emotional_tone, primary_theme, secondary_theme
    if (m.primary_emotional_tone) tones.add(m.primary_emotional_tone);
    if (m.secondary_emotional_tone && m.secondary_emotional_tone !== 'none') tones.add(m.secondary_emotional_tone);
    if (m.primary_theme) themes.add(m.primary_theme);
    if (m.secondary_theme && m.secondary_theme !== 'none') themes.add(m.secondary_theme);
  }''',
    '''  for (const m of state.data) {
    // Handle both old and new structures
    if (m.emotional_tone && Array.isArray(m.emotional_tone)) {
      // Old structure: array of tones
      m.emotional_tone.forEach(t => tones.add(t));
    } else {
      // New structure: primary/secondary tones
      if (m.primary_emotional_tone) tones.add(m.primary_emotional_tone);
      if (m.secondary_emotional_tone && m.secondary_emotional_tone !== 'none') tones.add(m.secondary_emotional_tone);
    }
    
    if (m.themes && Array.isArray(m.themes)) {
      // Old structure: array of themes
      m.themes.forEach(t => themes.add(t));
    } else {
      // New structure: primary/secondary themes
      if (m.primary_theme) themes.add(m.primary_theme);
      if (m.secondary_theme && m.secondary_theme !== 'none') themes.add(m.secondary_theme);
    }
  }'''
)

# Write back the fixed content
with open('app.js', 'w') as f:
    f.write(content)

print('✅ Fixed both issues:')
print('1. Added poster_url and backdrop_url to mergeMovies function')
print('2. Made filter building work with both old and new data structures')
print('3. Now filters will show the new taxonomy categories')
