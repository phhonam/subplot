#!/usr/bin/env python3
"""
Test script to preview backdrop images from TMDB.
This will show you what backdrops look like before running the full enhancement.
"""

import json
import os
import requests
from typing import Dict, List, Any, Optional


def load_env_from_dotenv(dotenv_path: str = ".env") -> None:
    """Load environment variables from .env file"""
    if not os.path.exists(dotenv_path):
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v and k not in os.environ:
                os.environ[k] = v


def get_tmdb_backdrops(tmdb_id: int, api_key: str) -> List[Dict[str, Any]]:
    """
    Get all available backdrops for a movie from TMDB.

    Args:
        tmdb_id: TMDB movie ID
        api_key: TMDB API key

    Returns:
        List of backdrop objects with URLs and metadata
    """
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/images"
    params = {"api_key": api_key}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        backdrops = []
        for backdrop in data.get("backdrops", []):
            if backdrop.get("file_path"):
                backdrops.append({
                    "file_path": backdrop["file_path"],
                    "width": backdrop.get("width"),
                    "height": backdrop.get("height"),
                    "aspect_ratio": backdrop.get("aspect_ratio"),
                    "vote_average": backdrop.get("vote_average", 0),
                    "vote_count": backdrop.get("vote_count", 0),
                    "urls": {
                        "w300": f"https://image.tmdb.org/t/p/w300{backdrop['file_path']}",
                        "w780": f"https://image.tmdb.org/t/p/w780{backdrop['file_path']}",
                        "w1280": f"https://image.tmdb.org/t/p/w1280{backdrop['file_path']}",
                        "original": f"https://image.tmdb.org/t/p/original{backdrop['file_path']}"
                    }
                })

        # Sort by vote average (best first)
        backdrops.sort(key=lambda x: x["vote_average"], reverse=True)
        return backdrops

    except requests.RequestException as e:
        print(f"Error fetching backdrops for TMDB ID {tmdb_id}: {e}")
        return []


def test_backdrops():
    """Test backdrop fetching with sample movies"""

    # Load environment
    load_env_from_dotenv()
    api_key = os.environ.get("TMDB_API_KEY")

    if not api_key:
        print("❌ TMDB_API_KEY not found in environment")
        print("Please set your TMDB API key in .env file")
        return

    # Test movies from your dataset
    test_movies = [
        {"title": "The Godfather", "tmdb_id": 238, "year": "1972"},
        {"title": "Citizen Kane", "tmdb_id": 15, "year": "1941"},
        {"title": "Casablanca", "tmdb_id": 289, "year": "1943"},
        {"title": "The Matrix", "tmdb_id": 603, "year": "1999"},
        {"title": "Pulp Fiction", "tmdb_id": 680, "year": "1994"}
    ]

    print("🎬 Testing backdrop fetching...")
    print("=" * 60)

    for movie in test_movies:
        print(f"\n�� {movie['title']} ({movie['year']})")
        print(f"   TMDB ID: {movie['tmdb_id']}")

        backdrops = get_tmdb_backdrops(movie['tmdb_id'], api_key)

        if backdrops:
            print(f"   ✅ Found {len(backdrops)} backdrops")

            # Show top 3 backdrops
            for i, backdrop in enumerate(backdrops[:3]):
                print(f"   📷 Backdrop {i + 1}:")
                print(f"      Rating: {backdrop['vote_average']:.1f}/10 ({backdrop['vote_count']} votes)")
                print(f"      Size: {backdrop['width']}x{backdrop['height']}")
                print(f"      Aspect: {backdrop['aspect_ratio']:.2f}")
                print(f"      URL: {backdrop['urls']['w1280']}")

                # Test if image is accessible
                try:
                    response = requests.head(backdrop['urls']['w1280'], timeout=5)
                    if response.status_code == 200:
                        print(f"      ✅ Image accessible")
                    else:
                        print(f"      ⚠️  Image not accessible (status: {response.status_code})")
                except requests.RequestException as e:
                    print(f"      ❌ Error checking image: {e}")
        else:
            print(f"   ❌ No backdrops found")

        print()

    print("=" * 60)
    print("🎉 Backdrop test complete!")
    print("\n💡 Next steps:")
    print("1. If backdrops look good, run the full enhancement script")
    print("2. Use w1280 size for hero images, w780 for cards")
    print("3. Consider the vote_average for quality selection")


if __name__ == "__main__":
    test_backdrops()