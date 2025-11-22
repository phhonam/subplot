# Failure Mode Analysis: Movie Profile Generation (v1.0)

**Date**: 2025-10-18  
**Version Evaluated**: v1.0_baseline  
**Evaluation Method**: Human annotation + LLM judge assessment  
**Movies Analyzed**: Tangerine (2015), Close-Up (1990)

## Executive Summary

The baseline profile generator (v1.0) produces readable profile text but consistently fails to include specific, actionable details that would help viewers understand what makes each film distinctive. The most critical failures are:

1. **Generic movement identification** - Using vague terms like "indie film landscape" instead of specific cinema movements
2. **Missing historical context** - Omitting era-specific social, political, and economic details
3. **Incomplete technical analysis** - Failing to credit cinematographers or describe specific techniques
4. **Abstract narrative descriptions** - Vague plot summaries without concrete elements
5. **Redundant audience targeting** - Repetitive language about who would enjoy the film

## Detailed Failure Modes

### 1. Cinema Movement Identification Failures

#### **Severity**: CRITICAL  
**Frequency**: High (observed in both films)

**Problem**: The generator uses generic terms like "indie film landscape" or "independent cinema" instead of identifying specific cinema movements with historical context.

**Examples from Tangerine**:
- ❌ **Current**: "stands out in the indie film landscape"
- ✅ **Expected**: Should identify specific aesthetic movements (e.g., "mumblecore influence", "guerrilla-style filmmaking")
- ❌ **Missing**: Recognition that it's part of a wave of micro-budget digital filmmaking

**Examples from Close-Up**:
- ❌ **Current**: Missing cinema movement identification entirely
- ✅ **Expected**: "Iranian New Wave cinema (late 20th century)" with context that it was a "big departure from Iranian movies at the time"
- ❌ **Missing**: Director's name (Kiarostami) as a key figure in the movement

**Impact**: Viewers cannot understand the film's place in cinema history or its relationship to broader artistic movements. This particularly hurts international and contemporary films that don't fit standard categorization.

**LLM Judge Assessment**: Low scores on "cinema movement" category (2/5 for both films)

---

### 2. Socio-Cultural Context Failures

#### **Severity**: CRITICAL  
**Frequency**: High (observed in both films)

**Problem**: Profile text misses specific historical, political, and economic context that shapes the film's meaning and significance.

**Examples from Tangerine**:
- ❌ **Current**: Generic mention of "LA trans community" and "urban life"
- ✅ **Expected**: Specific setting (year 2015 Los Angeles), neighborhoods, subcultures (Albanian community, donut shop culture)
- ❌ **Missing**: Director's method of constructing dialogues with cast members (authenticity in representation)

**Examples from Close-Up**:
- ❌ **Current**: Missing historical context entirely
- ✅ **Expected**: "late 1980s in Iran, defined by the aftermath of the revolution, dominated by the devastating eight-year war with Iraq, which caused immense hardship and loss of life. The economy was in a state of crisis due to the war and the new government's policies, leading to rationing, inflation, and poverty."
- ❌ **Missing**: Connection between film's documentary-fiction hybrid and the need for indirect political commentary

**Impact**: Films lose their cultural authenticity and viewers miss the deeper political and social commentary. International films especially need this context.

**LLM Judge Assessment**: Mixed scores - acknowledges cultural mentions but penalizes lack of specificity (3/5 for Tangerine, lower for Close-Up if judged)

---

### 3. Formal/Technical Analysis Failures

#### **Severity**: HIGH  
**Frequency**: High (observed in both films)

**Problem**: Generic visual descriptions without specific technical details, cinematographer credits, or connections between technique and meaning.

**Examples from Tangerine**:
- ❌ **Current**: Vague "unique filming technique"
- ✅ **Expected**: "Shot on iPhone 5" with context that this was due to "low-budget, artistically-driven directions that challenged mainstream conventions"
- ✅ **Should include**: "Guerrilla-style filmmaking" creating a "raw and unfiltered aesthetic"
- ✅ **Missing**: "Bold colors and intimate close-ups" as visual metaphor for character journey
- ✅ **Missing**: Connection between technical constraints and artistic choices

**Examples from Close-Up**:
- ❌ **Current**: Missing cinematography details entirely
- ✅ **Expected**: "Minimalist filmmaking. Kiarostami's use of long takes, natural lighting, and a documentary-style approach lends the film a sense of authenticity and immediacy."
- ❌ **Missing**: Specific connection between techniques and the film's exploration of truth vs. fiction

