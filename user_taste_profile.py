import os
import json
from typing import Any, Dict, List, Optional, Tuple
import requests
from main import MovieRecommender, MovieProfile

# Ensure .env environment variables are loaded when this module is used standalone
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    # If python-dotenv isn't installed or .env not present, silently continue
    pass


LLM_OUTPUT_SCHEMA = """{
  "narrative": "1-2 vivid paragraphs that capture the user's specific taste (avoid generic filler)",
  "signature_preferences": {
    "emotional_tone": ["..."],
    "themes": ["..."],
    "cultural_context": ["..."],
    "discussion_topics": ["..."],
    "pacing": ["..."],
    "narrative_style": ["..."],
    "energy": ["..."],
    "audience_markers": ["..."]
  },
  "contrasts_and_edges": [
    "specific nuance or boundary of taste (e.g., 'likes slow-burn family dramas but not sentimentality')"
  ],
  "watch_next_criteria": [
    "concrete guidance for curation (e.g., 'intergenerational dramas set outside the US with observational camera work')"
  ]
}"""

SYSTEM_GUIDANCE = SYSTEM_GUIDANCE = """You're someone who's studied this person's movie collection and formed strong opinions about what kind of person they are. Share your personal take on them.

YOUR VOICE: Opinionated, observant, slightly judgmental but affectionate - like a friend who knows your secrets

PART 1 - PERSONALITY DIAGNOSIS:
Write 1-2 paragraphs using "I think you're..." voice. Be direct and specific about their personality quirks. Use actual scenes from their movies as evidence. Randomize the orders of the movies referenced.

STRUCTURE YOUR ANALYSIS:
"I think you're the type who..." 
"My guess is you..."
"I bet you..."
"You strike me as someone who..."

USE SPECIFIC MOVIE DETAILS AS EVIDENCE:
- Reference memorable scenes, shots, or moments that reveal something about THEM
- "I think you're someone who probably got way too invested in [specific movie moment] because [psychological insight about them]"
- Use these details to build your case about their personality

EXAMPLES OF THE APPROACH:
"I think you're the type who watches the Star Child sequence in 2001 and feels personally vindicated, like finally someone gets that you're destined for something bigger than your current life."
"I think you're someone who probably got way too excited during the briefcase scene in Pulp Fiction - not because of the mystery, but because you love feeling like you're in on something everyone else is missing. My guess is you're the type who quotes movie lines to seem interesting at parties."
"My guess is you ugly-cried during the van scene in Nomadland because you're secretly terrified you'll end up alone, but you tell yourself it's about 'finding freedom.'"

PART 2 - MOVIE RECOMMENDATIONS:
List 3-5 specific films they should watch next, with brief explanations of why each matches their psychological profile.

EXAMPLE:
"You should watch The Master because you clearly have a thing for characters who think they're special but might just be delusional."

BE PERSONAL AND SPECIFIC:
- What do their choices reveal about their insecurities, dreams, or blind spots?
- How do they probably relate to specific characters or moments?
- MUST: What does this combination say about how they see themselves vs reality?

TONE: Direct personal assessment, not film criticism
BANNED: All film school language, abstract concepts, generic observations
REQUIRED: Specific movie moments used as psychological evidence about the person
REQUIRED: Movie recommendations

Respond ONLY with strict JSON matching the provided schema."""


def _read_attr(p: Any, key: str, default: Any = None) -> Any:
    # Support dict or object access
    if isinstance(p, dict):
        return p.get(key, default)
    return getattr(p, key, default)


def _normalize_narrative(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(x) for x in value)
    return str(value or "")


def _compact_movie_snapshot(p: Any) -> Dict[str, Any]:
    return {
        "title": _read_attr(p, "title", ""),
        "emotional_tone": _read_attr(p, "emotional_tone", []) or [],
        "themes": _read_attr(p, "themes", []) or [],
        "pacing_style": _read_attr(p, "pacing_style", "") or "",
        "visual_aesthetic": _read_attr(p, "visual_aesthetic", "") or "",
        "target_audience": _read_attr(p, "target_audience", "") or "",
        "similar_films": _read_attr(p, "similar_films", []) or [],
        "cultural_context": _read_attr(p, "cultural_context", []) or [],
        "narrative_structure": _normalize_narrative(_read_attr(p, "narrative_structure", "")),
        "energy_level": _read_attr(p, "energy_level", "") or "",
        "discussion_topics": _read_attr(p, "discussion_topics", []) or [],
    }


def resolve_liked_movies(movie_profiles: Dict[str, Any], liked_movies: List[str]) -> (List[str], List[str]):
    """Return a tuple of (used_titles, skipped_titles).
    Used = present in movie_profiles; Skipped = not found in movie_profiles.
    """
    used = [m for m in liked_movies if m in movie_profiles]
    skipped = [m for m in liked_movies if m not in movie_profiles]
    return used, skipped


