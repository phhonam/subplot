#!/usr/bin/env python3
"""
Human Evaluation Interface for Movie Profile Text
Web interface for evaluating profile_text quality with structured ratings and annotation tools
"""

from flask import Flask, render_template, jsonify, request
import json
from pathlib import Path

app = Flask(__name__, template_folder='../templates')

# Global data
golden_profiles = {}
golden_movies = []

def load_data():
    """Load golden dataset and profiles"""
    global golden_profiles, golden_movies
    
    # Load golden dataset movies
    golden_dataset_path = Path("/Users/nam/movie-recommender/prompt_engineering/golden_dataset/movies.json")
    with open(golden_dataset_path, 'r') as f:
        dataset_data = json.load(f)
        golden_movies = dataset_data["golden_dataset"]["movies"]
    
    # Load generated profiles
    profiles_path = Path("/Users/nam/movie-recommender/prompt_engineering/golden_dataset/generated_profiles_v1.0.json")
    with open(profiles_path, 'r') as f:
        profiles_data = json.load(f)
        golden_profiles = profiles_data["profiles"]

@app.route('/')
def index():
    """Main evaluation interface"""
    return render_template('human_eval_interface.html')

@app.route('/api/movies', methods=['GET'])
def get_movies():
    """Get list of movies available for evaluation"""
    try:
        movies_list = []
        
        for movie in golden_movies:
            title = movie["title"]
            if title in golden_profiles:
                profile = golden_profiles[title]
                movies_list.append({
                    'title': title,
                    'year': movie["year"],
                    'director': movie["director"],
                    'country': movie["country"],
                    'category': movie["category"],
                    'key_challenges': movie["key_challenges"],
                    'has_profile': True
                })
            else:
                movies_list.append({
                    'title': title,
                    'year': movie["year"],
                    'director': movie["director"],
                    'country': movie["country"],
                    'category': movie["category"],
                    'key_challenges': movie["key_challenges"],
                    'has_profile': False
                })
        
        # Sort by title
        movies_list.sort(key=lambda x: x['title'])
        
        return jsonify({
            'success': True,
            'movies': movies_list,
            'total': len(movies_list)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/movie/<movie_title>', methods=['GET'])
def get_movie_profile(movie_title):
    """Get movie profile for evaluation"""
    try:
        # Find movie info
        movie_info = None
        for movie in golden_movies:
            if movie["title"] == movie_title:
                movie_info = movie
                break
        
        if not movie_info:
            return jsonify({
                'success': False,
                'error': f'Movie "{movie_title}" not found in golden dataset'
            }), 404
        
        # Get profile text if available
        profile_text = ""
        if movie_title in golden_profiles:
            profile_text = golden_profiles[movie_title]["profile_text"]
        
        return jsonify({
            'success': True,
            'movie': {
                'title': movie_info["title"],
                'year': movie_info["year"],
                'director': movie_info["director"],
                'country': movie_info["country"],
                'category': movie_info["category"],
                'key_challenges': movie_info["key_challenges"],
                'profile_text': profile_text,
                'has_profile': movie_title in golden_profiles
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/evaluate', methods=['POST'])
def submit_evaluation():
    """Submit human evaluation results"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['movie_title', 'overall_quality', 'category_ratings', 'comments']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        # Save evaluation results
        eval_results_path = Path("/Users/nam/movie-recommender/prompt_engineering/golden_dataset/human_evaluations")
        eval_results_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing results or create new
        results_file = eval_results_path / "batch_1_results.json"
        if results_file.exists():
            with open(results_file, 'r') as f:
                results = json.load(f)
        else:
            results = {
                "evaluations": [],
                "metadata": {
                    "created_date": "2025-10-18",
                    "version": "v1.0",
                    "total_evaluations": 0
                }
            }
        
        # Add new evaluation
        results["evaluations"].append(data)
        results["metadata"]["total_evaluations"] = len(results["evaluations"])
        
        # Save updated results
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Evaluation submitted successfully',
            'total_evaluations': results["metadata"]["total_evaluations"]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/evaluations', methods=['GET'])
def get_evaluations():
    """Get all submitted evaluations"""
    try:
        results_file = Path("/Users/nam/movie-recommender/prompt_engineering/golden_dataset/human_evaluations/batch_1_results.json")
        
        if results_file.exists():
            with open(results_file, 'r') as f:
                results = json.load(f)
        else:
            results = {
                "evaluations": [],
                "metadata": {
                    "created_date": "2025-10-18",
                    "version": "v1.0",
                    "total_evaluations": 0
                }
            }
        
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🎬 Human Evaluation Interface for Movie Profile Text")
    print("=" * 60)
    
    # Load data
    load_data()
    print(f"✅ Loaded {len(golden_movies)} movies from golden dataset")
    print(f"✅ Loaded {len(golden_profiles)} profile texts")
    
    print("🚀 Starting human evaluation interface...")
    print("   - Interface: http://localhost:5002")
    print("   - Press Ctrl+C to stop")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5002)