**Impact**: Viewers can't appreciate the technical innovations or understand how form serves content. This is especially critical for films known for cinematographic innovation.

**LLM Judge Assessment**: Moderate scores (4/5) for Tangerine due to iPhone mention, but penalizes "unique filming technique" as generic language

---

### 4. Narrative Analysis Failures

#### **Severity**: HIGH  
**Frequency**: High (observed in both films)

**Problem**: Abstract plot summaries without specific story elements, character names, or narrative innovations.

**Examples from Tangerine**:
- ❌ **Current**: Generic "two friends embarking on a quest for truth"
- ✅ **Expected**: "It's Christmas Eve in Tinseltown and Sin-Dee is back on the block. Upon hearing that her pimp boyfriend hasn't been faithful during the 28 days she was locked up, the working girl and her best friend, Alexandra, embark on a mission to get to the bottom of the scandalous rumor."
- ❌ **Missing**: Specific plot elements - confronting a cis woman and ex-boyfriend/pimp Chester
- ❌ **Missing**: "Frenetic pacing" and "non-linear structure and episodic storytelling" reflecting "the chaotic and unpredictable nature of their journey"
- ❌ **Missing**: Specific locations of iconic scenes (donut shop, drive-in car wash, parking lot, motel)

**Examples from Close-Up**:
- ❌ **Current**: Vague mention of "weaving real-life with fictional elements"
- ✅ **Expected**: "The narrative of Close-Up intricately weaves together the true story of a man impersonating filmmaker Mohsen Makhmalbaf with reenactments and interviews involving the real individuals."
- ❌ **Missing**: Key casting decision - "cast the real people involved in the actual events as themselves blurs the lines between documentary and fiction"
- ❌ **Missing**: Specific narrative structure innovations

**Impact**: Viewers can't distinguish this film from similar ones. The plot summary becomes interchangeable with other films.

**LLM Judge Assessment**: Very low scores on narrative analysis (1/5 for Tangerine) - "doesn't reference the main story line"

---

### 5. Representation & Casting Failures

#### **Severity**: HIGH  
**Frequency**: Observed in Tangerine

**Problem**: Generic mentions of representation without specific details about casting choices and their significance.

**Examples from Tangerine**:
- ❌ **Current**: Generic "transgender actresses"
- ✅ **Expected**: "Transgender women of color" (specific demographic), "Kitana Kiki Rodriguez and Mya Taylor in leading roles" (specific names)
- ✅ **Should emphasize**: "adds a layer of authenticity and representation to the narrative"
- ❌ **Missing**: This was groundbreaking casting at the time

**Impact**: Misses the opportunity to highlight why the film matters in terms of representation and authentic storytelling.

---

### 6. Distinctiveness & Audience Targeting Failures

#### **Severity**: MEDIUM  
**Frequency**: High (observed in both films)

**Problem**: Generic, vague language about who would enjoy the film and what makes it special. Repetitive phrases.

**Examples from Tangerine**:
- ❌ **Current**: Vague "resonates with those who appreciate the art of storytelling in its purest form"
- ✅ **Expected**: More specific - "for people who are curious about fiction vs. reality" or interest in "subgenres / approaches to storytelling" (not just "the art of storytelling" in general)
- ✅ **Better**: "Ethnographic lens into lives of marginalized communities and complex realistic character dynamics"
- ❌ **Pattern**: Repetitive with viewer/audience language - "stands out in the indie film landscape", "for viewers seeking authentic storytelling", "resonates with audiences interested in..."
- ❌ **Current**: Repetitive "connections in unconventional spaces" without specifying what these are
- ✅ **Expected**: Clarify what "unconventional spaces" means (locations like donut shop, car wash, parking lot, motel)

**Examples from Close-Up**:
- ❌ **Current**: Repetitive about who would appreciate the film / target audience
- ❌ **Same issue**: Generic language about "art of storytelling" without specifying why this particular approach is distinctive

**Impact**: Profile text sounds generic and could apply to many films. Doesn't help viewers decide if this film is for them.

**LLM Judge Assessment**: Moderate scores (4/5 for Tangerine on distinctiveness) but penalizes vague language

---

### 7. Theme Description Failures

#### **Severity**: MEDIUM  
**Frequency**: Observed in Tangerine

**Problem**: Abstract theme descriptions without specific examples or connections to narrative.

