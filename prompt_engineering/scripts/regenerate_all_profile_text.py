#!/usr/bin/env python3
"""
Regenerate profile_text for all movies in movie_profiles_merged.json using v1.1 enhanced prompt.
Only updates the profile_text field, preserves all other fields.

Features:
- Timestamped backup creation
- Batch processing with rate limiting
- Checkpoint system for resume capability
- Error handling and retry logic
- Progress tracking and reporting
"""

import json
import os
import sys
import time
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Constants
CHECKPOINT_FILE = Path('prompt_engineering/regeneration_checkpoint.json')
PROMPT_FILE = Path('prompt_engineering/prompts/versions/v1.1_specificity_focused.json')
MOVIE_FILE = Path('movie_profiles_merged.json')
BACKUP_DIR = Path('backups')
BATCH_SIZE = 25  # Reduced for more frequent checkpoints
API_DELAY = 0.5  # Reduced delay for faster processing
MAX_RETRIES = 3

def load_v1_1_prompt() -> Dict[str, Any]:
    """Load the v1.1 prompt configuration"""
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_theme_list() -> str:
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

def build_prompt(movie_data: Dict[str, Any], prompt_config: Dict[str, Any]) -> tuple[str, str]:
    """Build the full prompt using v1.1 template"""
    system_prompt = prompt_config['full_prompt']['system_prompt']
    user_template = prompt_config['full_prompt']['user_prompt_template']
    theme_list = generate_theme_list()
    
    # Get reviews if available
    critic_reviews = '\n'.join(movie_data.get('critic_reviews', [])[:2]) if movie_data.get('critic_reviews') else "None available"
    user_reviews = '\n'.join(movie_data.get('user_reviews', [])[:2]) if movie_data.get('user_reviews') else "None available"
    
    # Fill in the template
    user_prompt = user_template.format(
        title=movie_data.get('title', ''),
        year=movie_data.get('year', ''),
        director=movie_data.get('director', ''),
        genres=', '.join(movie_data.get('genre_tags', [])),
        plot_summary=movie_data.get('plot_summary', ''),
        visual_style=movie_data.get('visual_style', 'Not specified'),
        critic_reviews=critic_reviews,
        user_reviews=user_reviews,
        theme_list=theme_list
    )
    
    return system_prompt, user_prompt

def extract_profile_text_from_response(response_text: str) -> str:
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

def generate_profile_text(movie_data: Dict[str, Any], prompt_config: Dict[str, Any], client: OpenAI) -> Optional[str]:
    """Generate profile_text using OpenAI API with retry logic"""
    system_prompt, user_prompt = build_prompt(movie_data, prompt_config)
    title = movie_data.get('title', 'Unknown')
    
    for attempt in range(MAX_RETRIES):
        try:
            api_start = time.time()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000,  # Reduced for faster response
                temperature=0.6,  # Slightly lower for more consistent output
                top_p=0.9,  # Add top_p for better quality
                frequency_penalty=0.1,  # Reduce repetition
                presence_penalty=0.1  # Encourage new content
            )
            api_time = time.time() - api_start
            
            full_response = response.choices[0].message.content
            profile_text = extract_profile_text_from_response(full_response)
            
            if profile_text:
                return profile_text
            else:
                print(f"    ⚠️  Warning: Empty profile_text for {title} (API: {api_time:.1f}s)")
                return None
                
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"    ⚠️  API error (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)[:100]}... Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"    ❌ Failed after {MAX_RETRIES} attempts: {str(e)[:100]}...")
                return None
    
    return None

def create_backup() -> Path:
    """Create timestamped backup of movie_profiles_merged.json"""
    BACKUP_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"movie_profiles_merged_backup_{timestamp}.json"
    
    shutil.copy2(MOVIE_FILE, backup_file)
    return backup_file

def load_checkpoint() -> Optional[Dict[str, Any]]:
    """Load checkpoint if exists"""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_checkpoint(checkpoint: Dict[str, Any]):
    """Save checkpoint"""
    CHECKPOINT_FILE.parent.mkdir(exist_ok=True)
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=2)

def save_movies(movies: Dict[str, Any]):
    """Save updated movies to file"""
    with open(MOVIE_FILE, 'w', encoding='utf-8') as f:
        json.dump(movies, f, indent=2, ensure_ascii=False)

