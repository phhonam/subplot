"""
Test script for the LLM-based movie profile evaluation system

This script demonstrates how to use the evaluation system with sample movie profiles
and provides examples of running evaluations, validations, and benchmarks.
"""

import json
import os
from typing import Dict, Any
from llm_movie_evaluator import LLMJudge, GroundTruthGenerator, AutomatedEvaluationPipeline
from llm_validation_system import ValidationPipeline


def load_sample_movies() -> Dict[str, Any]:
    """Load a small sample of movies for testing"""
    try:
        with open('movie_profiles_merged.json', 'r') as f:
            all_movies = json.load(f)
        
        # Select a diverse sample of well-known films for testing
        sample_titles = [
            "Citizen Kane",
            "The Godfather", 
            "Casablanca",
            "Pulp Fiction",
            "2001: A Space Odyssey"
        ]
        
        # Find movies that exist in our dataset
        sample_movies = {}
        for title in sample_titles:
            if title in all_movies:
                sample_movies[title] = all_movies[title]
        
        # If we don't have enough from our list, add some random ones
        if len(sample_movies) < 3:
            remaining_titles = [t for t in all_movies.keys() if t not in sample_movies]
            for title in remaining_titles[:3-len(sample_movies)]:
                sample_movies[title] = all_movies[title]
        
        return sample_movies
        
    except FileNotFoundError:
        print("movie_profiles_merged.json not found. Creating sample data...")
        return create_sample_data()


def create_sample_data() -> Dict[str, Any]:
    """Create sample movie data for testing when real data isn't available"""
    return {
        "Citizen Kane": {
            "title": "Citizen Kane",
            "year": "1941",
            "director": "Orson Welles",
            "genre_tags": ["Drama", "Mystery"],
            "plot_summary": "Newspaper magnate Charles Foster Kane is taken from his mother as a boy and made the ward of a rich industrialist. As a result, every well-meaning, tyrannical or self-destructive move he makes for the rest of his life appears in some way to be a reaction to that deeply wounding event.",
            "primary_emotional_tone": "dramatic",
            "secondary_emotional_tone": "contemplative",
            "primary_theme": "identity_crisis",
            "secondary_theme": "media_manipulation",
            "intensity_level": "high",
            "pacing_style": "steady unraveling",
            "visual_aesthetic": "Deep focus cinematography, chiaroscuro lighting, innovative camera angles",
            "target_audience": "Film enthusiasts interested in character studies and cinematic innovation",
            "similar_films": ["The Social Network", "All the President's Men", "The Insider"],
            "cultural_context": ["Rise of media empires", "power of press in shaping public opinion"],
            "narrative_structure": "Non-linear narrative with multiple perspectives",
            "energy_level": "Intellectually stimulating",
            "discussion_topics": ["Identity construction in media", "ethical implications of journalism", "the nature of truth and perception", "the price of ambition"],
            "profile_text": "Citizen Kane stands as a cornerstone of cinematic history, captivates with its innovative storytelling techniques and deep psychological exploration. Orson Welles' directorial virtuosity shines through the intricate narrative structure and visually striking compositions."
        },
        "Pulp Fiction": {
            "title": "Pulp Fiction",
            "year": "1994",
            "director": "Quentin Tarantino",
            "genre_tags": ["Crime", "Drama"],
            "plot_summary": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
            "primary_emotional_tone": "tense",
            "secondary_emotional_tone": "dark",
            "primary_theme": "moral_ambiguity",
            "secondary_theme": "redemption",
            "intensity_level": "high",
            "pacing_style": "non-linear storytelling",
            "visual_aesthetic": "Stylized cinematography with bold colors and dynamic camera work",
            "target_audience": "Fans of crime dramas and postmodern storytelling",
            "similar_films": ["Reservoir Dogs", "The Usual Suspects", "Goodfellas"],
            "cultural_context": ["1990s independent film renaissance", "postmodern cinema"],
            "narrative_structure": "Non-linear interconnected stories",
            "energy_level": "High-octane and intellectually engaging",
            "discussion_topics": ["Moral complexity in crime", "redemption themes", "postmodern storytelling", "violence in cinema"],
            "profile_text": "Pulp Fiction revolutionized independent cinema with its non-linear narrative structure and bold exploration of moral ambiguity in the criminal underworld."
        }
    }


def test_basic_evaluation():
    """Test basic evaluation functionality"""
    print("=== Testing Basic Evaluation ===")
    
    # Load sample movies
    sample_movies = load_sample_movies()
    
    if not sample_movies:
        print("No sample movies available for testing")
        return
    
    # Initialize judge
    judge = LLMJudge(model="gpt-3.5-turbo", provider="openai")  # Use cheaper model for testing
    
    # Test with one movie
    movie_title = list(sample_movies.keys())[0]
    movie_data = sample_movies[movie_title]
    
    print(f"Testing evaluation with: {movie_title}")
    
    # Generate ground truth
    ground_truth_generator = GroundTruthGenerator(model="gpt-3.5-turbo", provider="openai")
    ground_truth = ground_truth_generator.generate_reference_profile(movie_data)
    
    # Extract generated profile
    generated_profile = extract_profile_text(movie_data)
    
    # Evaluate
    result = judge.evaluate_profile(movie_title, generated_profile, ground_truth)
    
    # Print results
    print(f"\nEvaluation Results for {movie_title}:")
    print(f"Overall Score: {result.overall_score:.2f}")
    print("\nCategory Scores:")
    for category, score in result.category_scores.items():
        print(f"  {category}: {score:.2f}")
    
    print("\nDetailed Feedback:")
    for category, feedback in result.detailed_feedback.items():
        print(f"  {category}: {feedback}")


