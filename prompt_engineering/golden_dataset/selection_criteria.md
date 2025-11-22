# Golden Dataset Selection Criteria

## Overview
This golden dataset contains 20 carefully selected films designed to expose failure modes in movie profile generation, specifically focusing on the `profile_text` field.

## Selection Rationale

### Why Edge Cases?
Failure modes surface most clearly where films don't fit standard patterns. Generic descriptions fail to capture:
- Specific cinema movements (Dogme 95, Korean New Wave, Slow Cinema)
- Cultural/historical context (Cold War Poland, 1970s Mexico City, post-IMF Korea)
- Technical innovations (iPhone cinematography, naturalistic Dogme style)
- Director's unique visual language (Wong Kar-wai's color palette, Park Chan-wook's baroque compositions)

### Categories & Testing Focus

#### Classic Cinema Movement Exemplars (3 films)
- **Purpose**: Test historical accuracy and movement identification
- **Key challenges**: 
  - Distinguishing Classical Hollywood from "indie cinema"
  - Identifying specific movements (Neorealism, New Wave)
  - Including historical context and technical innovations

#### Contemporary International Cinema (6 films, 2010s-2020s)
- **Purpose**: Test modern movement identification and cultural specificity
- **Key challenges**:
  - Contemporary movements (Dogme 95 influence, Slow Cinema)
  - Cultural authenticity (Korean class dynamics, Danish drinking culture)
  - Technical specificity (cinematographer names, specific techniques)

#### Middle Eastern & Asian Cinema (4 films)
- **Purpose**: Test cross-cultural analysis and movement identification
- **Key challenges**:
  - Regional movements (Iranian New Wave, Hong Kong cinema)
  - Cultural context (Iranian restrictions, colonial history)
  - Technical innovations (Christopher Doyle's cinematography)

#### Latin American Cinema (2 films)
- **Purpose**: Test cultural specificity and technical analysis
- **Key challenges**:
  - Historical context (Stalinist Poland, 1970s Mexico)
  - Personal vs. political narratives
  - Technical innovations (black & white, single cinematographer)

#### Experimental/Avant-garde (3 films)
- **Purpose**: Test analysis of unconventional films
- **Key challenges**:
  - Post-cinema concepts
  - Non-linear narratives
  - Technical experimentation (DV, industrial soundscapes)

#### Documentary-style Fiction (2 films)
- **Purpose**: Test hybrid genre analysis
- **Key challenges**:
  - Meta-documentary techniques
  - Technical innovations (iPhone cinematography)
  - Authentic casting and real-time storytelling

## Expected Failure Modes

### 1. Cinema Movement Misidentification
- **Problem**: Using "indie cinema" or "indie film landscape" for Classical Hollywood films
- **Example**: Citizen Kane described as "indie film" instead of Classical Hollywood
- **Test films**: Citizen Kane, Another Round, Portrait of a Lady on Fire

### 2. Missing Technical Credits
- **Problem**: Not crediting cinematographers for visually innovative films
- **Example**: Missing Gregg Toland (Citizen Kane), Christopher Doyle (In the Mood for Love)
- **Test films**: Citizen Kane, In the Mood for Love, Another Round

### 3. Generic Cultural Context
- **Problem**: Vague mentions like "explores identity" without specifics
- **Example**: Missing Howard Beach incident for Do the Right Thing, Cold War context for Cold War
- **Test films**: Cold War, Parasite, The Handmaiden

### 4. Missing Historical Context
- **Problem**: No mention of historical events that influenced the film
- **Example**: Missing post-war Italy for Bicycle Thieves, Stalinist Poland for Cold War
- **Test films**: Bicycle Thieves, Cold War, Roma

### 5. Generic Technical Descriptions
- **Problem**: "Beautiful cinematography" without specifics
- **Example**: Missing deep focus technique for Citizen Kane, jump cuts for Breathless
- **Test films**: Citizen Kane, Breathless, Portrait of a Lady on Fire

### 6. Missing Narrative Specifics
- **Problem**: Abstract descriptions without concrete examples
- **Example**: "Complex narrative" without explaining complexity
- **Test films**: Inland Empire, The Handmaiden, Stories We Tell

## Success Criteria
A good profile_text should:
1. **Name specific cinema movements** with historical context
2. **Include cinematographer credits** for visually innovative films
3. **Provide cultural/historical context** specific to the film's era and setting
4. **Mention specific techniques** (deep focus, jump cuts, handheld camera)
5. **Reference key plot elements** or iconic moments
6. **Explain what makes the film unique** rather than using generic praise

## Usage
This dataset will be used for:
1. **Human evaluation** to identify failure patterns
2. **Prompt iteration** to address discovered issues
3. **LLM judge calibration** to validate automated evaluation
4. **Scale testing** to ensure improvements work across diverse films