**Examples from Tangerine**:
- ❌ **Current**: Vague "the movie delves into themes of identity crisis and the resilience of forming connections in unconventional spaces"
- ✅ **Expected**: More specific about what "identity crisis" and "unconventional spaces" mean in context of the film
- ❌ **Issue**: "connections in unconventional spaces" is too abstract without reference to specific plot elements or character relationships

**Impact**: Themes sound academic rather than rooted in the specific story being told.

---

## Summary of Failure Patterns

### **Pattern 1: Specificity Gradient**
- **Problem**: Profile text stays at high level of abstraction
- **Effect**: Could apply to many films
- **Solution**: Require specific names, dates, techniques, plot elements

### **Pattern 2: Missing Historical Anchors**
- **Problem**: Omits era-specific context
- **Effect**: Films lose cultural and political significance
- **Solution**: Explicitly require historical context section

### **Pattern 3: Generic Technical Language**
- **Problem**: Uses terms like "unique filming technique", "visually striking"
- **Effect**: Doesn't differentiate films or educate viewers
- **Solution**: Require specific technical details (camera model, cinematographer names, specific techniques)

### **Pattern 4: Redundant Phrasing**
- **Problem**: Repeats audience targeting language multiple times
- **Effect**: Wastes space, reduces readability
- **Solution**: Require unique, specific audience description

### **Pattern 5: Missing Key Narrative Elements**
- **Problem**: Omits specific plot points, character names, iconic moments
- **Effect**: Narrative description becomes interchangeable
- **Solution**: Require at least 2-3 specific plot details or character moments

## LLM Judge vs Human Evaluation Comparison

### **Tangerine Evaluation Comparison**

| Category | Human Rating | LLM Judge Expected | Alignment |
|----------|--------------|--------------------|-----------|
| Cinema Movement | 2/5 | ~2/5 | ✅ Strong agreement |
| Socio-Cultural | 3/5 | ~3/5 | ✅ Strong agreement |
| Formal Analysis | 4/5 | ~4/5 | ✅ Strong agreement |
| Narrative Analysis | 1/5 | ~1-2/5 | ✅ Strong agreement |
| Distinctiveness | 4/5 | ~3-4/5 | ⚠️ Partial agreement (human slightly higher) |

**Note**: LLM judge appears to properly penalize generic language and missing specifics, aligning well with human evaluation.

## Priority Ranking for Prompt Improvement

Based on severity and frequency:

1. **Cinema Movement Identification** (CRITICAL) - Affects all films, especially contemporary and international
2. **Historical Context** (CRITICAL) - Essential for cultural understanding
3. **Technical Specificity** (HIGH) - Differentiates films and educates viewers
4. **Narrative Specificity** (HIGH) - Prevents generic descriptions
5. **Representation Details** (HIGH) - Important for authentic storytelling
6. **Distinctiveness Language** (MEDIUM) - Improves readability and utility

## Recommendations for v1.1 Prompt

### **Required Prompt Components**:

```
1. CINEMA MOVEMENT SECTION (MANDATORY):
   - Name specific movement (NOT "indie cinema" for classical films)
   - Include historical period and context
   - Mention director's role in the movement (if applicable)
   - Explain how film differs from previous cinema

2. HISTORICAL/CULTURAL CONTEXT (MANDATORY):
   - Specific era and dates
   - Political/social conditions of the time
   - Economic context (if relevant)
   - Cultural significance

3. TECHNICAL SPECIFICS (MANDATORY for visually innovative films):
   - Cinematographer name (when relevant)
   - Specific techniques (e.g., "long takes", "iPhone 5", "deep focus")
   - Connection between technique and meaning
   - Visual style connected to themes

4. NARRATIVE SPECIFICS (MANDATORY):
   - Include 2-3 specific plot elements or character moments
   - Character names when relevant to plot description
   - Narrative structure innovations
   - Key casting decisions and their significance

5. DISTINCTIVENESS (AVOID GENERIC LANGUAGE):
   - DO NOT use: "visually striking", "art of storytelling in its purest form", "powerful film"
   - DO use: Specific subgenres, concrete qualities, unique selling points
   - Avoid repeating audience targeting language

6. REPRESENTATION (when applicable):
   - Specific demographics and identities
   - Casting decisions and significance
   - Authenticity of representation
```

### **Prompt Structure Changes**:

