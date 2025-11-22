# LLM-Based Movie Profile Evaluation System

A comprehensive multi-agent evaluation system that uses Large Language Models (LLMs) to evaluate the quality of generated movie profiles across multiple dimensions including cinema movements, socio-cultural context, formal analysis, narrative analysis, and distinctiveness.

## Overview

This system provides:
- **Multi-agent evaluation** using specialized LLM judges for different evaluation categories
- **Automated ground truth generation** using expert-level prompting
- **Multi-model validation** for consistency checking
- **Benchmark testing** against known film examples
- **Comprehensive analysis** and reporting

## System Architecture

### Core Components

1. **LLMJudge** (`llm_movie_evaluator.py`) - Main evaluation engine
2. **Validation System** (`llm_validation_system.py`) - Multi-model validation and benchmarks
3. **Test Suite** (`test_evaluation_system.py`) - Testing and demonstration scripts

### Evaluation Categories

The system evaluates movie profiles across 5 weighted categories:

| Category | Weight | Focus Area |
|----------|--------|------------|
| Cinema Movement & Genre Significance | 20% | Film movements, techniques, historical significance |
| Socio-Cultural-Historical Context | 25% | Historical period, social issues, cultural authenticity |
| Formal Cinematography Analysis | 20% | Technical innovations, visual style, thematic connections |
| Character Design & Plot Analysis | 15% | Narrative structure, character complexity, storytelling choices |
| Distinctiveness | 20% | Unique elements, influence, cultural impact |

## Quick Start

### 1. Setup

```bash
# Install required packages
pip install openai anthropic numpy

# Set up API keys
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

### 2. Basic Usage

```python
from llm_movie_evaluator import LLMJudge, GroundTruthGenerator

# Initialize judge
judge = LLMJudge(model="gpt-4", provider="openai")

# Generate ground truth for a movie
gt_generator = GroundTruthGenerator(model="gpt-4", provider="openai")
ground_truth = gt_generator.generate_reference_profile(movie_data)

# Evaluate a profile
result = judge.evaluate_profile(
    movie_title="Citizen Kane",
    generated_profile=your_generated_profile,
    ground_truth=ground_truth
)

print(f"Overall Score: {result.overall_score:.2f}")
```

### 3. Run Tests

```bash
python test_evaluation_system.py
```

## Detailed Usage

### LLMJudge Class

The main evaluation engine that uses specialized prompts for each category.

```python
judge = LLMJudge(model="gpt-4", provider="openai")

# Evaluate a single profile
result = judge.evaluate_profile(movie_title, generated_profile, ground_truth)

# Access results
print(f"Overall Score: {result.overall_score}")
print(f"Category Scores: {result.category_scores}")
print(f"Detailed Feedback: {result.detailed_feedback}")
```

### Ground Truth Generator

Creates expert-level reference profiles for evaluation.

```python
gt_generator = GroundTruthGenerator(model="gpt-4", provider="openai")
ground_truth = gt_generator.generate_reference_profile(movie_data)
```

### Automated Pipeline

Evaluate multiple profiles automatically.

```python
from llm_movie_evaluator import AutomatedEvaluationPipeline

pipeline = AutomatedEvaluationPipeline(
    judge_model="gpt-4",
    ground_truth_model="gpt-4"
)

# Evaluate sample of profiles
results = pipeline.evaluate_movie_profiles(movie_profiles, sample_size=20)

# Analyze results
analysis = pipeline.analyze_results(results)
print(f"Average Score: {analysis['overall_stats']['average']:.2f}")
```

### Validation System

Validate judge accuracy and consistency.

```python
from llm_validation_system import ValidationPipeline

validator = ValidationPipeline()
validation_results = validator.run_full_validation(judge)

