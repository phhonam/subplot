"""
Evaluation API for Movie Profile Assessment

Provides REST API endpoints for the movie profile evaluation frontend.
"""

from flask import Flask, jsonify, request, render_template
import json
import os
from typing import Dict, Any, List
from llm_movie_evaluator import LLMJudge, GroundTruthGenerator, AutomatedEvaluationPipeline
from llm_validation_system import ValidationPipeline
import traceback


app = Flask(__name__)

# Global instances for evaluation
judge = None
ground_truth_generator = None
validation_pipeline = None
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


def initialize_evaluation_system():
    """Initialize the evaluation system components"""
    global judge, ground_truth_generator, validation_pipeline
    
    try:
        # Load environment variables
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        
        # Initialize components
        judge = LLMJudge(model="gpt-3.5-turbo", provider="openai")
        ground_truth_generator = GroundTruthGenerator(model="gpt-3.5-turbo", provider="openai")
        validation_pipeline = ValidationPipeline()
        
        print("Evaluation system initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing evaluation system: {e}")
        return False


@app.route('/')
def index():
    """Main evaluation dashboard"""
    return render_template('evaluation_dashboard.html')


@app.route('/debug')
def debug_dashboard():
    """Debug evaluation dashboard"""
    with open('debug_dashboard.html', 'r') as f:
        return f.read()


@app.route('/simple')
def simple_test():
    """Simple test page"""
    with open('simple_test.html', 'r') as f:
        return f.read()


@app.route('/dom-test')
def dom_test():
    """DOM test page"""
    with open('dom_test.html', 'r') as f:
        return f.read()


@app.route('/api/movies', methods=['GET'])
def get_movies():
    """Get list of all movies in the database"""
    try:
        # Ensure movie profiles are loaded
        global movie_profiles
        if not movie_profiles:
            load_movie_profiles()
        
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
        # Ensure movie profiles are loaded
        global movie_profiles
        if not movie_profiles:
            load_movie_profiles()
            
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
    """Generate ground truth and evaluate a movie profile"""
    try:
        # Ensure movie profiles are loaded
        global movie_profiles, judge, ground_truth_generator
        if not movie_profiles:
            load_movie_profiles()
        
        # Ensure evaluation components are initialized
        if not judge or not ground_truth_generator:
            initialize_evaluation_system()
            
        if movie_title not in movie_profiles:
            return jsonify({
                'success': False,
                'error': f'Movie "{movie_title}" not found'
            }), 404
        
        movie_data = movie_profiles[movie_title]
        
        # Generate ground truth
        print(f"Generating ground truth for {movie_title}...")
        ground_truth = ground_truth_generator.generate_reference_profile(movie_data)
        
        # Check if ground truth generation failed
        if "Unable to generate ground truth due to API error" in ground_truth:
            return jsonify({
                'success': False,
                'error': 'Failed to generate ground truth due to API error. Please try again later.'
            }), 503  # Service Unavailable
        
        # Extract generated profile text
        generated_profile = extract_profile_text(movie_data)
        
        # Debug: Print what we're actually evaluating
        print(f"DEBUG - Profile text being evaluated for {movie_title}:")
        print(f"'{generated_profile}'")
        print(f"DEBUG - Profile text length: {len(generated_profile)} characters")
        
        # Run evaluation
        print(f"Running evaluation for {movie_title}...")
        evaluation_result = judge.evaluate_profile(
            movie_title, generated_profile, ground_truth
        )
        
        # Check if evaluation failed
        if "Unable to complete evaluation due to API error" in str(evaluation_result.detailed_feedback):
            return jsonify({
                'success': False,
                'error': 'Failed to complete evaluation due to API error. Please try again later.'
            }), 503  # Service Unavailable
        
        # Format results
        result = {
            'movie_title': evaluation_result.movie_title,
            'overall_score': evaluation_result.overall_score,
            'category_scores': evaluation_result.category_scores,
            'detailed_feedback': evaluation_result.detailed_feedback,
            'ground_truth': ground_truth,
            'generated_profile': generated_profile
        }
        
        return jsonify({
            'success': True,
            'evaluation': result
        })
    except Exception as e:
        print(f"Error evaluating {movie_title}: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/batch-evaluate', methods=['POST'])
def batch_evaluate():
    """Evaluate multiple movies in batch"""
    try:
        data = request.get_json()
        movie_titles = data.get('movies', [])
        max_movies = min(len(movie_titles), 10)  # Limit to 10 movies for performance
        
        if not movie_titles:
            return jsonify({
                'success': False,
                'error': 'No movies specified'
            }), 400
        
        results = []
        # Ensure movie profiles are loaded
        global movie_profiles, judge, ground_truth_generator
        if not movie_profiles:
            load_movie_profiles()
        
        # Ensure evaluation components are initialized
        if not judge or not ground_truth_generator:
            initialize_evaluation_system()
            
        for i, movie_title in enumerate(movie_titles[:max_movies]):
            try:
                if movie_title not in movie_profiles:
                    continue
                
                movie_data = movie_profiles[movie_title]
                
                # Generate ground truth
                ground_truth = ground_truth_generator.generate_reference_profile(movie_data)
                generated_profile = extract_profile_text(movie_data)
                
                # Run evaluation
                evaluation_result = judge.evaluate_profile(
                    movie_title, generated_profile, ground_truth
                )
                
                results.append({
                    'movie_title': movie_title,
                    'overall_score': evaluation_result.overall_score,
                    'category_scores': evaluation_result.category_scores
                })
                
            except Exception as e:
                print(f"Error evaluating {movie_title}: {e}")
                continue
        
        # Calculate summary statistics
        if results:
            avg_score = sum(r['overall_score'] for r in results) / len(results)
            category_averages = {}
            for category in results[0]['category_scores'].keys():
                category_averages[category] = sum(
                    r['category_scores'][category] for r in results
                ) / len(results)
        else:
            avg_score = 0
            category_averages = {}
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total_evaluated': len(results),
                'average_score': avg_score,
                'category_averages': category_averages
            }
        })
    except Exception as e:
        print(f"Error in batch evaluation: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/validate-system', methods=['POST'])
def validate_evaluation_system():
    """Run validation tests on the evaluation system"""
    try:
        print("Running validation tests...")
        validation_results = validation_pipeline.run_full_validation(judge)
        
        return jsonify({
            'success': True,
            'validation': validation_results
        })
    except Exception as e:
        print(f"Error in validation: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def extract_profile_text(movie_data: Dict[str, Any]) -> str:
    """Extract ONLY the profile text from movie data (not the structured metadata)"""
    # Debug: Print what's in the movie_data
    print(f"DEBUG - Movie data keys: {list(movie_data.keys())}")
    if 'profile_text' in movie_data:
        print(f"DEBUG - Profile text found: '{movie_data['profile_text'][:100]}...'")
    else:
        print("DEBUG - No 'profile_text' key found in movie_data")
        print(f"DEBUG - Available keys: {list(movie_data.keys())}")
    
    # Return only the actual profile text, not the structured metadata
    return movie_data.get('profile_text', '')


if __name__ == '__main__':
    # Initialize the system
    print("Initializing Movie Profile Evaluation System...")
    
    if not load_movie_profiles():
        print("Failed to load movie profiles. Exiting.")
        exit(1)
    
    print("Movie profiles loaded. LLM components will initialize when needed.")
    print("Starting evaluation API server...")
    app.run(debug=True, host='0.0.0.0', port=5001)
