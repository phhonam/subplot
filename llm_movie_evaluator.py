"""
LLM-Based Movie Profile Evaluation System

A multi-agent evaluation system that uses LLMs to evaluate the quality of 
generated movie profiles across multiple dimensions including cinema movements,
socio-cultural context, formal analysis, narrative analysis, and distinctiveness.
"""

import json
import os
import random
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import numpy as np
from openai import OpenAI
import anthropic
import requests


@dataclass
class EvaluationResult:
    """Results from evaluating a movie profile"""
    movie_title: str
    overall_score: float
    category_scores: Dict[str, float]
    detailed_feedback: Dict[str, str]
    ground_truth: Optional[str] = None


@dataclass
class CategoryEvaluation:
    """Evaluation results for a single category"""
    score: float
    feedback: str
    criteria_scores: Dict[str, float]


class LLMJudge:
    """Multi-agent LLM-based evaluation system for movie profiles"""
    
    def __init__(self, model: str = "gpt-4", provider: str = "openai"):
        self.model = model
        self.provider = provider
        self.client = self._initialize_client()
        
        # Evaluation category weights (matching the framework)
        self.category_weights = {
            "cinema_movement": 0.20,
            "socio_cultural": 0.25,
            "formal_analysis": 0.20,
            "narrative_analysis": 0.15,
            "distinctiveness": 0.20
        }
        
        # Initialize evaluation prompts
        self.evaluation_prompts = self._initialize_evaluation_prompts()
    
    def _initialize_client(self):
        """Initialize the LLM client based on provider"""
        if self.provider == "openai":
            return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider == "anthropic":
            return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _initialize_evaluation_prompts(self) -> Dict[str, str]:
        """Initialize specialized evaluation prompts for each category"""
        return {
            "cinema_movement": """
You are an expert film scholar evaluating movie profile generation. Focus specifically on CINEMA MOVEMENT & GENRE SIGNIFICANCE.

MOVIE: {movie_title}
GENERATED PROFILE TO EVALUATE: {generated_profile}

CRITICAL INSTRUCTION: You are ONLY evaluating the "GENERATED PROFILE TO EVALUATE" above. 
- Do NOT use your knowledge about the movie from other sources
- Do NOT assume or infer details not explicitly written in the profile text
- Do NOT reference any external information about the film
- Score ONLY what is literally written in the generated profile text
- If the profile doesn't mention something, score it poorly - do NOT fill in gaps with your knowledge

EXAMPLE: If the profile says "groundbreaking film" but doesn't mention "New Hollywood movement", then score MOVEMENT_IDENTIFICATION as 1-2, not 5. Only reward what is explicitly stated.

Evaluate the generated profile on these criteria (score 1-5 for each):

1. MOVEMENT IDENTIFICATION (1-5):
   - Does it correctly identify the film's movement using precise terminology?
   - For American films: "Classical Hollywood", "Independent Cinema Revival", "Independent Social Cinema", "African American New Wave"
   - For European films: "French New Wave", "Italian Neorealism", "Dogme 95", etc.
   - Does it place the film within the correct cinematic movement context?

2. TECHNIQUE RECOGNITION (1-5):
   - Does it mention specific techniques associated with the movement?
   - Are the technical innovations accurately described?
   - Does it include cinematographer names for technically innovative films?

3. HISTORICAL PLACEMENT (1-5):
   - Does it position the film within broader cinema history?
   - Is the historical significance correctly identified?
   - Does it include specific historical context and cultural moments?

4. GENRE CONTRIBUTION (1-5):
   - Does it recognize how the film contributed to or subverted its genre?
   - Are genre innovations properly noted?
   - Does it include specific plot elements and character details?

SCORING SCALE:
- 5: Excellent - Comprehensive, accurate, insightful, includes specific details
- 4: Good - Mostly accurate with minor gaps
- 3: Adequate - Generally correct but lacks depth or specificity
- 2: Poor - Significant inaccuracies or omissions
- 1: Very Poor - Major errors, wrong movement, or generic descriptions

CRITICAL: Movement identification must be precise. Generic terms like "American cinema" or "independent film" without specific movement context should score poorly.

Provide scores and brief justification for each criterion.
Format your response as:
MOVEMENT_ID: [score] - [brief justification]
TECHNIQUE: [score] - [brief justification]
HISTORICAL: [score] - [brief justification]
GENRE: [score] - [brief justification]
OVERALL: [average score] - [summary]

FINAL WARNING: You MUST base your evaluation ONLY on what is explicitly written in the generated profile text above. 
- If the profile doesn't mention a specific detail (like "New Hollywood", "70mm film", "cinematographer name"), then it should score POORLY on that criterion
- Do NOT use your external knowledge about the movie to fill in missing information
- Only reward what is actually written in the profile text
- Penalize omissions heavily - this is evaluating the profile quality, not the movie quality
""",
            
            "socio_cultural": """
You are an expert film scholar evaluating movie profile generation. Focus specifically on SOCIO-CULTURAL-HISTORICAL CONTEXT.

MOVIE: {movie_title}
GENERATED PROFILE TO EVALUATE: {generated_profile}

CRITICAL INSTRUCTION: You are ONLY evaluating the "GENERATED PROFILE TO EVALUATE" above. 
- Do NOT use your knowledge about the movie from other sources
- Do NOT assume or infer details not explicitly written in the profile text
- Do NOT reference any external information about the film
- Score ONLY what is literally written in the generated profile text
- If the profile doesn't mention something, score it poorly - do NOT fill in gaps with your knowledge

Evaluate the generated profile on these criteria (score 1-5 for each):

1. TEMPORAL ACCURACY (1-5):
   - Does it correctly place the film in its historical period?
   - Are historical references accurate?
   - Does it include specific historical events that influenced the film?

2. SOCIAL SPECIFICITY (1-5):
   - Does it identify specific social issues and themes?
   - Are social contexts accurately described?
   - Does it include specific cultural/political events (e.g., "Howard Beach incident" for Do the Right Thing)?

3. CULTURAL AUTHENTICITY (1-5):
   - Does it recognize the filmmaker's perspective and cultural context?
   - Is cultural specificity maintained?
   - Does it include specific cultural movements or contexts?

4. POLITICAL RELEVANCE (1-5):
   - Does it understand political implications and responses to contemporary events?
   - Are political contexts accurately portrayed?
   - Does it include specific political/historical context that shaped the film?

SCORING SCALE:
- 5: Excellent - Comprehensive, accurate, insightful, includes specific historical events
- 4: Good - Mostly accurate with minor gaps
- 3: Adequate - Generally correct but lacks depth or specificity
- 2: Poor - Significant inaccuracies or omissions
- 1: Very Poor - Major errors or generic descriptions

CRITICAL: Look for specific historical events, cultural moments, and political context that influenced the film's creation and reception.

Format your response as:
TEMPORAL: [score] - [brief justification]
SOCIAL: [score] - [brief justification]
CULTURAL: [score] - [brief justification]
POLITICAL: [score] - [brief justification]
OVERALL: [average score] - [summary]

FINAL WARNING: You MUST base your evaluation ONLY on what is explicitly written in the generated profile text above. 
- If the profile doesn't mention a specific detail (like "New Hollywood", "70mm film", "cinematographer name"), then it should score POORLY on that criterion
- Do NOT use your external knowledge about the movie to fill in missing information
- Only reward what is actually written in the profile text
- Penalize omissions heavily - this is evaluating the profile quality, not the movie quality
""",
            
            "formal_analysis": """
You are an expert film scholar evaluating movie profile generation. Focus specifically on FORMAL CINEMATOGRAPHY ANALYSIS.

MOVIE: {movie_title}
GENERATED PROFILE TO EVALUATE: {generated_profile}

CRITICAL INSTRUCTION: You are ONLY evaluating the "GENERATED PROFILE TO EVALUATE" above. 
- Do NOT use your knowledge about the movie from other sources
- Do NOT assume or infer details not explicitly written in the profile text
- Do NOT reference any external information about the film
- Score ONLY what is literally written in the generated profile text
- If the profile doesn't mention something, score it poorly - do NOT fill in gaps with your knowledge

Evaluate the generated profile on these criteria (score 1-5 for each):

1. TECHNICAL ACCURACY (1-5):
   - Does it correctly identify cinematographic techniques?
   - Are technical details accurate?

2. INNOVATION RECOGNITION (1-5):
   - Does it note groundbreaking technical achievements?
   - Are innovations properly highlighted?

3. THEMATIC CONNECTION (1-5):
   - Does it link visual choices to thematic content?
   - Are formal choices connected to meaning?

4. STYLE IDENTIFICATION (1-5):
   - Does it recognize distinctive visual approaches?
   - Is the cinematographer's style identified?

SCORING SCALE:
- 5: Excellent - Comprehensive, accurate, insightful
- 4: Good - Mostly accurate with minor gaps
- 3: Adequate - Generally correct but lacks depth
- 2: Poor - Significant inaccuracies or omissions
- 1: Very Poor - Major errors or generic descriptions

Format your response as:
TECHNICAL: [score] - [brief justification]
INNOVATION: [score] - [brief justification]
THEMATIC: [score] - [brief justification]
STYLE: [score] - [brief justification]
OVERALL: [average score] - [summary]

FINAL WARNING: You MUST base your evaluation ONLY on what is explicitly written in the generated profile text above. 
- If the profile doesn't mention a specific detail (like "New Hollywood", "70mm film", "cinematographer name"), then it should score POORLY on that criterion
- Do NOT use your external knowledge about the movie to fill in missing information
- Only reward what is actually written in the profile text
- Penalize omissions heavily - this is evaluating the profile quality, not the movie quality
""",
            
            "narrative_analysis": """
You are an expert film scholar evaluating movie profile generation. Focus specifically on CHARACTER DESIGN & PLOT ANALYSIS.

MOVIE: {movie_title}
GENERATED PROFILE TO EVALUATE: {generated_profile}

CRITICAL INSTRUCTION: You are ONLY evaluating the "GENERATED PROFILE TO EVALUATE" above. 
- Do NOT use your knowledge about the movie from other sources
- Do NOT assume or infer details not explicitly written in the profile text
- Do NOT reference any external information about the film
- Score ONLY what is literally written in the generated profile text
- If the profile doesn't mention something, score it poorly - do NOT fill in gaps with your knowledge

Evaluate the generated profile on these criteria (score 1-5 for each):

1. STRUCTURE RECOGNITION (1-5):
   - Does it identify narrative innovations (non-linear, etc.)?
   - Is the narrative structure accurately described?

2. CHARACTER COMPLEXITY (1-5):
   - Does it recognize character archetypes and their subversion?
   - Are character developments properly analyzed?

3. NARRATIVE INNOVATION (1-5):
   - Does it note unique storytelling approaches?
   - Are narrative innovations highlighted?

4. THEMATIC PURPOSE (1-5):
   - Does it connect narrative choices to thematic goals?
   - Are story choices linked to meaning?

SCORING SCALE:
- 5: Excellent - Comprehensive, accurate, insightful
- 4: Good - Mostly accurate with minor gaps
- 3: Adequate - Generally correct but lacks depth
- 2: Poor - Significant inaccuracies or omissions
- 1: Very Poor - Major errors or generic descriptions

Format your response as:
STRUCTURE: [score] - [brief justification]
CHARACTER: [score] - [brief justification]
INNOVATION: [score] - [brief justification]
THEMATIC: [score] - [brief justification]
OVERALL: [average score] - [summary]

FINAL WARNING: You MUST base your evaluation ONLY on what is explicitly written in the generated profile text above. 
- If the profile doesn't mention a specific detail (like "New Hollywood", "70mm film", "cinematographer name"), then it should score POORLY on that criterion
- Do NOT use your external knowledge about the movie to fill in missing information
- Only reward what is actually written in the profile text
- Penalize omissions heavily - this is evaluating the profile quality, not the movie quality
""",
            
            "distinctiveness": """
You are an expert film scholar evaluating movie profile generation. Focus specifically on DISTINCTIVENESS.

MOVIE: {movie_title}
GENERATED PROFILE TO EVALUATE: {generated_profile}

CRITICAL INSTRUCTION: You are ONLY evaluating the "GENERATED PROFILE TO EVALUATE" above. 
- Do NOT use your knowledge about the movie from other sources
- Do NOT assume or infer details not explicitly written in the profile text
- Do NOT reference any external information about the film
- Score ONLY what is literally written in the generated profile text
- If the profile doesn't mention something, score it poorly - do NOT fill in gaps with your knowledge

Evaluate the generated profile on these criteria (score 1-5 for each):

1. UNIQUENESS IDENTIFICATION (1-5):
   - Does it recognize distinctive elements that set the film apart?
   - Are unique selling points identified?

2. INFLUENCE RECOGNITION (1-5):
   - Does it understand the film's impact on subsequent cinema?
   - Is influence on other filmmakers noted?

3. CULTURAL IMPACT (1-5):
   - Does it acknowledge broader cultural significance?
   - Is cultural footprint recognized?

4. AWARDS/RECOGNITION (1-5):
   - Does it note significant awards and their meaning?
   - Are achievements properly contextualized?

SCORING SCALE:
- 5: Excellent - Comprehensive, accurate, insightful
- 4: Good - Mostly accurate with minor gaps
- 3: Adequate - Generally correct but lacks depth
- 2: Poor - Significant inaccuracies or omissions
- 1: Very Poor - Major errors or generic descriptions

Format your response as:
UNIQUENESS: [score] - [brief justification]
INFLUENCE: [score] - [brief justification]
CULTURAL: [score] - [brief justification]
AWARDS: [score] - [brief justification]
OVERALL: [average score] - [summary]

FINAL WARNING: You MUST base your evaluation ONLY on what is explicitly written in the generated profile text above. 
- If the profile doesn't mention a specific detail (like "New Hollywood", "70mm film", "cinematographer name"), then it should score POORLY on that criterion
- Do NOT use your external knowledge about the movie to fill in missing information
- Only reward what is actually written in the profile text
- Penalize omissions heavily - this is evaluating the profile quality, not the movie quality
"""
        }
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM with the given prompt"""
        import time
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if self.provider == "openai":
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are an expert film scholar with deep knowledge of cinema history, movements, techniques, and cultural context."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1000,
                        temperature=0.3,  # Low temperature for consistent evaluation
                        timeout=30  # Add timeout
                    )
                    return response.choices[0].message.content
                elif self.provider == "anthropic":
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=1000,
                        temperature=0.3,
                        timeout=30,  # Add timeout
                        system="You are an expert film scholar with deep knowledge of cinema history, movements, techniques, and cultural context.",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text
            except Exception as e:
                print(f"Error calling LLM (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"All retry attempts failed for LLM call")
                    # Return a fallback response instead of failing completely
                    return "Unable to complete evaluation due to API error. Please try again later."
    
    def _parse_evaluation_response(self, response: str) -> Tuple[float, str]:
        """Parse the LLM evaluation response to extract score and feedback"""
        try:
            lines = response.strip().split('\n')
            scores = []
            feedback_parts = []
            
            for line in lines:
                if ':' in line and any(keyword in line.upper() for keyword in ['MOVEMENT', 'TECHNIQUE', 'HISTORICAL', 'GENRE', 'TEMPORAL', 'SOCIAL', 'CULTURAL', 'POLITICAL', 'TECHNICAL', 'INNOVATION', 'THEMATIC', 'STYLE', 'STRUCTURE', 'CHARACTER', 'UNIQUENESS', 'INFLUENCE', 'AWARDS', 'OVERALL']):
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        try:
                            # Extract score from the line
                            score_text = parts[1].split('-')[0].strip()
                            # Find the first number in the score text
                            import re
                            score_match = re.search(r'\b([1-5])\b', score_text)
                            if score_match:
                                score = float(score_match.group(1))
                                scores.append(score)
                                
                                # Extract feedback
                                feedback_part = parts[1].split('-', 1)[1].strip() if '-' in parts[1] else ""
                                feedback_parts.append(f"{parts[0].strip()}: {feedback_part}")
                        except (ValueError, IndexError):
                            continue
            
            if scores:
                overall_score = sum(scores) / len(scores)
                feedback = '; '.join(feedback_parts)
                return overall_score, feedback
            else:
                return 2.0, "Could not parse evaluation response"
                
        except Exception as e:
            print(f"Error parsing evaluation response: {e}")
            return 2.0, f"Parsing error: {str(e)}"
    
    def evaluate_category(self, movie_title: str, generated_profile: str, ground_truth: str, category: str) -> CategoryEvaluation:
        """Evaluate a single category using keyword-based approach to prevent hallucination"""
        
        # Debug: Print what we're evaluating
        print(f"DEBUG - Evaluating {category} for {movie_title}")
        print(f"DEBUG - Generated profile text: '{generated_profile[:200]}...' (length: {len(generated_profile)})")
        
        # Use keyword-based evaluation for cinema_movement to prevent hallucination
        if category == "cinema_movement":
            return self._evaluate_cinema_movement_keywords(generated_profile)
        else:
            # For other categories, use the LLM but with even more explicit instructions
            prompt_template = self.evaluation_prompts[category]
            prompt = prompt_template.format(
                movie_title=movie_title,
                generated_profile=generated_profile
            )
            
            # Add extra warning to prevent hallucination
            prompt += "\n\nSTOP! Before you respond, re-read the generated profile above. Only mention facts that are explicitly written in that text. Do not add any information from your knowledge about the movie."
            
            # Debug: Print the prompt being sent to LLM
            print(f"DEBUG - Prompt for {category}:")
            print(f"'{prompt[:500]}...'")
            
            response = self._call_llm(prompt)
            score, feedback = self._parse_evaluation_response(response)
            
            return CategoryEvaluation(
                score=score,
                feedback=feedback,
                criteria_scores={}
            )
    
    def _evaluate_cinema_movement_keywords(self, generated_profile: str) -> CategoryEvaluation:
        """Keyword-based evaluation for cinema movement to prevent hallucination"""
        profile_lower = generated_profile.lower()
        
        # Define specific keywords that indicate cinema movement identification
        movement_keywords = [
            "new hollywood", "classical hollywood", "independent cinema", "french new wave",
            "italian neorealism", "dogme 95", "american new wave", "independent social cinema",
            "african american new wave", "cinema movement", "film movement"
        ]
        
        # Check if any movement keywords are present
        movement_found = any(keyword in profile_lower for keyword in movement_keywords)
        
        # Define technique keywords
        technique_keywords = [
            "cinematographer", "70mm", "special effects", "practical effects", "camera work",
            "cinematography", "visual effects", "film technique", "camera movement"
        ]
        
        technique_found = any(keyword in profile_lower for keyword in technique_keywords)
        
        # Define historical context keywords
        historical_keywords = [
            "1960s", "1970s", "1980s", "1990s", "space race", "cold war", "historical",
            "era", "period", "time", "decade", "century", "world war", "cultural moment"
        ]
        
        historical_found = any(keyword in profile_lower for keyword in historical_keywords)
        
        # Calculate scores based on what's actually present
        movement_score = 5.0 if movement_found else 1.0
        technique_score = 5.0 if technique_found else 1.0  
        historical_score = 5.0 if historical_found else 1.0
        genre_score = 3.0  # Basic genre recognition if profile exists
        
        overall_score = (movement_score + technique_score + historical_score + genre_score) / 4
        
        # Create feedback based on what's actually found
        feedback_parts = []
        if movement_found:
            feedback_parts.append("MOVEMENT_ID: 5.00 - Movement identification found in profile")
        else:
            feedback_parts.append("MOVEMENT_ID: 1.00 - No specific cinema movement mentioned")
            
        if technique_found:
            feedback_parts.append("TECHNIQUE: 5.00 - Technical details mentioned")
        else:
            feedback_parts.append("TECHNIQUE: 1.00 - No specific technical details mentioned")
            
        if historical_found:
            feedback_parts.append("HISTORICAL: 5.00 - Historical context mentioned")
        else:
            feedback_parts.append("HISTORICAL: 1.00 - No specific historical context mentioned")
            
        feedback_parts.append("GENRE: 3.00 - Basic genre recognition")
        feedback_parts.append(f"OVERALL: {overall_score:.2f} - Evaluation based only on content explicitly present in profile")
        
        feedback = "; ".join(feedback_parts)
        
        return CategoryEvaluation(
            score=overall_score,
            feedback=feedback,
            criteria_scores={
                "movement_id": movement_score,
                "technique": technique_score,
                "historical": historical_score,
                "genre": genre_score
            }
        )
    
    def evaluate_profile(self, movie_title: str, generated_profile: str, ground_truth: str) -> EvaluationResult:
        """Evaluate a movie profile across all categories"""
        category_scores = {}
        detailed_feedback = {}
        
        print(f"Evaluating {movie_title}...")
        
        for category in self.category_weights.keys():
            print(f"  Evaluating {category}...")
            evaluation = self.evaluate_category(movie_title, generated_profile, ground_truth, category)
            category_scores[category] = evaluation.score
            detailed_feedback[category] = evaluation.feedback
        
        # Calculate weighted overall score
        overall_score = sum(
            category_scores[category] * self.category_weights[category]
            for category in self.category_weights.keys()
        )
        
        return EvaluationResult(
            movie_title=movie_title,
            overall_score=overall_score,
            category_scores=category_scores,
            detailed_feedback=detailed_feedback,
            ground_truth=ground_truth
        )


class GroundTruthGenerator:
    """Generate high-quality reference profiles using LLMs"""
    
    def __init__(self, model: str = "gpt-4", provider: str = "openai"):
        self.model = model
        self.provider = provider
        self.client = self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the LLM client based on provider"""
        if self.provider == "openai":
            return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif self.provider == "anthropic":
            return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM with the given prompt"""
        import time
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if self.provider == "openai":
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a world-renowned film scholar with expertise in cinema history, movements, technical analysis, cultural context, and critical theory."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1500,
                        temperature=0.7,
                        timeout=30  # Add timeout
                    )
                    return response.choices[0].message.content
                elif self.provider == "anthropic":
                    response = self.client.messages.create(
                        model=self.model,
                        max_tokens=1500,
                        temperature=0.7,
                        timeout=30,  # Add timeout
                        system="You are a world-renowned film scholar with expertise in cinema history, movements, technical analysis, cultural context, and critical theory.",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text
            except Exception as e:
                print(f"Error calling LLM (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"All retry attempts failed for LLM call")
                    # Return a fallback response instead of failing completely
                    return "Unable to generate ground truth due to API error. Please try again later."
    
    def generate_reference_profile(self, movie_data: Dict[str, Any]) -> str:
        """Generate a high-quality reference profile using expert-level prompting"""
        prompt = f"""
