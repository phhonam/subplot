// PATCH for app.js - Update to work with new profile structure
// Replace the following sections in app.js:

// 1. Update normalizeMovie function (around line 246-259):
function normalizeMovie(obj) {
  return {
    title: String(obj.title || obj.Title || 'Untitled'),
    // Convert new structure back to arrays for frontend compatibility
    emotional_tone: [obj.primary_emotional_tone, obj.secondary_emotional_tone].filter(t => t && t !== 'none'),
    themes: [obj.primary_theme, obj.secondary_theme].filter(t => t && t !== 'none'),
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
    intensity_level: String(obj.intensity_level ?? ''),
    // Keep original fields for backward compatibility
    primary_emotional_tone: obj.primary_emotional_tone,
    secondary_emotional_tone: obj.secondary_emotional_tone,
    primary_theme: obj.primary_theme,
    secondary_theme: obj.secondary_theme
  };
}

// 2. Update filter building logic (around line 224-231):
// Replace the existing filter building code with:
const tones = new Set();
const themes = new Set();
for (const m of state.data) {
  // Handle new structure: primary_emotional_tone, secondary_emotional_tone, primary_theme, secondary_theme
  if (m.primary_emotional_tone) tones.add(m.primary_emotional_tone);
  if (m.secondary_emotional_tone && m.secondary_emotional_tone !== 'none') tones.add(m.secondary_emotional_tone);
  if (m.primary_theme) themes.add(m.primary_theme);
  if (m.secondary_theme && m.secondary_theme !== 'none') themes.add(m.secondary_theme);
}

// 3. Update mergeMovies function (around line 278-309):
function mergeMovies(a, b) {
  return {
    title: a.title || b.title,
    year: a.year || b.year,
    director: a.director || b.director,
    plot: a.plot || b.plot,
    genres: union(a.genres, b.genres),
    emotional_tone: union(a.emotional_tone, b.emotional_tone),
    themes: union(a.themes, b.themes),
    pacing_style: a.pacing_style || b.pacing_style,
    visual_aesthetic: a.visual_aesthetic || b.visual_aesthetic,
    target_audience: a.target_audience || b.target_audience,
    similar_films: union(a.similar_films, b.similar_films),
    cultural_context: union(a.cultural_context, b.cultural_context),
    narrative_structure: a.narrative_structure || b.narrative_structure,
    energy_level: a.energy_level || b.energy_level,
    discussion_topics: union(a.discussion_topics, b.discussion_topics),
    card_description: a.card_description || b.card_description,
    profile_text: a.profile_text || b.profile_text,
    intensity_level: a.intensity_level || b.intensity_level,
    // Keep new structure fields
    primary_emotional_tone: a.primary_emotional_tone || b.primary_emotional_tone,
    secondary_emotional_tone: a.secondary_emotional_tone || b.secondary_emotional_tone,
    primary_theme: a.primary_theme || b.primary_theme,
    secondary_theme: a.secondary_theme || b.secondary_theme
  };
}

// 4. Update movie card rendering to use card_description (around line 900-906):
// In the recommendation rendering section, replace:
const themes = (p?.themes || []).slice(0,4).join(', ');
const tones = (p?.emotional_tone || []).slice(0,3).join(', ');

// With:
const themes = (p?.themes || []).slice(0,4).join(', ');
const tones = (p?.emotional_tone || []).slice(0,3).join(', ');

// And in the movie card HTML, replace the description line with:
<div class="movie-description">
  <p>${escapeHtml(movie.card_description || movie.plot)}</p>
</div>

// 5. Update the recommendation card description (around line 906):
// Replace:
<div class="rec-description">${escapeHtml(p.card_description || p.plot)}</div>

// The rest of the code should work as-is since we're converting the new structure back to arrays
