"""
LLM Validation and Benchmarking System

Provides multi-model validation, consistency checking, and benchmark testing
for the movie profile evaluation system.
"""

import json
import os
import statistics
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import numpy as np
from llm_movie_evaluator import LLMJudge, EvaluationResult, GroundTruthGenerator


@dataclass
class ValidationResult:
    """Results from multi-model validation"""
    movie_title: str
    model_scores: Dict[str, float]
    average_score: float
    consistency_score: float
    standard_deviation: float
    max_difference: float


@dataclass
class BenchmarkResult:
    """Results from benchmark testing"""
    movie_title: str
    expected_score: float
    actual_score: float
    difference: float
    accuracy: float
    key_elements_found: List[str]
    key_elements_missing: List[str]


class MultiModelValidation:
    """Validate evaluations using multiple LLM models"""
    
    def __init__(self):
        # Available models for validation
        self.models = {
            "gpt-4": {"provider": "openai", "model": "gpt-4"},
            "gpt-3.5-turbo": {"provider": "openai", "model": "gpt-3.5-turbo"},
            "claude-3-sonnet": {"provider": "anthropic", "model": "claude-3-sonnet-20240229"}
        }
        
        self.judges = {}
        for name, config in self.models.items():
            try:
                self.judges[name] = LLMJudge(
                    model=config["model"], 
                    provider=config["provider"]
                )
            except Exception as e:
                print(f"Warning: Could not initialize {name}: {e}")
    
    def validate_evaluation(self, movie_title: str, generated_profile: str, ground_truth: str) -> ValidationResult:
        """Get evaluations from multiple models and check consistency"""
        model_scores = {}
        
        for model_name, judge in self.judges.items():
            try:
                result = judge.evaluate_profile(movie_title, generated_profile, ground_truth)
                model_scores[model_name] = result.overall_score
            except Exception as e:
                print(f"Error with {model_name}: {e}")
                continue
        
        if not model_scores:
            raise ValueError("No models were able to provide evaluations")
        
        # Calculate consistency metrics
        scores = list(model_scores.values())
        average_score = statistics.mean(scores)
        standard_deviation = statistics.stdev(scores) if len(scores) > 1 else 0
        max_difference = max(scores) - min(scores)
        
        # Consistency score (higher is more consistent)
        consistency_score = max(0, 1 - (standard_deviation / 2))  # Normalize to 0-1 scale
        
        return ValidationResult(
            movie_title=movie_title,
            model_scores=model_scores,
            average_score=average_score,
            consistency_score=consistency_score,
            standard_deviation=standard_deviation,
            max_difference=max_difference
        )
    
    def validate_multiple_profiles(self, profiles_data: List[Dict[str, Any]]) -> List[ValidationResult]:
        """Validate multiple profiles across models"""
        results = []
        
        for profile_data in profiles_data:
            movie_title = profile_data['movie_title']
            generated_profile = profile_data['generated_profile']
            ground_truth = profile_data['ground_truth']
            
            try:
                result = self.validate_evaluation(movie_title, generated_profile, ground_truth)
                results.append(result)
            except Exception as e:
                print(f"Error validating {movie_title}: {e}")
                continue
        
        return results


