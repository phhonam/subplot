#!/usr/bin/env python3
"""
Golden Dataset Evaluation Script

Evaluates the current movie profile_text generator against 20 carefully selected
edge-case films using the LLM judge system. Compares results against ground truth
expectations and generates comprehensive reports.
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent.parent))

from llm_movie_evaluator import LLMJudge
from evaluation_api import extract_profile_text


class GoldenDatasetEvaluator:
    """Evaluates movie profiles against golden dataset expectations"""
    
    def __init__(self, model: str = "gpt-3.5-turbo", provider: str = "openai"):
        """Initialize the evaluator with LLM judge"""
        self.judge = LLMJudge(model=model, provider=provider)
        self.model = model
        self.provider = provider
        
        # Load environment variables
        self._load_env()
        
        # Initialize data containers
        self.golden_movies = {}
        self.ground_truth = {}
        self.movie_profiles = {}
        self.evaluation_results = {}
        
    def _load_env(self):
        """Load environment variables from .env file"""
        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            print("✅ Environment variables loaded")
        except FileNotFoundError:
            print("⚠️  No .env file found - make sure API keys are set in environment")
    
    def load_golden_movies(self, movies_file: str) -> Dict[str, Any]:
        """Load the 20 golden dataset movies from movies.json"""
        try:
            with open(movies_file, 'r') as f:
                data = json.load(f)
            
            self.golden_movies = {}
            for movie in data['golden_dataset']['movies']:
                title = movie['title']
                self.golden_movies[title] = movie
            
            print(f"✅ Loaded {len(self.golden_movies)} golden dataset movies")
            return self.golden_movies
        except Exception as e:
            print(f"❌ Error loading golden movies: {e}")
            return {}
    
    def load_ground_truth(self, ground_truth_file: str) -> Dict[str, Any]:
        """Load ground truth expectations from ground_truth.json"""
        try:
            with open(ground_truth_file, 'r') as f:
                self.ground_truth = json.load(f)
            
            print(f"✅ Loaded ground truth for {len(self.ground_truth['movies'])} movies")
            return self.ground_truth
        except Exception as e:
            print(f"❌ Error loading ground truth: {e}")
            return {}
    
    def load_current_profiles(self, profiles_file: str) -> Dict[str, Any]:
        """Load current movie profiles from movie_profiles_merged.json"""
        try:
            with open(profiles_file, 'r') as f:
                self.movie_profiles = json.load(f)
            
            print(f"✅ Loaded {len(self.movie_profiles)} movie profiles")
            return self.movie_profiles
        except Exception as e:
            print(f"❌ Error loading movie profiles: {e}")
            return {}
    
    def get_profile_text(self, title: str) -> str:
        """Extract profile_text for a given movie title"""
        if title in self.movie_profiles:
            movie_data = self.movie_profiles[title]
            return extract_profile_text(movie_data)
        else:
            print(f"⚠️  No profile found for: {title}")
            return ""
    
    def evaluate_movie(self, title: str, profile_text: str, ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single movie against ground truth expectations"""
        print(f"\n🎬 Evaluating: {title}")
        print(f"Profile text length: {len(profile_text)} characters")
        
        if not profile_text.strip():
            return {
                "title": title,
                "error": "No profile text found",
                "category_scores": {},
                "overall_score": 0.0,
                "detected_issues": ["No profile text available"],
                "improvement_suggestions": ["Generate profile text for this movie"]
            }
        
        try:
            # Use the LLM judge to evaluate the profile
            evaluation = self.judge.evaluate_profile(title, profile_text, "")
            
            # Analyze against ground truth expectations
            detected_issues = []
            improvement_suggestions = []
            
            # Check cinema movement identification
            expected_movement = ground_truth.get('expected_cinema_movement', '')
            if expected_movement and expected_movement.lower() not in profile_text.lower():
                detected_issues.append(f"Missing cinema movement: {expected_movement}")
                improvement_suggestions.append(f"Should identify {expected_movement}")
            
            # Check technical credits
            expected_credits = ground_truth.get('expected_technical_credits', [])
            missing_credits = []
            for credit in expected_credits:
                if credit.lower() not in profile_text.lower():
                    missing_credits.append(credit)
            
            if missing_credits:
                detected_issues.append(f"Missing technical credits: {', '.join(missing_credits)}")
                improvement_suggestions.append("Include specific cinematographer names and techniques")
            
            # Check historical context
            expected_context = ground_truth.get('expected_historical_context', [])
            missing_context = []
            for context in expected_context:
                if context.lower() not in profile_text.lower():
                    missing_context.append(context)
            
            if missing_context:
                detected_issues.append(f"Missing historical context: {', '.join(missing_context)}")
                improvement_suggestions.append("Include specific historical periods and events")
            
            # Check for generic language
            generic_terms = ['beautiful', 'stunning', 'amazing', 'incredible', 'wonderful']
            found_generic = [term for term in generic_terms if term in profile_text.lower()]
            if found_generic:
                detected_issues.append(f"Generic language detected: {', '.join(found_generic)}")
                improvement_suggestions.append("Replace generic adjectives with specific technical terms")
            
            return {
                "title": title,
                "category_scores": evaluation.category_scores,
                "overall_score": evaluation.overall_score,
                "detected_issues": detected_issues,
                "improvement_suggestions": improvement_suggestions,
                "profile_text_preview": profile_text[:200] + "..." if len(profile_text) > 200 else profile_text
            }
            
        except Exception as e:
            print(f"❌ Error evaluating {title}: {e}")
            return {
                "title": title,
                "error": str(e),
                "category_scores": {},
                "overall_score": 0.0,
                "detected_issues": [f"Evaluation error: {str(e)}"],
                "improvement_suggestions": ["Fix evaluation system error"]
            }
    
    def evaluate_all_movies(self) -> Dict[str, Any]:
        """Evaluate all movies in the golden dataset"""
        print(f"\n🚀 Starting evaluation of {len(self.ground_truth['movies'])} movies...")
        
        results = {}
        total_score = 0.0
        movie_count = 0
        
        for movie_key, ground_truth in self.ground_truth['movies'].items():
            # Get the actual title to look up in profiles
            actual_title = ground_truth.get('replacement_title') or ground_truth.get('original_title')
            
            # Get profile text
            profile_text = self.get_profile_text(actual_title)
            
            # Evaluate the movie
            result = self.evaluate_movie(actual_title, profile_text, ground_truth)
            results[movie_key] = result
            
            if result['overall_score'] > 0:
                total_score += result['overall_score']
                movie_count += 1
        
        # Calculate overall statistics
        overall_stats = {
            "average_score": total_score / movie_count if movie_count > 0 else 0.0,
            "movies_evaluated": movie_count,
            "movies_with_profiles": movie_count,
            "movies_missing": len(self.ground_truth['movies']) - movie_count
        }
        
        # Calculate category averages
        category_totals = {}
        category_counts = {}
        
        for result in results.values():
            if 'category_scores' in result:
                for category, score in result['category_scores'].items():
                    if category not in category_totals:
                        category_totals[category] = 0.0
                        category_counts[category] = 0
                    
                    if score > 0:
                        category_totals[category] += score
                        category_counts[category] += 1
        
        category_averages = {}
        for category in category_totals:
            if category_counts[category] > 0:
                category_averages[category] = category_totals[category] / category_counts[category]
            else:
                category_averages[category] = 0.0
        
        overall_stats['category_averages'] = category_averages
        
        return {
            "evaluation_date": datetime.now().isoformat(),
            "model_used": self.model,
            "provider_used": self.provider,
            "overall_stats": overall_stats,
            "results": results
        }
    
    def generate_json_report(self, results: Dict[str, Any], output_file: str):
        """Generate detailed JSON report"""
        try:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"✅ JSON report saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving JSON report: {e}")
    
    def generate_markdown_report(self, results: Dict[str, Any], output_file: str):
        """Generate human-readable markdown report"""
        try:
            stats = results['overall_stats']
            
            report = f"""# Golden Dataset LLM Evaluation Report

## Executive Summary

**Evaluation Date**: {results['evaluation_date']}  
**Model Used**: {results['model_used']} ({results['provider_used']})  
**Movies Evaluated**: {stats['movies_evaluated']}  
**Overall Average Score**: {stats['average_score']:.2f}/5.0  

## Overall Statistics

- **Movies with Profiles**: {stats['movies_with_profiles']}
- **Movies Missing**: {stats['movies_missing']}
- **Success Rate**: {(stats['movies_with_profiles'] / len(self.ground_truth['movies']) * 100):.1f}%

## Category Performance

"""
            
            # Add category averages
            for category, avg_score in stats['category_averages'].items():
                report += f"- **{category.replace('_', ' ').title()}**: {avg_score:.2f}/5.0\n"
            
            report += f"""

## Detailed Results

"""
            
            # Add results for each movie
            for movie_key, result in results['results'].items():
                ground_truth = self.ground_truth['movies'][movie_key]
                category = ground_truth.get('category', 'Unknown')
                
                report += f"""### {result['title']}
**Category**: {category}  
**Overall Score**: {result['overall_score']:.2f}/5.0  

**Category Scores**:
"""
                
                for cat, score in result.get('category_scores', {}).items():
                    report += f"- {cat.replace('_', ' ').title()}: {score:.2f}/5.0\n"
                
                if result.get('detected_issues'):
                    report += "\n**Issues Detected**:\n"
                    for issue in result['detected_issues']:
                        report += f"- {issue}\n"
                
                if result.get('improvement_suggestions'):
                    report += "\n**Improvement Suggestions**:\n"
                    for suggestion in result['improvement_suggestions']:
                        report += f"- {suggestion}\n"
                
                if 'error' in result:
                    report += f"\n**Error**: {result['error']}\n"
                
                report += "\n---\n\n"
            
            # Add summary of common issues
            all_issues = []
            for result in results['results'].values():
                all_issues.extend(result.get('detected_issues', []))
            
            if all_issues:
                from collections import Counter
                issue_counts = Counter(all_issues)
                
                report += """## Common Issues Summary

"""
                for issue, count in issue_counts.most_common(10):
                    report += f"- **{issue}**: {count} occurrences\n"
            
            # Add recommendations
            report += """
## Recommendations

Based on the evaluation results, here are key recommendations for improving the movie profile generator:

1. **Include Specific Cinema Movements**: Many profiles miss identifying specific cinema movements (e.g., "French New Wave", "Italian Neorealism")

2. **Mention Technical Credits**: Include cinematographer names and specific techniques (e.g., "deep focus", "handheld camera")

3. **Add Historical Context**: Reference specific historical periods and events that influenced the film

4. **Avoid Generic Language**: Replace vague terms like "beautiful" with specific technical descriptions

5. **Include Cultural Specificity**: Provide culturally specific context beyond generic descriptions

6. **Reference Narrative Innovations**: Mention specific narrative techniques and structural innovations

## Conclusion

This evaluation provides a baseline assessment of the current movie profile generator against challenging edge-case films. The results highlight specific areas for improvement in prompt engineering and profile generation.
"""
            
            with open(output_file, 'w') as f:
                f.write(report)
            
            print(f"✅ Markdown report saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error saving markdown report: {e}")


