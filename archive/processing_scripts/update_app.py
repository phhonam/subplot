#!/usr/bin/env python3

import re

# Read the current app.js file
with open('app.js', 'r') as f:
    content = f.read()

# 1. Update normalizeMovie function to handle new structure
content = re.sub(
    r'emotional_tone: toArray\(obj\.emotional_tone\),\s*themes: toArray\(obj\.themes\),',
    '''emotional_tone: [obj.primary_emotional_tone, obj.secondary_emotional_tone].filter(t => t && t !== 'none'),
    themes: [obj.primary_theme, obj.secondary_theme].filter(t => t && t !== 'none'),''',
    content
)

# 2. Add card_description field to normalizeMovie
content = re.sub(
    r'profile_text: String\(obj\.profile_text \?\? \'\'\),',
    '''card_description: String(obj.card_description ?? ''),
    profile_text: String(obj.profile_text ?? ''),''',
    content
)

# 3. Update filter building logic
content = re.sub(
    r'for \(const m of state\.data\) \{\s*m\.emotional_tone\.forEach\(t => tones\.add\(t\)\);\s*m\.themes\.forEach\(t => themes\.add\(t\)\);\s*\}',
    '''for (const m of state.data) {
    // Handle new structure: primary_emotional_tone, secondary_emotional_tone, primary_theme, secondary_theme
    if (m.primary_emotional_tone) tones.add(m.primary_emotional_tone);
    if (m.secondary_emotional_tone && m.secondary_emotional_tone !== 'none') tones.add(m.secondary_emotional_tone);
    if (m.primary_theme) themes.add(m.primary_theme);
    if (m.secondary_theme && m.secondary_theme !== 'none') themes.add(m.secondary_theme);
  }''',
    content
)

# 4. Update mergeMovies function to include new fields
content = re.sub(
    r'profile_text: a\.profile_text \|\| b\.profile_text,',
    '''card_description: a.card_description || b.card_description,
    profile_text: a.profile_text || b.profile_text,
    // Keep new structure fields
    primary_emotional_tone: a.primary_emotional_tone || b.primary_emotional_tone,
    secondary_emotional_tone: a.secondary_emotional_tone || b.secondary_emotional_tone,
    primary_theme: a.primary_theme || b.primary_theme,
    secondary_theme: a.secondary_theme || b.secondary_theme''',
    content
)

# 5. Update movie card rendering to use card_description
content = re.sub(
    r'<p>\$\{escapeHtml\(movie\.plot\)\}</p>',
    r'<p>${escapeHtml(movie.card_description || movie.plot)}</p>',
    content
)

# 6. Update recommendation card description
content = re.sub(
    r'<div class="rec-description">\$\{escapeHtml\(p\.plot\)\}</div>',
    r'<div class="rec-description">${escapeHtml(p.card_description || p.plot)}</div>',
    content
)

# Write the updated content back to app.js
with open('app.js', 'w') as f:
    f.write(content)

print('✅ Updated app.js to work with new profile structure')
print('Changes made:')
print('- Updated normalizeMovie to convert new structure to arrays')
print('- Added card_description field support')
print('- Updated filter building for new taxonomy')
print('- Updated mergeMovies to handle new fields')
print('- Updated movie cards to use card_description')
