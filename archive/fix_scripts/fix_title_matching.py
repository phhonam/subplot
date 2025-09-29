#!/usr/bin/env python3

# Fix the title matching issue
with open('app.js', 'r') as f:
    content = f.read()

# Improve the makeKey function to handle quotes better
content = content.replace(
    '''function makeKey(title) {
  return String(title || '')
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '') // strip diacritics
    .replace(/\s+/g, ' ')             // collapse spaces
    .trim();
}''',
    '''function makeKey(title) {
  return String(title || '')
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '') // strip diacritics
    .replace(/[""''`]/g, '"')        // normalize quotes
    .replace(/\s+/g, ' ')             // collapse spaces
    .trim();
}'''
)

# Add debug logging to see what's happening with the merge
content = content.replace(
    '''        // Merge with original movie data if available
        const originalInfo = originalMovieData.get(key);
        if (originalInfo) {
          m.director = originalInfo.director;
          m.year = originalInfo.year;
          m.poster_url = originalInfo.poster_url;
          m.backdrop_url = originalInfo.backdrop_url;
        }''',
    '''        // Merge with original movie data if available
        const originalInfo = originalMovieData.get(key);
        if (originalInfo) {
          m.director = originalInfo.director;
          m.year = originalInfo.year;
          m.poster_url = originalInfo.poster_url;
          m.backdrop_url = originalInfo.backdrop_url;
          console.log(`Merged image data for ${m.title}:`, {poster: m.poster_url, backdrop: m.backdrop_url});
        } else {
          console.log(`No image data found for ${m.title} (key: ${key})`);
        }'''
)

# Write back the fixed content
with open('app.js', 'w') as f:
    f.write(content)

print('✅ Fixed title matching:')
print('1. Improved makeKey function to normalize quotes')
print('2. Added debug logging to see merge results')
print('3. Now refresh and check console for merge debug info')