def main():
    """Main execution function"""
    print("🎬 Golden Dataset LLM Evaluation")
    print("=" * 50)
    
    # Initialize evaluator
    evaluator = GoldenDatasetEvaluator()
    
    # Load data
    print("\n📁 Loading data...")
    
    # Load golden movies
    movies_file = "prompt_engineering/golden_dataset/movies.json"
    evaluator.load_golden_movies(movies_file)
    
    # Load ground truth
    ground_truth_file = "prompt_engineering/golden_dataset/ground_truth.json"
    evaluator.load_ground_truth(ground_truth_file)
    
    # Load current profiles
    profiles_file = "movie_profiles_merged.json"
    evaluator.load_current_profiles(profiles_file)
    
    # Run evaluation
    print("\n🔍 Running evaluation...")
    results = evaluator.evaluate_all_movies()
    
    # Generate reports
    print("\n📊 Generating reports...")
    
    # JSON report
    json_output = "prompt_engineering/golden_dataset/llm_evaluation_results.json"
    evaluator.generate_json_report(results, json_output)
    
    # Markdown report
    md_output = "prompt_engineering/golden_dataset/llm_evaluation_report.md"
    evaluator.generate_markdown_report(results, md_output)
    
    print("\n✅ Evaluation complete!")
    print(f"📈 Overall average score: {results['overall_stats']['average_score']:.2f}/5.0")
    print(f"📝 Reports saved to: {json_output} and {md_output}")


if __name__ == "__main__":
    main()