class BenchmarkValidation:
    """Validate LLM judge accuracy against known benchmark films"""
    
    def __init__(self):
        # Benchmark films with expected scores and key elements
        self.benchmark_films = {
            "Citizen Kane": {
                "expected_score": 4.8,
                "key_elements": [
                    "deep focus cinematography",
                    "non-linear narrative",
                    "media power themes",
                    "Orson Welles",
                    "1941",
                    "cinematic innovation",
                    "Rosebud",
                    "multiple perspectives"
                ],
                "movement": "Classical Hollywood",
                "cultural_context": "Pre-war America, media empire rise"
            },
            "Breathless": {
                "expected_score": 4.5,
                "key_elements": [
                    "French New Wave",
                    "jump cuts",
                    "handheld camera",
                    "Jean-Luc Godard",
                    "1960",
                    "cinematic revolution",
                    "natural lighting",
                    "improvised dialogue"
                ],
                "movement": "French New Wave",
                "cultural_context": "1960s French cinema revolution"
            },
            "Bicycle Thieves": {
                "expected_score": 4.6,
                "key_elements": [
                    "Italian Neorealism",
                    "non-professional actors",
                    "location shooting",
                    "Vittorio De Sica",
                    "1948",
                    "post-war Italy",
                    "social realism",
                    "working class"
                ],
                "movement": "Italian Neorealism",
                "cultural_context": "Post-WWII Italian society"
            },
            "Pulp Fiction": {
                "expected_score": 4.4,
                "key_elements": [
                    "non-linear structure",
                    "Quentin Tarantino",
                    "1994",
                    "postmodern",
                    "moral ambiguity",
                    "pop culture references",
                    "interconnected stories",
                    "crime genre subversion"
                ],
                "movement": "Independent Cinema Revival",
                "cultural_context": "1990s independent film boom"
            },
            "Do the Right Thing": {
                "expected_score": 4.3,
                "key_elements": [
                    "Spike Lee",
                    "1989",
                    "racial tensions",
                    "police brutality",
                    "Howard Beach",
                    "Brooklyn",
                    "social commentary",
                    "civil unrest"
                ],
                "movement": "Independent Social Cinema",
                "cultural_context": "Late 1980s racial tensions, post-Reagan era"
            }
        }
    
    def validate_judge_accuracy(self, judge: LLMJudge) -> List[BenchmarkResult]:
        """Test if LLM judge scores align with expected scores"""
        results = []
        
        for film_title, benchmark_data in self.benchmark_films.items():
            print(f"Benchmarking {film_title}...")
            
            try:
                # Create a mock generated profile (you'd replace this with actual generated profiles)
                generated_profile = self._create_mock_profile(film_title, benchmark_data)
                
                # Create ground truth
                ground_truth = self._create_ground_truth(film_title, benchmark_data)
                
                # Get evaluation from judge
                evaluation_result = judge.evaluate_profile(film_title, generated_profile, ground_truth)
                actual_score = evaluation_result.overall_score
                
                # Calculate metrics
                expected_score = benchmark_data["expected_score"]
                difference = abs(actual_score - expected_score)
                accuracy = max(0, 1 - (difference / expected_score))  # Accuracy as percentage
                
                # Check key elements (simplified - in practice you'd parse the evaluation text)
                key_elements_found = self._check_key_elements(
                    evaluation_result.detailed_feedback, benchmark_data["key_elements"]
                )
                key_elements_missing = [
                    element for element in benchmark_data["key_elements"] 
                    if element not in key_elements_found
                ]
                
                result = BenchmarkResult(
                    movie_title=film_title,
                    expected_score=expected_score,
                    actual_score=actual_score,
                    difference=difference,
                    accuracy=accuracy,
                    key_elements_found=key_elements_found,
                    key_elements_missing=key_elements_missing
                )
                
                results.append(result)
                
                print(f"  Expected: {expected_score:.2f}, Got: {actual_score:.2f}, Diff: {difference:.2f}")
                
            except Exception as e:
                print(f"Error benchmarking {film_title}: {e}")
                continue
        
        return results
    
    def _create_mock_profile(self, film_title: str, benchmark_data: Dict[str, Any]) -> str:
        """Create a mock generated profile for testing"""
        # This would normally be replaced with actual generated profiles
        movement = benchmark_data.get("movement", "Unknown movement")
        cultural_context = benchmark_data.get("cultural_context", "Unknown context")
        
        return f"""
Title: {film_title}
Primary emotional tone: dramatic
Secondary emotional tone: contemplative
Primary theme: identity_crisis
Secondary theme: social_commentary
Intensity level: high
Pacing style: methodical
Visual aesthetic: {movement} with innovative cinematography
Target audience: Film enthusiasts and critics
Cultural context: {cultural_context}
Narrative structure: Complex narrative with multiple perspectives
Profile text: {film_title} represents a significant achievement in cinema, showcasing innovative techniques and deep thematic exploration within the context of {movement}. The film demonstrates remarkable {cultural_context} and continues to influence contemporary filmmaking.
"""
    
    def _create_ground_truth(self, film_title: str, benchmark_data: Dict[str, Any]) -> str:
        """Create ground truth for benchmarking"""
        key_elements = ", ".join(benchmark_data["key_elements"])
        movement = benchmark_data["movement"]
        cultural_context = benchmark_data["cultural_context"]
        
        return f"""
EXPERT REFERENCE PROFILE FOR {film_title.upper()}

CINEMA MOVEMENT: {movement}
KEY TECHNICAL ELEMENTS: {key_elements}
CULTURAL CONTEXT: {cultural_context}

This film is a landmark achievement in {movement}, demonstrating innovative techniques and significant cultural impact. The film's influence extends beyond its immediate context and continues to shape contemporary cinema.
"""
    
    def _check_key_elements(self, evaluation_text: str, key_elements: List[str]) -> List[str]:
        """Check which key elements are mentioned in the evaluation"""
        found_elements = []
        evaluation_lower = evaluation_text.lower()
        
        for element in key_elements:
            if element.lower() in evaluation_lower:
                found_elements.append(element)
        
        return found_elements
    
    def analyze_benchmark_results(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Analyze benchmark validation results"""
        if not results:
            return {"error": "No benchmark results to analyze"}
        
        accuracies = [r.accuracy for r in results]
        differences = [r.difference for r in results]
        
        # Calculate statistics
        avg_accuracy = statistics.mean(accuracies)
        avg_difference = statistics.mean(differences)
        
        # Find most and least accurate
        most_accurate = max(results, key=lambda r: r.accuracy)
        least_accurate = min(results, key=lambda r: r.accuracy)
        
        # Calculate element coverage
        total_elements = sum(len(r.key_elements_found) + len(r.key_elements_missing) for r in results)
        found_elements = sum(len(r.key_elements_found) for r in results)
        element_coverage = found_elements / total_elements if total_elements > 0 else 0
        
        return {
            "overall_accuracy": avg_accuracy,
            "average_difference": avg_difference,
            "element_coverage": element_coverage,
            "most_accurate": {
                "movie": most_accurate.movie_title,
                "accuracy": most_accurate.accuracy
            },
            "least_accurate": {
                "movie": least_accurate.movie_title,
                "accuracy": least_accurate.accuracy
            },
            "individual_results": results
        }


class ValidationPipeline:
    """Complete validation pipeline combining multi-model and benchmark validation"""
    
    def __init__(self):
        self.multi_model_validator = MultiModelValidation()
        self.benchmark_validator = BenchmarkValidation()
    
    def run_full_validation(self, judge: LLMJudge) -> Dict[str, Any]:
        """Run complete validation including benchmarks and multi-model consistency"""
        print("=== Running Full Validation Pipeline ===")
        
        # 1. Benchmark validation
        print("\n1. Running benchmark validation...")
        benchmark_results = self.benchmark_validator.validate_judge_accuracy(judge)
        benchmark_analysis = self.benchmark_validator.analyze_benchmark_results(benchmark_results)
        
        # 2. Multi-model consistency check (if multiple models available)
        print("\n2. Checking multi-model consistency...")
        consistency_results = []
        
        if len(self.multi_model_validator.judges) > 1:
            # Test with a few benchmark films
            test_films = ["Citizen Kane", "Breathless"]
            for film in test_films:
                if film in self.benchmark_validator.benchmark_films:
                    benchmark_data = self.benchmark_validator.benchmark_films[film]
                    mock_profile = self.benchmark_validator._create_mock_profile(film, benchmark_data)
                    ground_truth = self.benchmark_validator._create_ground_truth(film, benchmark_data)
                    
                    try:
                        consistency_result = self.multi_model_validator.validate_evaluation(
                            film, mock_profile, ground_truth
                        )
                        consistency_results.append(consistency_result)
                    except Exception as e:
                        print(f"Error in consistency check for {film}: {e}")
        
        # 3. Compile results
        validation_summary = {
            "benchmark_validation": benchmark_analysis,
            "consistency_check": {
                "average_consistency": statistics.mean([r.consistency_score for r in consistency_results]) if consistency_results else 0,
                "consistency_results": consistency_results
            },
            "overall_judge_quality": self._calculate_judge_quality(benchmark_analysis, consistency_results)
        }
        
        return validation_summary
    
    def _calculate_judge_quality(self, benchmark_analysis: Dict[str, Any], consistency_results: List) -> Dict[str, Any]:
        """Calculate overall judge quality score"""
        benchmark_accuracy = benchmark_analysis.get("overall_accuracy", 0)
        consistency_score = statistics.mean([r.consistency_score for r in consistency_results]) if consistency_results else 0
        
        # Weighted quality score
        overall_quality = (benchmark_accuracy * 0.7) + (consistency_score * 0.3)
        
        # Quality rating
        if overall_quality >= 0.8:
            quality_rating = "Excellent"
        elif overall_quality >= 0.6:
            quality_rating = "Good"
        elif overall_quality >= 0.4:
            quality_rating = "Fair"
        else:
            quality_rating = "Poor"
        
        return {
            "overall_quality_score": overall_quality,
            "quality_rating": quality_rating,
            "benchmark_contribution": benchmark_accuracy * 0.7,
            "consistency_contribution": consistency_score * 0.3
        }


def main():
    """Example usage of the validation system"""
    from llm_movie_evaluator import LLMJudge
    
    # Initialize judge
    judge = LLMJudge(model="gpt-4", provider="openai")
    
    # Initialize validation pipeline
    validator = ValidationPipeline()
    
    # Run full validation
    print("Starting validation of LLM judge...")
    validation_results = validator.run_full_validation(judge)
    
    # Print results
    print("\n=== VALIDATION RESULTS ===")
    
    # Benchmark results
    benchmark = validation_results["benchmark_validation"]
    print(f"Overall Accuracy: {benchmark['overall_accuracy']:.2f}")
    print(f"Element Coverage: {benchmark['element_coverage']:.2f}")
    print(f"Most Accurate: {benchmark['most_accurate']['movie']} ({benchmark['most_accurate']['accuracy']:.2f})")
    print(f"Least Accurate: {benchmark['least_accurate']['movie']} ({benchmark['least_accurate']['accuracy']:.2f})")
    
    # Consistency results
    consistency = validation_results["consistency_check"]
    print(f"Average Consistency: {consistency['average_consistency']:.2f}")
    
    # Overall quality
    quality = validation_results["overall_judge_quality"]
    print(f"Overall Quality Score: {quality['overall_quality_score']:.2f}")
    print(f"Quality Rating: {quality['quality_rating']}")


if __name__ == "__main__":
    main()