def main():
    import sys
    sys.stdout.flush()  # Force immediate output
    
    print("="*80, flush=True)
    print("Profile Text Regeneration - v1.1 Enhanced", flush=True)
    print("="*80, flush=True)
    
    # Create backup
    backup_file = create_backup()
    print(f"\n✅ Created backup: {backup_file}")
    
    # Load v1.1 prompt
    prompt_config = load_v1_1_prompt()
    
    # Load movies
    print(f"📚 Loading movies...")
    with open(MOVIE_FILE, 'r', encoding='utf-8') as f:
        movies = json.load(f)
    
    total_movies = len(movies)
    print(f"✅ Loaded {total_movies} movies")
    
    # Show configuration
    print(f"\n⚙️  Configuration:")
    print(f"   • API Delay: {API_DELAY}s between calls")
    print(f"   • Batch Size: {BATCH_SIZE} movies per checkpoint")
    print(f"   • Max Retries: {MAX_RETRIES} per movie")
    print(f"   • Model: gpt-4o-mini (optimized parameters)")
    
    # Estimate time
    estimated_time_per_movie = 2.0  # seconds (conservative estimate)
    estimated_total_minutes = (total_movies * estimated_time_per_movie) / 60
    print(f"   • Estimated time: ~{estimated_total_minutes:.1f} minutes")
    print(f"   • Progress updates: Every 10 movies")
    print(f"   • Checkpoints: Every {BATCH_SIZE} movies")
    
    # Check for existing checkpoint
    checkpoint = load_checkpoint()
    processed_movies = set()
    failed_movies = []
    
    if checkpoint:
        print(f"\n🔄 Resuming from checkpoint...")
        print(f"   Previously processed: {checkpoint['processed_movies']} movies")
        processed_movies = set(checkpoint.get('processed_titles', []))
        failed_movies = checkpoint.get('failed_movies', [])
        start_idx = checkpoint['processed_movies']
    else:
        print(f"\n🚀 Starting fresh regeneration...")
        start_idx = 0
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Track progress
    movie_list = list(movies.items())
    updated_count = 0
    skipped_count = 0
    start_time = time.time()
    
    print(f"\n🎬 Processing movies...\n")
    
    for idx, (title, movie_data) in enumerate(movie_list[start_idx:], start=start_idx + 1):
        # Skip if already processed
        if title in processed_movies:
            skipped_count += 1
            print(f"[{idx}/{total_movies}] ⏭️  Skipping {title} (already processed)", flush=True)
            continue
        
        # Validate required fields
        if not movie_data.get('title') or not movie_data.get('plot_summary'):
            print(f"[{idx}/{total_movies}] ⚠️  Skipping {title}: missing required data", flush=True)
            failed_movies.append({'title': title, 'reason': 'Missing required fields'})
            continue
        
        # Start generating profile_text
        print(f"[{idx}/{total_movies}] 🎬 Starting profile generation for: {title}", flush=True)
        start_movie_time = time.time()
        
        profile_text = generate_profile_text(movie_data, prompt_config, client)
        
        movie_elapsed = time.time() - start_movie_time
        
        if profile_text:
            # Update only profile_text field
            movies[title]['profile_text'] = profile_text
            updated_count += 1
            print(f"[{idx}/{total_movies}] ✅ Completed {title} ({len(profile_text)} chars, {movie_elapsed:.1f}s)", flush=True)
        else:
            print(f"[{idx}/{total_movies}] ❌ Failed {title} ({movie_elapsed:.1f}s)", flush=True)
            failed_movies.append({'title': title, 'reason': 'API generation failed'})
        
        processed_movies.add(title)
        
        # Show progress summary every 10 movies
        if idx % 10 == 0:
            elapsed_total = (time.time() - start_time) / 60
            avg_time_per_movie = elapsed_total / (idx - start_idx) if idx > start_idx else 0
            remaining_movies = total_movies - idx
            eta_minutes = (remaining_movies * avg_time_per_movie) if avg_time_per_movie > 0 else 0
            
            print(f"\n📊 Progress: {idx}/{total_movies} ({idx/total_movies*100:.1f}%) | "
                  f"Updated: {updated_count} | Failed: {len(failed_movies)} | "
                  f"ETA: {eta_minutes:.1f}min\n", flush=True)
        
        # Save checkpoint every BATCH_SIZE movies
        if idx % BATCH_SIZE == 0:
            checkpoint_data = {
                'version': 'v1.1',
                'started_at': checkpoint.get('started_at', datetime.now().isoformat()) if checkpoint else datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'total_movies': total_movies,
                'processed_movies': idx,
                'processed_titles': list(processed_movies),
                'failed_movies': failed_movies,
                'backup_file': str(backup_file)
            }
            save_checkpoint(checkpoint_data)
            save_movies(movies)  # Save progress to main file
            elapsed = (time.time() - start_time) / 60
            print(f"\n💾 Checkpoint saved - {idx}/{total_movies} movies ({elapsed:.1f} min elapsed)\n")
        
        # Rate limiting
        time.sleep(API_DELAY)
    
    # Final save
    print(f"\n💾 Saving final results...")
    save_movies(movies)
    
    # Clean up checkpoint
    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()
    
    # Generate summary
    elapsed_time = time.time() - start_time
    print(f"\n{'='*80}")
    print("✅ REGENERATION COMPLETE")
    print(f"{'='*80}")
    print(f"Total movies:        {total_movies}")
    print(f"Updated:            {updated_count}")
    print(f"Skipped:            {skipped_count}")
    print(f"Failed:             {len(failed_movies)}")
    print(f"Time elapsed:       {elapsed_time/60:.1f} minutes")
    print(f"Backup file:        {backup_file}")
    
    if failed_movies:
        print(f"\n⚠️  Failed movies ({len(failed_movies)}):")
        for movie in failed_movies[:10]:  # Show first 10
            print(f"   - {movie['title']}: {movie['reason']}")
        if len(failed_movies) > 10:
            print(f"   ... and {len(failed_movies) - 10} more")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()
