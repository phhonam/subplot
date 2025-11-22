#!/usr/bin/env python3
"""
Generate profile_text for golden dataset movies using v1.1 enhanced prompt.
Uses OpenAI API to generate new profile_text with specificity requirements.
"""

import json
import os
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def load_v1_1_prompt():
    """Load the v1.1 prompt configuration"""
    prompt_file = Path('prompt_engineering/prompts/versions/v1.1_specificity_focused.json')
    with open(prompt_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_movie_data(movie_title, all_profiles):
    """Load movie data from merged profiles"""
    if movie_title in all_profiles:
        movie = all_profiles[movie_title]
        return {
            'title': movie.get('title', movie_title),
            'year': movie.get('year', ''),
            'director': movie.get('director', ''),
            'genres': movie.get('genre_tags', []),
            'plot_summary': movie.get('plot_summary', ''),
            'visual_style': movie.get('visual_style', 'Not specified'),
            'critic_reviews': '\n'.join(movie.get('critic_reviews', [])[:2]),
            'user_reviews': '\n'.join(movie.get('user_reviews', [])[:2])
        }
    return None

def generate_theme_list():
    """Generate the theme list for the prompt"""
    themes = [
        ("coming_of_age", "teenage angst, first love, finding yourself"),
        ("midlife_crisis", "career changes, relationship reevaluation, existential questioning"),
        ("identity_crisis", "who am I really? cultural identity, gender identity"),
        ("found_family", "chosen family, unlikely friendships, community bonds"),
        ("toxic_relationships", "codependency, manipulation, unhealthy dynamics"),
        ("forbidden_love", "taboo romance, star-crossed lovers, social barriers"),
        ("loneliness_isolation", "social alienation, urban isolation, emotional distance"),
        ("class_warfare", "rich vs poor, social mobility, economic inequality"),
        ("institutional_corruption", "systemic abuse, cover-ups, whistleblowing"),
        ("surveillance_control", "big brother, privacy invasion, authoritarianism"),
        ("media_manipulation", "fake news, propaganda, truth vs perception"),
        ("underdog_triumph", "beating the odds, small vs big, David vs Goliath"),
        ("post_apocalyptic", "end of world, rebuilding society, resource scarcity"),
        ("mental_health_struggle", "depression, addiction, trauma recovery"),
        ("immigrant_experience", "cultural adaptation, language barriers, belonging"),
        ("artistic_obsession", "creative madness, perfectionism, artistic sacrifice"),
        ("performance_anxiety", "stage fright, imposter syndrome, public scrutiny"),
        ("creative_block", "writer's block, artistic crisis, inspiration loss"),
        ("nostalgia_longing", "past regrets, lost opportunities, what could have been"),
        ("time_travel_paradox", "changing the past, multiple timelines, fate vs choice"),
        ("memory_loss", "amnesia, dementia, unreliable narrator"),
        ("ai_consciousness", "artificial intelligence, what makes us human"),
        ("virtual_reality", "digital worlds, reality vs simulation"),
        ("technological_dystopia", "tech gone wrong, digital surveillance, automation"),
        ("environmental_crisis", "climate change, ecological disaster, human impact"),
        ("wilderness_survival", "nature vs civilization, back to basics, primal instincts"),
        ("cosmic_horror", "vast unknown, existential dread, cosmic insignificance"),
        ("moral_ambiguity", "gray areas, difficult choices, no clear heroes"),
        ("revenge_justice", "vigilante justice, personal vendettas, eye for an eye"),
        ("organized_crime", "mafia, gangs, criminal underworld"),
        ("war_trauma", "PTSD, survivor's guilt, war's lasting effects"),
        ("civil_unrest", "protests, revolutions, social upheaval"),
        ("cold_war_espionage", "spies, double agents, political intrigue")
    ]
    return "\n".join([f"- {theme}: {desc}" for theme, desc in themes])

def build_prompt(movie_data, prompt_config):
    """Build the full prompt using v1.1 template"""
    system_prompt = prompt_config['full_prompt']['system_prompt']
    user_template = prompt_config['full_prompt']['user_prompt_template']
    theme_list = generate_theme_list()
    
    # Fill in the template
    user_prompt = user_template.format(
        title=movie_data['title'],
        year=movie_data['year'],
        director=movie_data['director'],
        genres=', '.join(movie_data['genres']),
        plot_summary=movie_data['plot_summary'],
        visual_style=movie_data['visual_style'],
        critic_reviews=movie_data['critic_reviews'] or "None available",
        user_reviews=movie_data['user_reviews'] or "None available",
        theme_list=theme_list
    )
    
    return system_prompt, user_prompt

def extract_profile_text_from_response(response_text):
    """Extract just the PROFILE_TEXT section from LLM response"""
    lines = response_text.split('\n')
    profile_lines = []
    in_profile = False
    
    for line in lines:
        if 'PROFILE_TEXT' in line.upper() or 'PROFILE_SUMMARY' in line.upper():
            in_profile = True
            continue
        if in_profile:
            # Stop if we hit another all-caps section
            if line and line.isupper() and line.strip().endswith(':'):
                break
            profile_lines.append(line)
    
    profile_text = '\n'.join(profile_lines).strip()
    
    # If we didn't find a section, try to extract the last 2-3 paragraphs
    if not profile_text:
        paragraphs = response_text.split('\n\n')
        if len(paragraphs) >= 2:
            profile_text = '\n\n'.join(paragraphs[-2:])
    
    return profile_text

def generate_profile_text(movie_data, prompt_config, client):
    """Generate profile_text using OpenAI API"""
    system_prompt, user_prompt = build_prompt(movie_data, prompt_config)
    
    print(f"\n🎬 Generating profile_text for: {movie_data['title']}")
    print("Calling OpenAI API...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use GPT-4 for better quality
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=1200,  # More tokens for detailed profile
            temperature=0.7
        )
        
        full_response = response.choices[0].message.content
        profile_text = extract_profile_text_from_response(full_response)
        
        print(f"✅ Generated profile_text ({len(profile_text)} chars)")
        return profile_text
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    # Load movies and prompt config
    print("Loading data...")
    
    with open('movie_profiles_merged.json', 'r', encoding='utf-8') as f:
        all_profiles = json.load(f)
    
    prompt_config = load_v1_1_prompt()
    
    # Select movies to generate
    golden_movies = [
        'Citizen Kane',
        'Tangerine', 
        'Close-Up',
        'Bicycle Thieves',
        'In the Mood for Love'
    ]
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Generate profiles
    results = {}
    
    for movie_title in golden_movies:
        print(f"\n{'='*60}")
        print(f"Processing: {movie_title}")
        print('='*60)
        
        movie_data = load_movie_data(movie_title, all_profiles)
        if not movie_data:
            print(f"❌ Movie not found: {movie_title}")
            continue
        
        profile_text = generate_profile_text(movie_data, prompt_config, client)
        
        if profile_text:
            results[movie_title] = {
                'title': movie_data['title'],
                'year': movie_data['year'],
                'director': movie_data['director'],
                'genres': movie_data['genres'],
                'plot_summary': movie_data['plot_summary'],
                'profile_text': profile_text,
                'version': 'v1.1',
                'generated_at': '2025-10-18'
            }
        
        # Small delay to respect rate limits
        import time
        time.sleep(1)
    
    # Save results
    output_file = Path('prompt_engineering/golden_dataset/generated_profiles_v1.1.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✅ Generated {len(results)} profiles")
    print(f"📁 Saved to: {output_file}")
    print('='*60)

if __name__ == "__main__":
    main()
