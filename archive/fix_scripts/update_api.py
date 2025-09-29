#!/usr/bin/env python3

# Update API to handle new profile structure
with open('api.py', 'r') as f:
    content = f.read()

# Update _merge_profiles function to handle new structure
content = content.replace(
    '''    return {
        "title": pref(a.get("title"), b.get("title")),
        "emotional_tone": union(a.get("emotional_tone"), b.get("emotional_tone")),
        "themes": union(a.get("themes"), b.get("themes")),
        "pacing_style": pref(a.get("pacing_style"), b.get("pacing_style")),
        "visual_aesthetic": pref(a.get("visual_aesthetic"), b.get("visual_aesthetic")),
        "target_audience": pref(a.get("target_audience"), b.get("target_audience")),
        "similar_films": union(a.get("similar_films"), b.get("similar_films")),
        "cultural_context": union(a.get("cultural_context"), b.get("cultural_context")),
        "narrative_structure": pref(a.get("narrative_structure"), b.get("narrative_structure")),
        "energy_level": pref(a.get("energy_level"), b.get("energy_level")),
        "discussion_topics": union(a.get("discussion_topics"), b.get("discussion_topics")),
        "profile_text": pref(a.get("profile_text"), b.get("profile_text")),
    }''',
    '''    return {
        "title": pref(a.get("title"), b.get("title")),
        "emotional_tone": union(a.get("emotional_tone"), b.get("emotional_tone")),
        "themes": union(a.get("themes"), b.get("themes")),
        "pacing_style": pref(a.get("pacing_style"), b.get("pacing_style")),
        "visual_aesthetic": pref(a.get("visual_aesthetic"), b.get("visual_aesthetic")),
        "target_audience": pref(a.get("target_audience"), b.get("target_audience")),
        "similar_films": union(a.get("similar_films"), b.get("similar_films")),
        "cultural_context": union(a.get("cultural_context"), b.get("cultural_context")),
        "narrative_structure": pref(a.get("narrative_structure"), b.get("narrative_structure")),
        "energy_level": pref(a.get("energy_level"), b.get("energy_level")),
        "discussion_topics": union(a.get("discussion_topics"), b.get("discussion_topics")),
        "card_description": pref(a.get("card_description"), b.get("card_description")),
        "profile_text": pref(a.get("profile_text"), b.get("profile_text")),
        # New structure fields
        "primary_emotional_tone": pref(a.get("primary_emotional_tone"), b.get("primary_emotional_tone")),
        "secondary_emotional_tone": pref(a.get("secondary_emotional_tone"), b.get("secondary_emotional_tone")),
        "primary_theme": pref(a.get("primary_theme"), b.get("primary_theme")),
        "secondary_theme": pref(a.get("secondary_theme"), b.get("secondary_theme")),
        "intensity_level": pref(a.get("intensity_level"), b.get("intensity_level")),
    }'''
)

# Update _normalize function to handle new structure
content = content.replace(
    '''def _normalize(obj: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": obj.get("title") or obj.get("Title") or "Untitled",
        "emotional_tone": _to_list(obj.get("emotional_tone")),
        "themes": _to_list(obj.get("themes")),
        "pacing_style": obj.get("pacing_style") or "",
        "visual_aesthetic": obj.get("visual_aesthetic") or "",
        "target_audience": obj.get("target_audience") or "",
        "similar_films": _to_list(obj.get("similar_films")),
        "cultural_context": _to_list(obj.get("cultural_context")),
        "narrative_structure": obj.get("narrative_structure") or "",
        "energy_level": obj.get("energy_level") or "",
        "discussion_topics": _to_list(obj.get("discussion_topics")),
        "profile_text": obj.get("profile_text") or "",
    }''',
    '''def _normalize(obj: Dict[str, Any]) -> Dict[str, Any]:
    # Convert new structure to old structure for compatibility
    emotional_tone = []
    if obj.get("primary_emotional_tone"):
        emotional_tone.append(obj.get("primary_emotional_tone"))
    if obj.get("secondary_emotional_tone") and obj.get("secondary_emotional_tone") != "none":
        emotional_tone.append(obj.get("secondary_emotional_tone"))
    
    themes = []
    if obj.get("primary_theme"):
        themes.append(obj.get("primary_theme"))
    if obj.get("secondary_theme") and obj.get("secondary_theme") != "none":
        themes.append(obj.get("secondary_theme"))
    
    return {
        "title": obj.get("title") or obj.get("Title") or "Untitled",
        "emotional_tone": emotional_tone or _to_list(obj.get("emotional_tone")),
        "themes": themes or _to_list(obj.get("themes")),
        "pacing_style": obj.get("pacing_style") or "",
        "visual_aesthetic": obj.get("visual_aesthetic") or "",
        "target_audience": obj.get("target_audience") or "",
        "similar_films": _to_list(obj.get("similar_films")),
        "cultural_context": _to_list(obj.get("cultural_context")),
        "narrative_structure": obj.get("narrative_structure") or "",
        "energy_level": obj.get("energy_level") or "",
        "discussion_topics": _to_list(obj.get("discussion_topics")),
        "card_description": obj.get("card_description") or "",
        "profile_text": obj.get("profile_text") or "",
        # Keep new structure fields
        "primary_emotional_tone": obj.get("primary_emotional_tone"),
        "secondary_emotional_tone": obj.get("secondary_emotional_tone"),
        "primary_theme": obj.get("primary_theme"),
        "secondary_theme": obj.get("secondary_theme"),
        "intensity_level": obj.get("intensity_level"),
    }'''
)

# Write back the updated content
with open('api.py', 'w') as f:
    f.write(content)

print('✅ Updated API to handle new profile structure')
print('Changes made:')
print('- Updated _merge_profiles to include new fields')
print('- Updated _normalize to convert new structure to old structure for compatibility')
print('- Added card_description support')
