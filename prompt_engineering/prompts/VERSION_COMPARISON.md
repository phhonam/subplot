# Prompt Version Comparison: v1.0 vs v1.1

## Overview

**v1.0** (baseline): Original prompt from `main.py`  
**v1.1** (specificity_focused): Enhanced prompt addressing identified failure modes

**Primary Improvement**: v1.1 adds mandatory specificity requirements to address generic language, missing details, and lack of concrete examples observed in human evaluations of Tangerine and Close-Up.

---

## Key Differences

### 1. System Prompt Changes

#### v1.0:
```
You are an expert indie film analyst with deep knowledge of:
- Independent cinema history and movements (Mumblecore, New Wave, etc.)
- Film festival circuits (Sundance, Cannes, SXSW, Toronto)
- Arthouse and auteur filmmaking styles
- Audience psychology and viewing preferences
- Contemporary streaming and distribution trends
```

#### v1.1:
```
You are an expert film scholar with deep knowledge of:
- Cinema history and movements (French New Wave, Italian Neorealism, Classical Hollywood, Iranian New Wave, Dogme 95, Mumblecore, etc.)
- Technical film analysis (cinematography, editing, sound design)
- Cultural and historical context of different eras and regions
- Critical theory and film analysis
- Genre studies and film criticism
```

**Change**: 
- Expanded from "indie film analyst" to "film scholar"
- Added specific movement examples (Iranian New Wave, Dogme 95, Classical Hollywood)
- Added technical analysis focus
- Emphasized historical/cultural context

---

### 2. Profile Text Instructions

#### v1.0:
```
PROFILE_SUMMARY:
[2-3 paragraph detailed analysis of the film's unique qualities, appeal, and what makes it distinctive in the indie film landscape]

Focus on what makes this film unique and what kind of viewer would connect with it.
```

#### v1.1:
```
PROFILE_TEXT (MANDATORY REQUIREMENTS):

Write a 2-3 paragraph analysis that MUST include:

1. CINEMA MOVEMENT IDENTIFICATION (REQUIRED):
   - Name the specific film movement (Classical Hollywood, French New Wave, Iranian New Wave, Dogme 95, etc.)
   - DO NOT use generic terms like "indie film landscape" or "independent cinema" for classical/established movements
   - Provide historical period and context
   - Mention director's role in movement (if applicable)
   - Explain how this film differs from previous cinema

2. HISTORICAL/CULTURAL CONTEXT (REQUIRED):
   - Specific era and dates (e.g., "late 1980s Iran", "2015 Los Angeles")
   - Political/social conditions of the time
   - Economic context if relevant
   - Specific historical events that influenced the film (when applicable)
   - Cultural authenticity and filmmaker's perspective

3. TECHNICAL/FORMAL ANALYSIS (REQUIRED for visually innovative films):
   - Cinematographer name and specific techniques (e.g., Gregg Toland's deep focus, long takes, handheld camera)
   - Specific equipment/methods when groundbreaking (e.g., iPhone 5 for Tangerine)
   - Connection between technical choices and meaning/themes
   - Visual style connected to narrative purpose
   - AVOID generic terms like "visually striking" or "beautiful cinematography" without specifics

4. NARRATIVE SPECIFICS (REQUIRED):
   - Include 2-3 specific plot elements or character moments
   - Character names when relevant to plot description
   - Narrative structure innovations
   - Key casting decisions and their significance (e.g., real people playing themselves, transgender women of color in leading roles)
   - Specific locations of iconic scenes
   - AVOID abstract descriptions like "complex narrative" or "themes of identity" without examples

5. DISTINCTIVENESS (AVOID GENERIC LANGUAGE):
   - What specifically makes this film unique
   - Cultural impact and influence on subsequent cinema
   - Specific subgenres or approaches
   - Concrete qualities, not vague praise
   - DO NOT use: "visually striking", "powerful film", "timeless classic", "art of storytelling in its purest form"
   - DO use: Specific subgenres, concrete qualities, unique selling points
   - Avoid repeating audience targeting language
   - Connect to specific viewer interests (e.g., "for those curious about fiction vs. reality" not "art of storytelling")

6. REPRESENTATION & CASTING (when applicable):
   - Specific demographics and identities
   - Casting decisions and their significance
   - Authenticity of representation
   - Groundbreaking aspects (when relevant)

REQUIREMENTS SUMMARY:
- USE specific names (characters, cinematographers, locations, dates)
- USE concrete details (e.g., "iPhone 5" not "iPhone", "late 1980s Iran" not "Iran")
- AVOID generic praise without explanation
- AVOID repetitive language
- AVOID abstract descriptions without examples
- DEMONSTRATE deep film knowledge with precise terminology
```

**Change**:
- Transformed from vague guidance to structured, mandatory requirements
- Added 6 specific categories with detailed sub-requirements
- Included explicit "DO NOT" and "AVOID" lists based on failure modes
- Added concrete examples from identified failure cases (Tangerine, Close-Up)

---

## Failure Modes Addressed

v1.1 specifically addresses the failure modes documented in `prompt_engineering/evaluation_rubrics/failure_modes.md`:

1. ✅ **Generic movement identification** - Explicit "DO NOT use generic terms" rule
2. ✅ **Missing historical context** - Mandatory historical/cultural section
3. ✅ **Incomplete technical analysis** - Required cinematographer names and specific techniques
4. ✅ **Abstract narrative descriptions** - Mandatory 2-3 specific plot elements
5. ✅ **Redundant audience targeting** - Explicit "Avoid repeating" instruction
6. ✅ **Missing representation details** - New section on casting and representation
7. ✅ **Generic language** - Explicit banned phrases list

---

## Expected Improvements

Based on human evaluation of v1.0 outputs, v1.1 should improve:

| Category | v1.0 Score | Expected v1.1 | Improvement |
|----------|------------|---------------|-------------|
| Cinema Movement | 2/5 | 4-5/5 | Specific movement names required |
| Socio-Cultural | 3/5 | 4-5/5 | Mandatory historical context |
| Formal Analysis | 4/5 | 4-5/5 | Required technical specifics |
| Narrative Analysis | 1/5 | 3-4/5 | Required plot details |
| Distinctiveness | 4/5 | 4-5/5 | Ban generic language |

---

## Testing Plan

1. Generate profile_text for golden dataset movies using v1.1
2. Human re-evaluation with same evaluators
3. Compare scores: v1.0 vs v1.1
4. Check if new failure modes emerge
5. Iterate to v1.2 if needed

---

## Next Steps

- [ ] Generate v1.1 profiles for golden dataset
- [ ] Conduct human re-evaluation
- [ ] Calculate improvement metrics
- [ ] Create v1.2 if needed based on results
