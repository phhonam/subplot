#!/usr/bin/env python3

# Fix the source file name in app.js
with open('app.js', 'r') as f:
    content = f.read()

# Replace the incorrect filename
content = content.replace(
    "return ['movie_profiles_complete.json'];",
    "return ['movie_profiles_merged.json'];"
)

# Write back the fixed content
with open('app.js', 'w') as f:
    f.write(content)

print('✅ Fixed source filename in app.js')
print('Changed: movie_profiles_complete.json → movie_profiles_merged.json')