You are a world-renowned film scholar with expertise in:
- Cinema history and movements (French New Wave, Italian Neorealism, Classical Hollywood, Independent Cinema, etc.)
- Technical film analysis (cinematography, editing, sound design)
- Cultural and historical context
- Critical theory and analysis
- Genre studies and film criticism

Create a comprehensive, expert-level movie profile for: {movie_data['title']}

MOVIE INFORMATION:
Title: {movie_data['title']} ({movie_data['year']})
Director: {movie_data['director']}
Genres: {', '.join(movie_data.get('genre_tags', []))}
Plot: {movie_data['plot_summary']}

CRITICAL REQUIREMENTS - You MUST include:

1. CINEMA MOVEMENT IDENTIFICATION: 
   - ACCURATELY identify the specific film movement (NOT generic terms)
   - For American films: Use "Classical Hollywood", "Independent Cinema Revival", "Independent Social Cinema", "African American New Wave"
   - For European films: Use "French New Wave", "Italian Neorealism", "Dogme 95", etc.
   - Place it within broader cinema history with specific historical context
   - Note specific techniques and innovations associated with that movement

2. SOCIO-CULTURAL CONTEXT:
   - Accurate historical, social, and cultural positioning
   - Specific social issues and political context of the era
   - Cultural authenticity and filmmaker perspective
   - Include specific historical events or cultural moments that influenced the film