def _build_prompt(movie_profiles: Dict[str, Any], liked_movies: List[str]) -> str:
    used, _ = resolve_liked_movies(movie_profiles, liked_movies)
    items = [_compact_movie_snapshot(movie_profiles[m]) for m in used]
    examples = json.dumps(items, indent=2, ensure_ascii=False)

    return f"""
Give this person a personality reading based on their {len(used)} favorite movies, then recommend specific films for them.

STEP 1: Diagnose their personality using "I think you're..." language. Reference specific scenes/moments from their actual movies as evidence of who they are.

STEP 2: Recommend 1-2 specific films that would appeal to their psychological makeup (not just similar genres).

Their movies:
{examples}

Be direct, be specific, be slightly judgmental. Use movie details as evidence of their personality, then suggest films that match their psychological needs.

Make it feel personal - like you know them through their movie choices.

Respond ONLY as strict JSON with this structure:
{LLM_OUTPUT_SCHEMA}

IMPORTANT: The watch_next_criteria should contain actual movie titles with brief explanations, not abstract criteria.
""".strip()


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                pass
    return {"narrative": text.strip()[:1000]}


def _call_openai(messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo", temperature: float = 0.5, max_tokens: int = 1000) -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment.")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return _extract_json(content)


def _call_anthropic(system: str, user: str, model: str = "claude-3-sonnet-20240229", max_tokens: int = 700) -> Dict[str, Any]:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in environment.")
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    # content is a list of blocks; take first text block
    blocks = data.get("content", [])
    text = ""
    for b in blocks:
        if b.get("type") == "text":
            text += b.get("text", "")
    return _extract_json(text)


def _call_ollama(full_prompt: str, model: str = "llama2") -> Dict[str, Any]:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    url = f"{base_url}/api/generate"
    payload = {
        "model": model,
        "prompt": full_prompt,
        "stream": False,
    }
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    text = data.get("response", "")
    return _extract_json(text)


