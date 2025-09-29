#!/usr/bin/env python3

# Fix the image merging issue
with open('app.js', 'r') as f:
    content = f.read()

# Fix the merge logic to include image URLs
content = content.replace(
    '''        // Merge with original movie data if available
        const originalInfo = originalMovieData.get(key);
        if (originalInfo) {
          m.director = originalInfo.director;
          m.year = originalInfo.year;
        }''',
    '''        // Merge with original movie data if available
        const originalInfo = originalMovieData.get(key);
        if (originalInfo) {
          m.director = originalInfo.director;
          m.year = originalInfo.year;
          m.poster_url = originalInfo.poster_url;
          m.backdrop_url = originalInfo.backdrop_url;
        }'''
)

# Write back the fixed content
with open('app.js', 'w') as f:
    f.write(content)

print('✅ Fixed image merging issue:')
print('Now the frontend will properly merge poster_url and backdrop_url from the image data')
print('Refresh the page to see movie posters!')
