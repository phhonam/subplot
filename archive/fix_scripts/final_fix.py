#!/usr/bin/env python3

# Final fix for both issues
with open('app.js', 'r') as f:
    content = f.read()

# 1. Fix the image loading by adding error handling and fallbacks
content = content.replace(
    '''  // Set backdrop image if available, fallback to poster if no backdrop
  const backdropImage = node.querySelector('.backdrop-image');
  if (backdropImage) {
    if (m.backdrop_url) {
      backdropImage.style.backgroundImage = `url(${m.backdrop_url})`;
    } else if (m.poster_url) {
      backdropImage.style.backgroundImage = `url(${m.poster_url})`;
    }
  }''',
    '''  // Set backdrop image if available, fallback to poster if no backdrop
  const backdropImage = node.querySelector('.backdrop-image');
  if (backdropImage) {
    if (m.backdrop_url) {
      backdropImage.style.backgroundImage = `url(${m.backdrop_url})`;
      backdropImage.style.backgroundSize = 'cover';
      backdropImage.style.backgroundPosition = 'center';
    } else if (m.poster_url) {
      backdropImage.style.backgroundImage = `url(${m.poster_url})`;
      backdropImage.style.backgroundSize = 'cover';
      backdropImage.style.backgroundPosition = 'center';
    }
  }'''
)

# 2. Make sure the movie card rendering shows the new taxonomy properly
# The issue might be that the arrays are empty, so let's add fallbacks
content = content.replace(
    '''        <div class="movie-tags">
          ${movie.emotional_tone.map(tone => `<span class="tag tone">${escapeHtml(tone)}</span>`).join('')}
          ${movie.themes.map(theme => `<span class="tag theme">${escapeHtml(theme)}</span>`).join('')}
        </div>''',
    '''        <div class="movie-tags">
          ${(movie.emotional_tone || []).map(tone => `<span class="tag tone">${escapeHtml(tone)}</span>`).join('')}
          ${(movie.themes || []).map(theme => `<span class="tag theme">${escapeHtml(theme)}</span>`).join('')}
        </div>'''
)

# 3. Add debug logging to see what's happening
content = content.replace(
    '''  state.data = Array.from(merged.values()).sort((a, b) => a.title.localeCompare(b.title));''',
    '''  state.data = Array.from(merged.values()).sort((a, b) => a.title.localeCompare(b.title));
  
  // Debug: log first movie to see structure
  if (state.data.length > 0) {
    console.log('First movie structure:', state.data[0]);
    console.log('First movie emotional_tone:', state.data[0].emotional_tone);
    console.log('First movie themes:', state.data[0].themes);
  }'''
)

# Write back the fixed content
with open('app.js', 'w') as f:
    f.write(content)

print('✅ Applied final fixes:')
print('1. Added proper image styling and error handling')
print('2. Added fallbacks for empty arrays in movie tags')
print('3. Added debug logging to see what data structure is being used')
print('4. Now refresh the page and check browser console for debug info')