3. FORMAL ANALYSIS:
   - Detailed technical and aesthetic analysis
   - Cinematographic innovations and techniques
   - Visual style and thematic connections
   - Include specific cinematographer names and technical innovations when known

4. NARRATIVE ANALYSIS:
   - Sophisticated understanding of storytelling choices
   - Character development and narrative structure
   - Thematic purpose of narrative decisions
   - Include specific plot elements and character arcs

5. DISTINCTIVENESS:
   - Clear identification of what makes this film unique
   - Influence on subsequent cinema
   - Cultural impact and significance
   - Include specific awards, recognition, or cultural milestones

SPECIFIC ACCURACY REQUIREMENTS:
- Include key plot elements and character names when relevant (e.g., "Rosebud" for Citizen Kane)
- Mention specific historical context (e.g., "Howard Beach incident" for Do the Right Thing)
- Include cinematographer names for technically innovative films (e.g., "Gregg Toland" for Citizen Kane)
- Use precise movement terminology, not generic descriptions
- Include specific cultural/political events that influenced the film

Be specific, accurate, and demonstrate deep film scholarship. This will be used as ground truth for evaluating AI-generated profiles.

Structure your response as a comprehensive movie profile that covers all these dimensions in a cohesive, scholarly manner.
"""
        return self._call_llm(prompt)


class AutomatedEvaluationPipeline:
    """Automated pipeline for evaluating movie profiles"""
    
    def __init__(self, judge_model: str = "gpt-4", ground_truth_model: str = "gpt-4"):
        self.judge = LLMJudge(model=judge_model)
        self.ground_truth_generator = GroundTruthGenerator(model=ground_truth_model)
    
    def _select_diverse_sample(self, movie_profiles: Dict[str, Any], sample_size: int) -> Dict[str, Any]:
        """Select a diverse sample of movies for evaluation"""
        # Simple random sampling for now - could be improved with diversity metrics
        all_titles = list(movie_profiles.keys())
        if len(all_titles) <= sample_size:
            return movie_profiles
        
        return {title: movie_profiles[title] for title in random.sample(all_titles, sample_size)}
    
    def evaluate_movie_profiles(self, movie_profiles: Dict[str, Any], sample_size: int = 20) -> List[EvaluationResult]:
        """Evaluate a sample of movie profiles"""
        results = []
        
        # Select diverse sample
        sample_movies = self._select_diverse_sample(movie_profiles, sample_size)
        
        for movie_title, movie_data in sample_movies.items():
            print(f"\n=== Evaluating: {movie_title} ===")
            
            try:
                # Generate ground truth
                print("Generating ground truth...")
                ground_truth = self.ground_truth_generator.generate_reference_profile(movie_data)
                
                # Get generated profile (combine relevant fields)
                generated_profile = self._extract_profile_text(movie_data)
                
                # Evaluate
                print("Running evaluation...")
                result = self.judge.evaluate_profile(
                    movie_title, generated_profile, ground_truth
                )
                
                results.append(result)
                
                # Print results
                print(f"Overall Score: {result.overall_score:.2f}")
                for category, score in result.category_scores.items():
                    print(f"  {category}: {score:.2f}")
                
            except Exception as e:
                print(f"Error evaluating {movie_title}: {e}")
                continue
        
        return results
    
    def _extract_profile_text(self, movie_data: Dict[str, Any]) -> str:
        """Extract the profile text from movie data"""
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
    
    def analyze_results(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """Analyze evaluation results and provide insights"""
        if not results:
            return {"error": "No results to analyze"}
        
        # Calculate statistics
        overall_scores = [r.overall_score for r in results]
        category_scores = {}
        
        for category in self.judge.category_weights.keys():
            scores = [r.category_scores[category] for r in results]
            category_scores[category] = {
                'average': np.mean(scores),
                'std': np.std(scores),
                'min': np.min(scores),
                'max': np.max(scores)
            }
        
        # Identify weak areas
        weak_categories = [cat for cat, stats in category_scores.items() if stats['average'] < 3.0]
        
        # Find best and worst performers
        best_result = max(results, key=lambda r: r.overall_score)
        worst_result = min(results, key=lambda r: r.overall_score)
        
        return {
            'overall_stats': {
                'average': np.mean(overall_scores),
                'std': np.std(overall_scores),
                'min': np.min(overall_scores),
                'max': np.max(overall_scores)
            },
            'category_scores': category_scores,
            'weak_categories': weak_categories,
            'best_performer': {
                'movie': best_result.movie_title,
                'score': best_result.overall_score
            },
            'worst_performer': {
                'movie': worst_result.movie_title,
                'score': worst_result.overall_score
            },
            'total_evaluated': len(results)
        }


def main():
    """Example usage of the evaluation system"""
    # Load movie profiles
    with open('movie_profiles_merged.json', 'r') as f:
        movie_profiles = json.load(f)
    
    # Initialize evaluation pipeline
    evaluator = AutomatedEvaluationPipeline()
    
    # Run evaluation on a small sample
    print("Starting movie profile evaluation...")
    results = evaluator.evaluate_movie_profiles(movie_profiles, sample_size=5)
    
    # Analyze results
    analysis = evaluator.analyze_results(results)
    
    print("\n=== EVALUATION ANALYSIS ===")
    print(f"Total evaluated: {analysis['total_evaluated']}")
    print(f"Overall average score: {analysis['overall_stats']['average']:.2f}")
    print(f"Score range: {analysis['overall_stats']['min']:.2f} - {analysis['overall_stats']['max']:.2f}")
    
    print("\nCategory Performance:")
    for category, stats in analysis['category_scores'].items():
        print(f"  {category}: {stats['average']:.2f} ± {stats['std']:.2f}")
    
    if analysis['weak_categories']:
        print(f"\nAreas needing improvement: {', '.join(analysis['weak_categories'])}")
    
    print(f"\nBest performer: {analysis['best_performer']['movie']} ({analysis['best_performer']['score']:.2f})")
    print(f"Worst performer: {analysis['worst_performer']['movie']} ({analysis['worst_performer']['score']:.2f})")


if __name__ == "__main__":
    main()
