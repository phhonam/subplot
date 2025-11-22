#!/usr/bin/env python3
"""
Simple test version of the evaluation system - just movie browsing without LLM
"""

from flask import Flask, jsonify, request, render_template
import json
import os

app = Flask(__name__)

# Global movie profiles
movie_profiles = {}

def load_movie_profiles():
    """Load movie profiles from JSON file"""
    global movie_profiles
    try:
        with open('movie_profiles_merged.json', 'r') as f:
            movie_profiles = json.load(f)
        print(f"Loaded {len(movie_profiles)} movie profiles")
        return True
    except Exception as e:
        print(f"Error loading movie profiles: {e}")
        return False

@app.route('/')
def index():
    """Main evaluation dashboard"""
    return render_template('evaluation_dashboard.html')

@app.route('/api/movies', methods=['GET'])
def get_movies():
    """Get list of all movies in the database"""
    try:
        search_query = request.args.get('search', '').lower()
        
        if search_query:
            filtered_movies = {
                title: data for title, data in movie_profiles.items()
                if search_query in title.lower()
            }
        else:
            filtered_movies = movie_profiles
        
        # Return basic movie info for the dropdown
        movies_list = []
        for title, data in filtered_movies.items():
            movies_list.append({
                'title': title,
                'year': data.get('year', 'Unknown'),
                'director': data.get('director', 'Unknown'),
                'genres': data.get('genre_tags', [])
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
    """Get detailed profile for a specific movie"""
    try:
        if movie_title not in movie_profiles:
            return jsonify({
                'success': False,
                'error': f'Movie "{movie_title}" not found'
            }), 404
        
        movie_data = movie_profiles[movie_title]
        
        # Extract and format the profile
        profile = {
            'title': movie_data.get('title', movie_title),
            'year': movie_data.get('year', 'Unknown'),
            'director': movie_data.get('director', 'Unknown'),
            'genres': movie_data.get('genre_tags', []),
            'plot_summary': movie_data.get('plot_summary', ''),
            'primary_emotional_tone': movie_data.get('primary_emotional_tone', ''),
            'secondary_emotional_tone': movie_data.get('secondary_emotional_tone', ''),
            'primary_theme': movie_data.get('primary_theme', ''),
            'secondary_theme': movie_data.get('secondary_theme', ''),
            'intensity_level': movie_data.get('intensity_level', ''),
            'pacing_style': movie_data.get('pacing_style', ''),
            'visual_aesthetic': movie_data.get('visual_aesthetic', ''),
            'target_audience': movie_data.get('target_audience', ''),
            'similar_films': movie_data.get('similar_films', []),
            'cultural_context': movie_data.get('cultural_context', []),
            'narrative_structure': movie_data.get('narrative_structure', ''),
            'energy_level': movie_data.get('energy_level', ''),
            'discussion_topics': movie_data.get('discussion_topics', []),
            'card_description': movie_data.get('card_description', ''),
            'profile_text': movie_data.get('profile_text', ''),
            'poster_url': movie_data.get('poster_url', ''),
            'backdrop_url': movie_data.get('backdrop_url', '')
        }
        
        return jsonify({
            'success': True,
            'movie': profile
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/evaluate/<movie_title>', methods=['POST'])
def evaluate_movie(movie_title):
    """Mock evaluation endpoint - returns sample data"""
    try:
        if movie_title not in movie_profiles:
            return jsonify({
                'success': False,
                'error': f'Movie "{movie_title}" not found'
            }), 404
        
        # Return mock evaluation data
        mock_evaluation = {
            'movie_title': movie_title,
            'overall_score': 4.2,
            'category_scores': {
                'cinema_movement': 4.5,
                'socio_cultural': 4.0,
                'formal_analysis': 4.3,
                'narrative_analysis': 4.1,
                'distinctiveness': 4.2
            },
            'detailed_feedback': {
                'cinema_movement': 'Excellent identification of film movement and historical context.',
                'socio_cultural': 'Good cultural context but could include more specific historical details.',
                'formal_analysis': 'Strong technical analysis with good cinematography insights.',
                'narrative_analysis': 'Solid narrative structure analysis with character insights.',
                'distinctiveness': 'Well-identified unique qualities and cultural significance.'
            },
            'ground_truth': 'This is a sample ground truth profile for testing purposes. It would contain expert-level analysis of the film.',
            'generated_profile': 'This is the current generated profile from your system for comparison.'
        }
        
        return jsonify({
            'success': True,
            'evaluation': mock_evaluation
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🎬 Simple Movie Evaluation Test System")
    print("=" * 50)
    
    if not load_movie_profiles():
        print("Failed to load movie profiles. Exiting.")
        exit(1)
    
    print("✅ Movie profiles loaded successfully!")
    print("🚀 Starting simple test server on http://localhost:5001")
    print("📝 This version uses mock evaluation data (no LLM calls)")
    print()
    
    app.run(debug=False, host='0.0.0.0', port=5001)