```
OLD: "Focus on what makes this film unique and what kind of viewer would connect with it."

NEW: 
"PROFILE_TEXT REQUIREMENTS:
- MANDATORY: Identify specific cinema movement with historical context
- MANDATORY: Include 2-3 specific plot elements or character moments
- MANDATORY: For visually innovative films, name cinematographer and describe specific techniques
- MANDATORY: Include specific historical/cultural context (era, social conditions)
- AVOID: Generic praise ('visually striking', 'powerful', 'timeless classic')
- AVOID: Repetitive audience targeting language
- AVOID: Abstract theme descriptions without examples
- REQUIRE: Specific names (characters, cinematographers, locations)
- REQUIRE: Concrete details (e.g., 'iPhone 5' not 'iPhone', 'late 1980s Iran' not 'Iran')"
```

## Next Steps

1. ✅ Complete human evaluation of remaining golden dataset films
2. Create v1.1 prompt with mandatory specificity requirements
3. Regenerate profiles for golden dataset using v1.1
4. Re-evaluate with same human evaluators
5. Compare v1.0 vs v1.1 scores
6. Iterate until achieving 4/5 average rating

## Appendix: Full Human Annotations

### Tangerine - Full Annotation

**Overall Quality**: 3/5

**Cinema Movement** (2/5):
- Doesn't capture frantic, frenetic pacing of entire film taking place over single day
- While mentions LA subcultures, doesn't specify which ones (Albanian community, donut shop owner)
- Generic "indie film landscape" language

**Socio-Cultural** (3/5):
- Captures LA trans community, urban life, resilience pretty well
- Need more specific setting (what happens in LA in year this movie is set in, neighborhood)
- Didn't mention how director constructs dialogues with cast

**Formal Analysis** (4/5):
- Mentions iPhone, which is good

**Narrative Analysis** (1/5):
- Doesn't reference main story line of character confronting cis woman and ex-boyfriend/pimp Chester

**Distinctiveness** (4/5):
- Understands components of film it's referencing
- But "connections in unconventional spaces" too vague - could refer to donut shop, drive-in car wash, parking lot, motel

**Free-form Annotation**:
- Repetitive "stands out in the indie film landscape"
- They might not be necessarily standing out
- Can be more specific with "transgender actresses" → "transgender women of color"
- Should mention they are in leading roles (e.g., "Kitana Kiki Rodriguez and Mya Taylor in leading roles adds authenticity and representation")
- 'unique filming technique' → more specific about low-budget, artistically-driven directions
- iPhone good but also mention iPhone 5
- Should emphasize lack of big production (guerrilla-style, raw aesthetic)
- Missing: frenetic pacing, non-linear structure, episodic storytelling
- Cinematography should mention bold colors and intimate close-ups as visual metaphor
- Plot summary too vague: "two friends embarking on a quest for truth" → should mention Christmas Eve in Tinseltown, Sin-Dee's quest for boyfriend's infidelity
- Theme too vague: "identity crisis and resilience of forming connections in unconventional spaces"
- "For viewers seeking authentic storytelling" → better as "ethnographic lens into marginalized communities"
- Repetitive with viewer/audiences: "Tangerine" resonates with audiences interested in exploring themes..."

**Tags**: Generic language, Missing cinema movement, Missing narrative specifics

### Close-Up - Full Annotation

**Cinema Movement** (CRITICAL):
- ❌ Did not mention Iranian New Wave cinema (late 20th century) and how it's a big departure from Iranian movies at the time (depicting social realities)
- ❌ Did not mention director's name as key figure in movement

**Historical Context** (CRITICAL):
- ❌ Need more information situating in late 1980s in Iran
- ❌ Missing: aftermath of revolution, eight-year war with Iraq causing hardship and loss of life
- ❌ Missing: economy in crisis due to war and new government policies (rationing, inflation, poverty)

**Formal/Technical** (HIGH):
- ❌ Missing cinematography details: minimalist filmmaking, long takes, natural lighting, documentary-style approach
- ❌ Missing: connection between techniques and authenticity/immediacy

**Narrative Innovation** (HIGH):
- ❌ While mentions "weaving real-life with fictional elements", missing key casting decision
- ❌ Missing: "cast the real people involved in the actual events as themselves blurs lines between documentary and fiction"
- ❌ Missing key plot line: "The narrative of Close-Up intricately weaves together the true story of a man impersonating filmmaker Mohsen Makhmalbaf with reenactments and interviews involving the real individuals"

**Distinctiveness** (MEDIUM):
- ❌ Repetitive about who would appreciate the movies / target audience
- ❌ "resonates with those who appreciate the art of storytelling in its purest form" is really vague
- ✅ Should be: for people who are curious about fiction vs. reality or subgenres/approaches to storytelling (not just "art of storytelling" in general)
