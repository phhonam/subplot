# Single-file interactive recommender CLI with built-in similarity matcher

import json
from typing import List, Tuple, Dict
from main import MovieRecommender, MovieProfile

class SimpleSimilarityMatcher:
    """Self-contained similarity matcher for MovieProfile objects."""

    def __init__(self, profiles: Dict[str, MovieProfile]):
        self.profiles = profiles

    # ----- Basic similarity helpers -----
    @staticmethod
    def _jaccard(a: List[str], b: List[str]) -> float:
        set_a, set_b = set(x.lower() for x in a), set(x.lower() for x in b)
        if not set_a and not set_b:
            return 1.0
        if not set_a or not set_b:
            return 0.0
        inter = len(set_a & set_b)
        union = len(set_a | set_b)
        return inter / union if union else 0.0

    @staticmethod
    def _eq_score(a: str, b: str) -> float:
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        return 1.0 if a.strip().lower() == b.strip().lower() else 0.0

    @staticmethod
    def _text_jaccard(a: str, b: str) -> float:
        if not a and not b:
            return 1.0
        if not a or not b:
            return 0.0
        toks_a = set(a.lower().split())
        toks_b = set(b.lower().split())
        stop = {'and', 'the', 'a', 'an', 'of', 'in', 'to', 'for', 'with', 'by'}
        toks_a -= stop
        toks_b -= stop
        if not toks_a and not toks_b:
            return 1.0
        if not toks_a or not toks_b:
            return 0.0
        inter = len(toks_a & toks_b)
        union = len(toks_a | toks_b)
        return inter / union if union else 0.0

    def _profile_similarity(self, p1: MovieProfile, p2: MovieProfile) -> Tuple[float, Dict[str, float]]:
        # Weighted components
        components = {
            "themes": self._jaccard(p1.themes, p2.themes),
            "emotional_tone": self._jaccard(p1.emotional_tone, p2.emotional_tone),
            "pacing_style": self._eq_score(p1.pacing_style, p2.pacing_style),
            "visual_aesthetic": self._text_jaccard(p1.visual_aesthetic, p2.visual_aesthetic),
            "narrative_structure": self._text_jaccard(p1.narrative_structure, p2.narrative_structure),
            "energy_level": self._eq_score(p1.energy_level, p2.energy_level),
            "cultural_context": self._jaccard(p1.cultural_context, p2.cultural_context),
        }
        weights = {
            "themes": 0.35,
            "emotional_tone": 0.30,
            "pacing_style": 0.05,
            "visual_aesthetic": 0.05,
            "narrative_structure": 0.15,
            "energy_level": 0.05,
            "cultural_context": 0.05,
        }
        score = sum(components[k] * weights[k] for k in components)
        return score, components

    def recommend_based_on_preferences(self, liked_titles: List[str], top_n: int = 5) -> List[Tuple[str, float, str]]:
        liked_profiles = [self.profiles[t] for t in liked_titles if t in self.profiles]
        if not liked_profiles:
            return []

        results = []
        for title, cand in self.profiles.items():
            if title in liked_titles:
                continue

            # Average similarity to all liked movies
            scores = []
            per_aspect_accumulator = {}
            for lp in liked_profiles:
                s, aspects = self._profile_similarity(lp, cand)
                scores.append(s)
                for k, v in aspects.items():
                    per_aspect_accumulator.setdefault(k, []).append(v)

            avg_score = sum(scores) / len(scores) if scores else 0.0
            avg_aspects = {k: sum(vs) / len(vs) for k, vs in per_aspect_accumulator.items()}

            # Build explanation from strongest aspects
            top_aspects = sorted(avg_aspects.items(), key=lambda kv: kv[1], reverse=True)[:3]
            def aspect_label(name: str) -> str:
                labels = {
                    "themes": "themes",
                    "emotional_tone": "emotional tone",
                    "pacing_style": "pacing",
                    "visual_aesthetic": "visual style",
                    "narrative_structure": "narrative",
                    "energy_level": "energy",
                    "cultural_context": "cultural context",
                }
                return labels.get(name, name)

            explanation_bits = [f"{aspect_label(k)} match {v:.2f}" for k, v in top_aspects if v > 0]
            explanation = "; ".join(explanation_bits) if explanation_bits else "overall profile alignment"

            results.append((title, avg_score, explanation))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_n]


