"""
Ground Truth Validation Script

This script validates the quality of LLM-generated ground truth by testing against
known benchmark films with expert-validated information.
"""

import json
import os
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from llm_movie_evaluator import GroundTruthGenerator
import re


@dataclass
class ValidationResult:
    """Results from validating ground truth against benchmark data"""
    movie_title: str
    factual_accuracy: float
    key_elements_found: List[str]
    key_elements_missing: List[str]
    factual_errors: List[str]
    overall_quality_score: float
    ground_truth_text: str


class GroundTruthValidator:
    """Validates LLM-generated ground truth against benchmark data"""
    
    def __init__(self, model: str = "gpt-4", provider: str = "openai"):
        self.generator = GroundTruthGenerator(model=model, provider=provider)
        
        # Benchmark films with expert-validated information
        self.benchmark_films = {
            "Citizen Kane": {
                "director": "Orson Welles",
                "year": "1941",
                "genres": ["Drama", "Mystery"],
                "movement": "Classical Hollywood",
                "key_elements": [
                    "deep focus cinematography",
                    "non-linear narrative",
                    "media power themes",
                    "Orson Welles",
                    "1941",
                    "cinematic innovation",
                    "Rosebud",
                    "multiple perspectives",
                    "Gregg Toland",
                    "chiaroscuro lighting"
                ],
                "cultural_context": [
                    "Pre-war America",
                    "media empire rise",
                    "Hearst controversy",
                    "journalism power"
                ],
                "technical_innovations": [
                    "deep focus",
                    "low angle shots",
                    "mise-en-scène",
                    "long takes"
                ]
            },
            "Breathless": {
                "director": "Jean-Luc Godard",
                "year": "1960",
                "genres": ["Crime", "Drama"],
                "movement": "French New Wave",
                "key_elements": [
                    "French New Wave",
                    "jump cuts",
                    "handheld camera",
                    "Jean-Luc Godard",
                    "1960",
                    "cinematic revolution",
                    "natural lighting",
                    "improvised dialogue",
                    "New Wave techniques",
                    "Paris setting"
                ],
                "cultural_context": [
                    "1960s French cinema revolution",
                    "Cahiers du Cinéma",
                    "auteur theory",
                    "youth culture"
                ],
                "technical_innovations": [
                    "jump cuts",
                    "handheld cinematography",
                    "natural lighting",
                    "location shooting"
                ]
            },
            "Bicycle Thieves": {
                "director": "Vittorio De Sica",
                "year": "1948",
                "genres": ["Drama"],
                "movement": "Italian Neorealism",
                "key_elements": [
                    "Italian Neorealism",
                    "non-professional actors",
                    "location shooting",
                    "Vittorio De Sica",
                    "1948",
                    "post-war Italy",
                    "social realism",
                    "working class",
                    "Rome",
                    "economic struggle"
                ],
                "cultural_context": [
                    "Post-WWII Italian society",
                    "economic devastation",
                    "working class struggles",
                    "social realism movement"
                ],
                "technical_innovations": [
                    "non-professional actors",
                    "location shooting",
                    "documentary style",
                    "natural lighting"
                ]
            },
            "Pulp Fiction": {
                "director": "Quentin Tarantino",
                "year": "1994",
                "genres": ["Crime", "Drama"],
                "movement": "Independent Cinema Revival",
                "key_elements": [
                    "non-linear structure",
                    "Quentin Tarantino",
                    "1994",
                    "postmodern",
                    "moral ambiguity",
                    "pop culture references",
                    "interconnected stories",
                    "crime genre subversion",
                    "Miramax",
                    "independent cinema"
                ],
                "cultural_context": [
                    "1990s independent film boom",
                    "postmodern cinema",
                    "Miramax era",
                    "pop culture saturation"
                ],
                "technical_innovations": [
                    "non-linear storytelling",
                    "pop culture integration",
                    "dialogue-driven scenes",
                    "genre mixing"
                ]
            },
            "Do the Right Thing": {
                "director": "Spike Lee",
                "year": "1989",
                "genres": ["Drama"],
                "movement": "Independent Social Cinema",
                "key_elements": [
                    "Spike Lee",
                    "1989",
                    "racial tensions",
                    "police brutality",
                    "Howard Beach",
                    "Brooklyn",
                    "social commentary",
                    "civil unrest",
                    "Bedford-Stuyvesant",
                    "racial injustice"
                ],
                "cultural_context": [
                    "Late 1980s racial tensions",
                    "post-Reagan era",
                    "urban America",
                    "police-community relations"
                ],
                "technical_innovations": [
                    "social realism",
                    "documentary style",
                    "location shooting",
                    "ensemble cast"
                ]
            }
        }
    
    def validate_ground_truth(self, movie_title: str) -> ValidationResult:
        """Validate ground truth for a specific movie"""
        if movie_title not in self.benchmark_films:
            raise ValueError(f"No benchmark data available for {movie_title}")
        
        benchmark_data = self.benchmark_films[movie_title]
        
        print(f"Validating ground truth for: {movie_title}")
        
        # Create movie data for ground truth generation
        movie_data = {
            "title": movie_title,
            "director": benchmark_data["director"],
            "year": benchmark_data["year"],
            "genre_tags": benchmark_data["genres"],
            "plot_summary": f"Plot summary for {movie_title}"  # Simplified for testing
        }
        
        # Generate ground truth
        print("  Generating ground truth...")
        ground_truth_text = self.generator.generate_reference_profile(movie_data)
        
        # Validate against benchmark data
        print("  Validating against benchmark data...")
        factual_accuracy = self._calculate_factual_accuracy(ground_truth_text, benchmark_data)
        key_elements_found = self._find_key_elements(ground_truth_text, benchmark_data["key_elements"])
        key_elements_missing = [
            element for element in benchmark_data["key_elements"] 
            if element not in key_elements_found
        ]
        factual_errors = self._find_factual_errors(ground_truth_text, benchmark_data)
        
        # Calculate overall quality score
        overall_quality_score = self._calculate_overall_quality(
            factual_accuracy, len(key_elements_found), len(key_elements_missing), len(factual_errors)
        )
        
        return ValidationResult(
            movie_title=movie_title,
            factual_accuracy=factual_accuracy,
            key_elements_found=key_elements_found,
            key_elements_missing=key_elements_missing,
            factual_errors=factual_errors,
            overall_quality_score=overall_quality_score,
            ground_truth_text=ground_truth_text
        )
    
    def _calculate_factual_accuracy(self, ground_truth: str, benchmark_data: Dict[str, Any]) -> float:
        """Calculate factual accuracy score"""
        gt_lower = ground_truth.lower()
        correct_facts = 0
        total_facts = 0
        
        # Check director
        total_facts += 1
        if benchmark_data["director"].lower() in gt_lower:
            correct_facts += 1
        
        # Check year
        total_facts += 1
        if benchmark_data["year"] in ground_truth:
            correct_facts += 1
        
        # Check movement
        total_facts += 1
        if benchmark_data["movement"].lower() in gt_lower:
            correct_facts += 1
        
        # Check genres (at least one should be mentioned)
        total_facts += 1
        if any(genre.lower() in gt_lower for genre in benchmark_data["genres"]):
            correct_facts += 1
        
        return correct_facts / total_facts if total_facts > 0 else 0.0
    
    def _find_key_elements(self, ground_truth: str, key_elements: List[str]) -> List[str]:
        """Find which key elements are mentioned in the ground truth"""
        gt_lower = ground_truth.lower()
        found_elements = []
        
        for element in key_elements:
            if element.lower() in gt_lower:
                found_elements.append(element)
        
        return found_elements
    
    def _find_factual_errors(self, ground_truth: str, benchmark_data: Dict[str, Any]) -> List[str]:
        """Find factual errors in the ground truth"""
        errors = []
        gt_lower = ground_truth.lower()
        
        # Check for incorrect director
        if benchmark_data["director"].lower() not in gt_lower:
            errors.append(f"Director not mentioned or incorrect: expected {benchmark_data['director']}")
        
        # Check for incorrect year
        if benchmark_data["year"] not in ground_truth:
            errors.append(f"Year not mentioned or incorrect: expected {benchmark_data['year']}")
        
        # Check for incorrect movement
        if benchmark_data["movement"].lower() not in gt_lower:
            errors.append(f"Movement not mentioned or incorrect: expected {benchmark_data['movement']}")
        
        return errors
    
    def _calculate_overall_quality(self, factual_accuracy: float, elements_found: int, 
                                 elements_missing: int, errors: int) -> float:
        """Calculate overall quality score"""
        # Weight different factors
        factual_weight = 0.4
        elements_weight = 0.4
        errors_weight = 0.2
        
        # Calculate elements score (more found = better)
        total_elements = elements_found + elements_missing
        elements_score = elements_found / total_elements if total_elements > 0 else 0.0
        
        # Calculate errors penalty (fewer errors = better)
        errors_score = max(0, 1 - (errors * 0.2))  # Each error reduces score by 0.2
        
        overall_score = (
            factual_accuracy * factual_weight +
            elements_score * elements_weight +
            errors_score * errors_weight
        )
        
        return min(1.0, overall_score)  # Cap at 1.0
    
    def validate_all_benchmarks(self) -> List[ValidationResult]:
        """Validate ground truth for all benchmark films"""
        results = []
        
        for movie_title in self.benchmark_films.keys():
            try:
                result = self.validate_ground_truth(movie_title)
                results.append(result)
            except Exception as e:
                print(f"Error validating {movie_title}: {e}")
                continue
        
        return results
    
    def generate_validation_report(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Generate a comprehensive validation report"""
        if not results:
            return {"error": "No validation results to analyze"}
        
        # Calculate aggregate statistics
        factual_accuracies = [r.factual_accuracy for r in results]
        quality_scores = [r.overall_quality_score for r in results]
        
        avg_factual_accuracy = sum(factual_accuracies) / len(factual_accuracies)
        avg_quality_score = sum(quality_scores) / len(quality_scores)
        
        # Find best and worst performers
        best_result = max(results, key=lambda r: r.overall_quality_score)
        worst_result = min(results, key=lambda r: r.overall_quality_score)
        
        # Analyze common issues
        all_missing_elements = []
        all_errors = []
        
        for result in results:
            all_missing_elements.extend(result.key_elements_missing)
            all_errors.extend(result.factual_errors)
        
        # Count most common missing elements
        from collections import Counter
        common_missing = Counter(all_missing_elements).most_common(5)
        common_errors = Counter(all_errors).most_common(5)
        
        return {
            "summary": {
                "total_films_validated": len(results),
                "average_factual_accuracy": avg_factual_accuracy,
                "average_quality_score": avg_quality_score,
                "best_performer": {
                    "movie": best_result.movie_title,
                    "score": best_result.overall_quality_score
                },
                "worst_performer": {
                    "movie": worst_result.movie_title,
                    "score": worst_result.overall_quality_score
                }
            },
            "common_issues": {
                "most_missing_elements": common_missing,
                "most_common_errors": common_errors
            },
            "individual_results": results
        }


def print_validation_report(report: Dict[str, Any]):
    """Print a formatted validation report"""
    print("\n" + "="*60)
    print("GROUND TRUTH VALIDATION REPORT")
    print("="*60)
    
    summary = report["summary"]
    print(f"\nSUMMARY:")
    print(f"  Total films validated: {summary['total_films_validated']}")
    print(f"  Average factual accuracy: {summary['average_factual_accuracy']:.2f}")
    print(f"  Average quality score: {summary['average_quality_score']:.2f}")
    
    print(f"\nBEST PERFORMER:")
    print(f"  {summary['best_performer']['movie']}: {summary['best_performer']['score']:.2f}")
    
    print(f"\nWORST PERFORMER:")
    print(f"  {summary['worst_performer']['movie']}: {summary['worst_performer']['score']:.2f}")
    
    common_issues = report["common_issues"]
    if common_issues["most_missing_elements"]:
        print(f"\nMOST COMMONLY MISSING ELEMENTS:")
        for element, count in common_issues["most_missing_elements"]:
            print(f"  {element}: {count} films")
    
    if common_issues["most_common_errors"]:
        print(f"\nMOST COMMON ERRORS:")
        for error, count in common_issues["most_common_errors"]:
            print(f"  {error}: {count} films")
    
    print(f"\nDETAILED RESULTS:")
    for result in report["individual_results"]:
        print(f"\n  {result.movie_title}:")
        print(f"    Factual Accuracy: {result.factual_accuracy:.2f}")
        print(f"    Quality Score: {result.overall_quality_score:.2f}")
        print(f"    Key Elements Found: {len(result.key_elements_found)}/{len(result.key_elements_found) + len(result.key_elements_missing)}")
        
        if result.key_elements_missing:
            print(f"    Missing Elements: {', '.join(result.key_elements_missing[:3])}{'...' if len(result.key_elements_missing) > 3 else ''}")
        
        if result.factual_errors:
            print(f"    Errors: {', '.join(result.factual_errors)}")


def load_env_file():
    """Load environment variables from .env file"""
    env_file = '.env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Loaded environment variables from .env file")
    else:
        print("⚠️  No .env file found")


def main():
    """Main validation function"""
    print("Ground Truth Validation Script")
    print("="*40)
    
    # Load environment variables from .env file
    load_env_file()
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key in the .env file or as an environment variable")
        return
    
    try:
        # Initialize validator
        validator = GroundTruthValidator(model="gpt-3.5-turbo", provider="openai")  # Use cheaper model for testing
        
        # Validate all benchmark films
        print("Starting validation of benchmark films...")
        results = validator.validate_all_benchmarks()
        
        # Generate report
        report = validator.generate_validation_report(results)
        
        # Print report
        print_validation_report(report)
        
        # Save detailed results
        with open('ground_truth_validation_results.json', 'w') as f:
            # Convert dataclass objects to dict for JSON serialization
            json_results = []
            for result in results:
                json_results.append({
                    'movie_title': result.movie_title,
                    'factual_accuracy': result.factual_accuracy,
                    'key_elements_found': result.key_elements_found,
                    'key_elements_missing': result.key_elements_missing,
                    'factual_errors': result.factual_errors,
                    'overall_quality_score': result.overall_quality_score,
                    'ground_truth_text': result.ground_truth_text
                })
            
            # Convert report to JSON-serializable format
            json_report = {
                'summary': report['summary'],
                'common_issues': report['common_issues'],
                'individual_results': json_results
            }
            
            json.dump({
                'report': json_report,
                'detailed_results': json_results
            }, f, indent=2)
        
        print(f"\nDetailed results saved to: ground_truth_validation_results.json")
        
        # Provide recommendations
        print(f"\nRECOMMENDATIONS:")
        avg_quality = report["summary"]["average_quality_score"]
        
        if avg_quality >= 0.8:
            print("✅ Ground truth quality is excellent! The system is ready for production use.")
        elif avg_quality >= 0.6:
            print("⚠️  Ground truth quality is good but could be improved. Consider prompt refinements.")
        else:
            print("❌ Ground truth quality needs significant improvement. Consider:")
            print("   - Refining the ground truth generation prompts")
            print("   - Using a more powerful model (GPT-4)")
            print("   - Adding more specific instructions for factual accuracy")
        
    except Exception as e:
        print(f"Error during validation: {e}")
        print("Please check your API key and internet connection")


if __name__ == "__main__":
    main()