def test_validation_system():
    """Test the validation system"""
    print("\n=== Testing Validation System ===")
    
    # Initialize validation pipeline
    validator = ValidationPipeline()
    
    # Initialize judge
    judge = LLMJudge(model="gpt-3.5-turbo", provider="openai")
    
    # Run validation (this will test against benchmark films)
    print("Running validation...")
    validation_results = validator.run_full_validation(judge)
    
    # Print results
    print("\nValidation Results:")
    benchmark = validation_results["benchmark_validation"]
    print(f"Overall Accuracy: {benchmark['overall_accuracy']:.2f}")
    print(f"Element Coverage: {benchmark['element_coverage']:.2f}")
    
    quality = validation_results["overall_judge_quality"]
    print(f"Overall Quality Score: {quality['overall_quality_score']:.2f}")
    print(f"Quality Rating: {quality['quality_rating']}")


def test_automated_pipeline():
    """Test the automated evaluation pipeline"""
    print("\n=== Testing Automated Pipeline ===")
    
    # Load sample movies
    sample_movies = load_sample_movies()
    
    if len(sample_movies) < 2:
        print("Need at least 2 movies for pipeline testing")
        return
    
    # Initialize pipeline
    pipeline = AutomatedEvaluationPipeline(
        judge_model="gpt-3.5-turbo",
        ground_truth_model="gpt-3.5-turbo"
    )
    
    # Run evaluation on small sample
    print("Running automated evaluation pipeline...")
    results = pipeline.evaluate_movie_profiles(sample_movies, sample_size=2)
    
    # Analyze results
    analysis = pipeline.analyze_results(results)
    
    print("\nPipeline Results:")
    print(f"Total evaluated: {analysis['total_evaluated']}")
    print(f"Overall average score: {analysis['overall_stats']['average']:.2f}")
    print(f"Score range: {analysis['overall_stats']['min']:.2f} - {analysis['overall_stats']['max']:.2f}")
    
    print("\nCategory Performance:")
    for category, stats in analysis['category_scores'].items():
        print(f"  {category}: {stats['average']:.2f} ± {stats['std']:.2f}")
    
    if analysis['weak_categories']:
        print(f"\nAreas needing improvement: {', '.join(analysis['weak_categories'])}")


def extract_profile_text(movie_data: Dict[str, Any]) -> str:
    """Extract profile text from movie data"""
    profile_parts = []
    
    # Add key profile fields
    if movie_data.get('primary_emotional_tone'):
        profile_parts.append(f"Primary emotional tone: {movie_data['primary_emotional_tone']}")
    if movie_data.get('secondary_emotional_tone'):
        profile_parts.append(f"Secondary emotional tone: {movie_data['secondary_emotional_tone']}")
    if movie_data.get('primary_theme'):
        profile_parts.append(f"Primary theme: {movie_data['primary_theme']}")
    if movie_data.get('secondary_theme'):
        profile_parts.append(f"Secondary theme: {movie_data['secondary_theme']}")
    if movie_data.get('visual_aesthetic'):
        profile_parts.append(f"Visual aesthetic: {movie_data['visual_aesthetic']}")
    if movie_data.get('cultural_context'):
        profile_parts.append(f"Cultural context: {', '.join(movie_data['cultural_context'])}")
    if movie_data.get('narrative_structure'):
        profile_parts.append(f"Narrative structure: {movie_data['narrative_structure']}")
    if movie_data.get('discussion_topics'):
        profile_parts.append(f"Discussion topics: {', '.join(movie_data['discussion_topics'])}")
    if movie_data.get('profile_text'):
        profile_parts.append(f"Profile text: {movie_data['profile_text']}")
    
    return '\n'.join(profile_parts)


def check_api_keys():
    """Check if required API keys are available"""
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    print("=== API Key Check ===")
    print(f"OpenAI API Key: {'✓ Available' if openai_key else '✗ Missing'}")
    print(f"Anthropic API Key: {'✓ Available' if anthropic_key else '✗ Missing'}")
    
    if not openai_key and not anthropic_key:
        print("\n⚠️  Warning: No API keys found!")
        print("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variables")
        print("Example: export OPENAI_API_KEY='your-key-here'")
        return False
    
    return True


def main():
    """Main test function"""
    print("LLM Movie Profile Evaluation System - Test Suite")
    print("=" * 50)
    
    # Check API keys first
    if not check_api_keys():
        return
    
    try:
        # Test basic evaluation
        test_basic_evaluation()
        
        # Test validation system
        test_validation_system()
        
        # Test automated pipeline
        test_automated_pipeline()
        
        print("\n=== All Tests Completed ===")
        print("The evaluation system is ready for use!")
        
    except Exception as e:
        print(f"\nError during testing: {e}")
        print("Please check your API keys and internet connection")


if __name__ == "__main__":
    main()