print(f"Overall Accuracy: {validation_results['benchmark_validation']['overall_accuracy']:.2f}")
print(f"Quality Rating: {validation_results['overall_judge_quality']['quality_rating']}")
```

## Evaluation Criteria

### Scoring Scale

- **5**: Excellent - Comprehensive, accurate, insightful
- **4**: Good - Mostly accurate with minor gaps  
- **3**: Adequate - Generally correct but lacks depth
- **2**: Poor - Significant inaccuracies or omissions
- **1**: Very Poor - Major errors or completely generic

### Category-Specific Criteria

#### Cinema Movement & Genre Significance
- Movement identification accuracy
- Technique recognition
- Historical placement
- Genre contribution analysis

#### Socio-Cultural-Historical Context
- Temporal accuracy
- Social specificity
- Cultural authenticity
- Political relevance

#### Formal Cinematography Analysis
- Technical accuracy
- Innovation recognition
- Thematic connections
- Style identification

#### Character Design & Plot Analysis
- Structure recognition
- Character complexity
- Narrative innovation
- Thematic purpose

#### Distinctiveness
- Uniqueness identification
- Influence recognition
- Cultural impact
- Awards/recognition

## Benchmark Films

The system includes benchmark testing against well-known films:

- **Citizen Kane** (1941) - Expected score: 4.8
- **Breathless** (1960) - Expected score: 4.5
- **Bicycle Thieves** (1948) - Expected score: 4.6
- **Pulp Fiction** (1994) - Expected score: 4.4
- **Do the Right Thing** (1989) - Expected score: 4.3

## Configuration

### Model Options

**OpenAI Models:**
- `gpt-4` (recommended for best quality)
- `gpt-3.5-turbo` (faster, lower cost)

**Anthropic Models:**
- `claude-3-sonnet-20240229` (high quality)
- `claude-3-haiku-20240307` (faster)

### Customization

You can customize the evaluation by:

1. **Modifying prompts** in `LLMJudge._initialize_evaluation_prompts()`
2. **Adjusting weights** in `LLMJudge.category_weights`
3. **Adding benchmark films** in `BenchmarkValidation.benchmark_films`
4. **Customizing criteria** in evaluation prompts

## API Requirements

### Required Environment Variables

```bash
# For OpenAI models
export OPENAI_API_KEY="your-key-here"

# For Anthropic models  
export ANTHROPIC_API_KEY="your-key-here"
```

### Cost Considerations

- **GPT-4**: ~$0.03 per evaluation (high quality)
- **GPT-3.5-turbo**: ~$0.002 per evaluation (cost-effective)
- **Claude-3-Sonnet**: ~$0.015 per evaluation (balanced)

## Example Output

```
Evaluation Results for Citizen Kane:
Overall Score: 4.65

Category Scores:
  cinema_movement: 4.8
  socio_cultural: 4.6
  formal_analysis: 4.7
  narrative_analysis: 4.5
  distinctiveness: 4.7

Detailed Feedback:
  cinema_movement: Excellent identification of classical Hollywood movement; mentions deep focus cinematography innovation
  socio_cultural: Accurate 1941 context and media power themes; minor historical detail missing
  formal_analysis: Comprehensive technical analysis; correctly identifies Gregg Toland's contributions
  narrative_analysis: Good understanding of non-linear structure; could be more specific about character motivations
  distinctiveness: Strong recognition of lasting influence; excellent cultural impact analysis
```

## Troubleshooting

### Common Issues

1. **API Key Errors**: Ensure environment variables are set correctly
2. **Model Availability**: Check if your API key has access to the requested model
3. **Rate Limiting**: Add delays between requests for large batches
4. **Parsing Errors**: LLM responses may vary; the system handles this gracefully

### Performance Tips

1. **Use GPT-3.5-turbo** for initial testing and iteration
2. **Use GPT-4** for final evaluations and important assessments
3. **Batch evaluations** to reduce API call overhead
4. **Cache ground truth** to avoid regenerating for the same movies

## Integration with Existing System

To integrate with your existing movie recommender:

```python
# In your existing code
from llm_movie_evaluator import AutomatedEvaluationPipeline

# Initialize evaluator
evaluator = AutomatedEvaluationPipeline()

# Evaluate your generated profiles
results = evaluator.evaluate_movie_profiles(your_movie_profiles, sample_size=50)

# Get improvement recommendations
analysis = evaluator.analyze_results(results)
weak_categories = analysis['weak_categories']
print(f"Focus on improving: {', '.join(weak_categories)}")
```

## Future Enhancements

- **Human validation integration** for edge cases
- **Continuous learning** from evaluation feedback
- **Custom evaluation criteria** for specific use cases
- **Batch processing optimization** for large datasets
- **Visualization dashboard** for evaluation results

## Contributing

To improve the evaluation system:

1. **Add benchmark films** with known scores
2. **Refine evaluation prompts** based on results
3. **Add new evaluation categories** as needed
4. **Improve parsing logic** for better consistency
5. **Add support for new LLM providers**

## License

This evaluation system is part of the movie-recommender project and follows the same license terms.