class InteractiveRecommenderCLI:
    """One-file interactive CLI to gather user input and recommend movies."""

    def __init__(self):
        self.recommender = None
        self.matcher = None
        self._init_system()

    def _init_system(self):
        print("Initializing movie recommendation system...")
        # Load the base recommender and movie data
        self.recommender = MovieRecommender(llm_provider="openai")
        self.recommender.load_movie_data('mock_movie_data.json')

        # Load generated profiles
        try:
            with open('movie_profiles.json', 'r') as f:
                profiles_data = json.load(f)

            for title, data in profiles_data.items():
                profile = MovieProfile(
                    title=data['title'],
                    emotional_tone=data.get('emotional_tone', []),
                    themes=data.get('themes', []),
                    pacing_style=data.get('pacing_style', ''),
                    visual_aesthetic=data.get('visual_aesthetic', ''),
                    target_audience=data.get('target_audience', ''),
                    similar_films=data.get('similar_films', []),
                    cultural_context=data.get('cultural_context', []),
                    narrative_structure=(
                        " ".join(data.get('narrative_structure', []))
                        if isinstance(data.get('narrative_structure'), list)
                        else data.get('narrative_structure', '')
                    ),
                    energy_level=data.get('energy_level', ''),
                    discussion_topics=data.get('discussion_topics', []),
                    profile_text=data.get('profile_text', '')
                )
                self.recommender.movie_profiles[title] = profile

            self.matcher = SimpleSimilarityMatcher(self.recommender.movie_profiles)
            print("System ready!")
        except FileNotFoundError:
            print("Error: movie_profiles.json not found. Please generate profiles first (run main.py).")
            self.matcher = None

    def _list_movies(self):
        movies = list(self.recommender.movie_profiles.keys())
        print("\n" + "=" * 60)
        print("AVAILABLE MOVIES")
        print("=" * 60)
        for i, movie in enumerate(movies, 1):
            profile = self.recommender.movie_profiles[movie]
            themes_str = ", ".join(profile.themes[:2]) if profile.themes else "N/A"
            tone_str = ", ".join(profile.emotional_tone[:2]) if profile.emotional_tone else "N/A"
            print(f"{i:2d}. {movie}")
            print(f"    Themes: {themes_str}")
            print(f"    Mood:   {tone_str}")
        return movies

    def _prompt_selection(self, movies: List[str], prompt: str, max_selections: int = 3) -> List[str]:
        print(f"\n{prompt}")
        print(f"(Select up to {max_selections}. Type 'list' to view movies, 'done' to finish.)")
        selected = []
        while len(selected) < max_selections:
            user_input = input(f"Selection ({len(selected)}/{max_selections}): ").strip().lower()
            if user_input == 'done':
                break
            if user_input == 'list':
                self._list_movies()
                continue
            try:
                nums = [int(x.strip()) for x in user_input.split(',') if x.strip().isdigit()]
                for n in nums:
                    if 1 <= n <= len(movies):
                        title = movies[n - 1]
                        if title not in selected:
                            selected.append(title)
                            print(f"Added: {title}")
                        else:
                            print(f"Already selected: {title}")
                    else:
                        print(f"Invalid number: {n}")
            except ValueError:
                print("Please enter numbers (e.g., 1,3) or 'list'/'done'.")
        return selected

    def _print_recommendations(self, recs: List[Tuple[str, float, str]]):
        print("\n" + "=" * 70)
        print("YOUR PERSONALIZED RECOMMENDATIONS")
        print("=" * 70)
        for i, (title, score, why) in enumerate(recs, 1):
            p = self.recommender.movie_profiles[title]
            print(f"\n{i}. {title.upper()}")
            print(f"   Match Score: {score:.3f}")
            print(f"   Why: {why}")
            if p.themes:
                print(f"   Themes: {', '.join(p.themes)}")
            if p.emotional_tone:
                print(f"   Mood: {', '.join(p.emotional_tone)}")
            if p.target_audience:
                print(f"   Target Audience: {p.target_audience}")
            print("-" * 70)

    def run(self):
        if self.matcher is None:
            return
        print("\n" + "=" * 70)
        print("WELCOME TO THE INDIE MOVIE RECOMMENDATION SYSTEM")
        print("=" * 70)
        all_movies = self._list_movies()
        liked = self._prompt_selection(all_movies, "Select 2–3 movies you absolutely love:", 3)
        if not liked:
            print("No selection made. Goodbye!")
            return
        print(f"\nYou selected: {', '.join(liked)}")
        print("\nGenerating recommendations...")
        recs = self.matcher.recommend_based_on_preferences(liked, top_n=5)
        if not recs:
            print("Sorry, no recommendations available.")
            return
        self._print_recommendations(recs)


def main():
    cli = InteractiveRecommenderCLI()
    cli.run()


if __name__ == "__main__":
    main()