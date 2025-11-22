#!/usr/bin/env python3
"""
Extract baseline prompt from main.py and save as versioned JSON
"""

import json
import re
from pathlib import Path

def extract_prompt_from_main():
    """Extract the current prompt from main.py"""
    
    main_py_path = Path("/Users/nam/movie-recommender/main.py")
    
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Extract the _create_profile_prompt method
    method_start = content.find('def _create_profile_prompt(self, movie_data: Dict) -> str:')
    if method_start == -1:
        raise ValueError("Could not find _create_profile_prompt method")
    
    # Find the method body (look for the return statement)
    method_content = content[method_start:]
    
    # Extract the system prompt (lines 433-446)
    system_prompt_start = method_content.find('system_prompt = """You are an expert indie film analyst')
    system_prompt_end = method_content.find('"""', system_prompt_start) + 3
    
    system_prompt = method_content[system_prompt_start:system_prompt_end]
    system_prompt = system_prompt.replace('system_prompt = """', '').replace('"""', '').strip()
    
    # Extract the main prompt template
    prompt_start = method_content.find('prompt = f"""')
    prompt_end = method_content.find('"""', prompt_start) + 3
    
    prompt_template = method_content[prompt_start:prompt_end]
    prompt_template = prompt_template.replace('prompt = f"""', '').replace('"""', '').strip()
    
    # Extract theme categories (the big list)
    theme_list_start = method_content.find('theme_list = "\\n".join([f"- {theme}: {desc}" for theme, desc in [')
    theme_list_end = method_content.find(']])', theme_list_start) + 4
    
    theme_list_code = method_content[theme_list_start:theme_list_end]
    
    # Extract emotional tone categories
    emotional_tones = [
        ("uplifting", "hopeful, inspirational, heartwarming"),
        ("melancholic", "bittersweet, poignant, reflective"),
        ("tense", "suspenseful, unnerving, anxious"),
        ("comedic", "humorous, lighthearted, witty"),
        ("dramatic", "intense, emotional, powerful"),
        ("contemplative", "thoughtful, introspective, meditative"),
        ("dark", "bleak, disturbing, unsettling"),
        ("romantic", "passionate, tender, intimate")
    ]
    
    # Extract theme categories from the code
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
    
    return {
        "system_prompt": system_prompt,
        "prompt_template": prompt_template,
        "emotional_tones": emotional_tones,
        "themes": themes
    }

def create_baseline_version():
    """Create the v1.0 baseline version file"""
    
    prompt_data = extract_prompt_from_main()
    
    baseline_version = {
        "version": "1.0",
        "name": "baseline",
        "created_date": "2025-10-18",
        "description": "Original prompt from main.py - baseline for comparison",
        "components": {
            "system_context": "v1",
            "movement_analysis": "v1",
            "socio_cultural_context": "v1",
            "formal_analysis": "v1",
            "narrative_structure": "v1",
            "profile_text_guidelines": "v1"
        },
        "full_prompt": {
            "system_prompt": prompt_data["system_prompt"],
            "user_prompt_template": prompt_data["prompt_template"],
            "emotional_tones": prompt_data["emotional_tones"],
            "themes": prompt_data["themes"]
        },
        "test_results": {
            "human_eval_avg_score": None,
            "tested_on_movies": [],
            "failure_modes_addressed": [],
            "sample_outputs": {}
        }
    }
    
    # Save to versions directory
    output_path = Path("/Users/nam/movie-recommender/prompt_engineering/prompts/versions/v1.0_baseline.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(baseline_version, f, indent=2)
    
    print(f"✅ Baseline prompt extracted and saved to {output_path}")
    
    return baseline_version

if __name__ == "__main__":
    create_baseline_version()