def generate_llm_taste_profile(
    movie_profiles: Dict[str, Any],
    liked_movies: List[str],
    provider: str = "openai",
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build an expressive, non-generic user taste profile using an LLM.
    - movie_profiles: mapping of title -> profile (dict or object with needed fields)
    - liked_movies: list of titles to consider
    - provider: "openai" | "anthropic" | "ollama"
    - model: optional override model name per provider
    """
    if not liked_movies:
        return {}

    user_prompt = _build_prompt(movie_profiles, liked_movies)

    try:
        if provider == "openai":
            # Prefer a stronger default; allow env override via TASTE_MODEL
            import os
            use_model = model or os.getenv("TASTE_MODEL", "gpt-4o-mini")
            messages = [
                {"role": "system", "content": SYSTEM_GUIDANCE},
                {"role": "user", "content": user_prompt},
            ]
            result = _call_openai(messages, model=use_model)
            if isinstance(result, dict):
                result["_meta"] = {"provider": "openai", "model": use_model}
            return result

        elif provider == "anthropic":
            use_model = model or "claude-3-sonnet-20240229"
            result = _call_anthropic(SYSTEM_GUIDANCE, user_prompt, model=use_model)
            if isinstance(result, dict):
                result["_meta"] = {"provider": "anthropic", "model": use_model}
            return result

        elif provider == "ollama":
            full_prompt = f"{SYSTEM_GUIDANCE}\n\n{user_prompt}\n\nReturn strict JSON only."
            use_model = model or "llama2"
            result = _call_ollama(full_prompt, model=use_model)
            if isinstance(result, dict):
                result["_meta"] = {"provider": "ollama", "model": use_model}
            return result

        else:
            return {"narrative": "Unsupported provider specified.", "signature_preferences": {}, "contrasts_and_edges": [], "watch_next_criteria": []}

    except requests.HTTPError as e:
        return {"narrative": f"HTTP error from provider: {e}", "signature_preferences": {}, "contrasts_and_edges": [], "watch_next_criteria": []}
    except Exception as e:
        return {"narrative": f"Provider error: {e}", "signature_preferences": {}, "contrasts_and_edges": [], "watch_next_criteria": []}


class SimpleMovieRecommender:
    """Simple interactive interface for movie recommendations"""

    def __init__(self):
        self.recommender = None
        self.matcher = None
        self.setup_system()

    def setup_system(self):
        """Initialize the movie recommender and preference matcher."""
        self.recommender = MovieRecommender()
        self.recommender.load_movie_profiles("movie_profiles.json")
        self.matcher = self.recommender.preference_matcher

    def display_available_movies(self):
        """Display the list of available movies."""
        print("\nAvailable Movies:")
        for title in sorted(self.recommender.movie_profiles.keys()):
            print(f"- {title}")

    def get_user_movie_selection(self, prompt: str, num_movies: int) -> List[str]:
        """Get movie selections from the user."""
        selected_movies = []
        while len(selected_movies) < num_movies:
            movie = input(f"{prompt} ({len(selected_movies)}/{num_movies}, type 'list' for options): ").strip()
            if movie.lower() == 'list':
                self.display_available_movies()
            elif movie in self.recommender.movie_profiles and movie not in selected_movies:
                selected_movies.append(movie)
            elif movie in selected_movies:
                print("You have already selected that movie. Please choose another.")
            else:
                print("Invalid movie title. Please choose from the available movies.")
        return selected_movies

    def display_recommendations(self, recommendations: List[Tuple[str, float]]):
        """Display the recommendations to the user."""
        print("\nRecommended Movies:")
        for movie, score in recommendations:
            print(f"- {movie} (Score: {score:.2f})")

    def run_recommendation_session(self):
        """Run a complete recommendation session"""
        print("\n" + "=" * 70)
        print("WELCOME TO THE INDIE MOVIE RECOMMENDATION SYSTEM")
        print("=" * 70)
        print("This system will recommend movies based on your preferences.")
        print("Type 'list' anytime to see all available movies.")

        # Display available movies
        self.display_available_movies()

        # Get user's favorite movies
        liked_movies = self.get_user_movie_selection(
            "Select 2-3 movies you absolutely love:", 3
        )

        if not liked_movies:
            print("No movies selected. Goodbye!")
            return

        print(f"\nYou selected: {', '.join(liked_movies)}")

        # Generate a concise LLM-based user taste profile before recommendations
        try:
            from user_taste_profile import generate_llm_taste_profile
            # Use the same provider you initialized elsewhere, or default to "openai"
            provider = "openai"
            taste = generate_llm_taste_profile(self.recommender.movie_profiles, liked_movies, provider=provider)

            narrative = taste.get("narrative", "").strip()
            sig = taste.get("signature_preferences", {})

            print("\n" + "=" * 70)
            print("YOUR TASTE PROFILE (LLM)")
            print("=" * 70)
            if narrative:
                print(narrative)
            else:
                print("No narrative available.")

            # Print a compact subset of facets if present
            compact_keys = ["emotional_tone", "themes", "cultural_context", "pacing", "narrative_style"]
            compact_lines = []
            if isinstance(sig, dict):
                for k in compact_keys:
                    v = sig.get(k)
                    if isinstance(v, list) and v:
                        compact_lines.append(f"- {k.replace('_', ' ').title()}: {', '.join(v[:5])}")
            if compact_lines:
                print("\nKey preferences:")
                for line in compact_lines:
                    print(line)
        except Exception as e:
            # Keep the session going even if the LLM profile fails
            print("\n(Note: Could not generate LLM taste profile. Proceeding with recommendations.)")

        # Generate recommendations
        print("\nGenerating recommendations based on your preferences...")
        recommendations = self.matcher.recommend_based_on_preferences(liked_movies, top_n=5)

        if not recommendations:
            print("Sorry, no recommendations available.")
            return

        # Display recommendations
        self.display_recommendations(recommendations)


if __name__ == "__main__":
    # Minimal CLI test: loads existing profiles JSON and prints a narrative for a hard-coded set.
    # This avoids importing the rest of the project to keep dependencies minimal.
    import argparse

    parser = argparse.ArgumentParser(description="Generate LLM-based user taste profile.")
    parser.add_argument("--profiles", default="movie_profiles_top_rated_us.json", help="Path to profiles JSON")
    parser.add_argument("--liked", nargs="+", default=["The Silence of the Lambs", "Tokyo Story", "Vertigo"], help="Liked movie titles")
    parser.add_argument("--provider", default="openai", choices=["openai", "anthropic", "ollama"], help="LLM provider")
    parser.add_argument("--model", default=None, help="Model override")
    args = parser.parse_args()

    # Load profiles from JSON file into a dict
    with open(args.profiles, "r") as f:
        profiles_data = json.load(f)

    # movie_profiles here is a mapping of title -> dict profile (works with this module)
    used, skipped = resolve_liked_movies(profiles_data, args.liked)
    print("\n=== LIKED MOVIES CONSIDERED ===")
    if used:
        print("Used:", ", ".join(used))
    else:
        print("Used: (none)")
    if skipped:
        print("Skipped (no profile found):", ", ".join(skipped))

    taste = generate_llm_taste_profile(profiles_data, args.liked, provider=args.provider, model=args.model)

    print("\n=== LLM USER TASTE NARRATIVE ===\n")
    print(taste.get("narrative", ""))

    sig = taste.get("signature_preferences", {})
    if sig:
        print("\n=== SIGNATURE PREFERENCES ===")
        for k, v in sig.items():
            if isinstance(v, list):
                print(f"- {k}: {', '.join(v)}")
            else:
                print(f"- {k}: {v}")

    edges = taste.get("contrasts_and_edges", [])
    if edges:
        print("\n=== CONTRASTS AND EDGES ===")
        for e in edges:
            print(f"- {e}")

    criteria = taste.get("watch_next_criteria", [])
    if criteria:
        print("\n=== WATCH-NEXT CRITERIA ===")
        for c in criteria:
            print(f"- {c}")