import json
import os
from main import MovieRecommender

# Choose provider: "openai", "anthropic", or "ollama"
provider = "openai"

# Process only the merged movie data
src = "/Users/nam/movie-recommender/merged_movie_data.json"
out = "/Users/nam/movie-recommender/movie_profiles_merged.json"

print(f"\n=== Generating profiles from {src} ===")
rec = MovieRecommender(llm_provider=provider)
rec.load_movie_data(src)
rec.generate_all_profiles()   # calls the LLM once per movie
rec.save_profiles(out)

print(f"\n✓ Profiles generated and saved to {out}")