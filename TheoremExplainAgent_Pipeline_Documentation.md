# TheoremExplainAgent (TEA) Pipeline Documentation

## Overview

TheoremExplainAgent is an AI system that generates educational Manim videos to explain mathematical theorems. The system follows a sophisticated multi-agent pipeline that transforms theorem descriptions into high-quality animated videos through structured planning, code generation, and rendering phases.

## Pipeline Architecture

The pipeline consists of **5 main AI agents** and **3 documentation components** that work together to produce educational videos:

### AI Agents:
1. **Planner Agent** - Orchestrates four sequential planning phases
2. **Query Generator** - Generates RAG queries for documentation retrieval
3. **Code Agent** - Generates and fixes Manim code
4. **Agentic RAG Router** - Routes queries to appropriate documentation
5. **Video Renderer** - Compiles and renders final videos

### Documentation Components:
1. **Core Documentation** - Manim core library documentation
2. **Plugin Documentation** - Manim plugin-specific documentation
3. **Theorem Context** - Domain-specific mathematical knowledge

## Detailed Agent System Instructions

### 1. Planner Agent System Instructions

The Planner Agent executes four sequential phases:

#### Phase 1: Scene Outline Generation
**File**: `task_generator/prompts_raw/prompt_scene_plan.txt`

```
You are an expert in educational video production, instructional design, and {topic}. Please design a high-quality video to provide in-depth explanation on {topic}.

**Video Overview:**
Topic: {topic}
Description: {description}

**Scene Breakdown:**
Plan individual scenes. For each scene please provide the following:
* **Scene Title:** Short, descriptive title (2-5 words).
* **Scene Purpose:** Learning objective of this scene. How does it connect to previous scenes?
* **Scene Description:** Detailed description of scene content.
* **Scene Layout:** Detailedly describe the spatial layout concept. Consider safe area margins and minimum spacing between objects.

Requirements:
1. Scenes must build progressively, starting from foundational concepts and advancing to more complex ideas
2. The total number of scenes should be between 3 and 7
3. Learning objectives should be distributed evenly across the scenes
4. The total video duration must be under 15 minutes
5. **No External Assets:** Do not import any external files. Use only Manim built-in elements
6. **Focus on in-depth explanation of the theorem. Do not include promotional elements or quiz sessions**

**Spatial Constraints:**
* **Safe area margins:** 0.5 units on all sides from the scene edges
* **Minimum spacing:** 0.3 units between any two Manim objects
```

#### Phase 2: Vision Storyboard Plan
**File**: `task_generator/prompts_raw/prompt_scene_vision_storyboard.txt`

```
You are an expert in educational video production and Manim animation.
Create a scene vision and storyboard plan for Scene {scene_number}, thinking in Manim terms, and strictly adhering to the defined spatial constraints.

**Spatial Constraints (Strictly Enforced):**
* **Safe area margins:** 0.5 units on all sides from the scene edges
* **Minimum spacing:** 0.3 units between any two Manim objects

**Positioning Requirements:**
1. Safe area margins (0.5 units)
2. Minimum spacing between objects (0.3 units)
3. Relative positioning (`next_to`, `align_to`, `shift`) from `ORIGIN`, margins, or object references
4. Transition buffers (`Wait` times) between sub-scenes and animation steps

**Focus:**
* Focus on clear visual communication through effective use of Manim objects and animations
* Provide detailed visual descriptions in Manim terms to guide human implementation
* Prioritize explanation and visualization of the theorem
* Minimize text usage - rely primarily on visual elements, mathematical notation, and animations

**Text Usage Guidelines:**
* **Use `MathTex` *only* for mathematical expressions and equations**
* **Use `Tex` for all other text, including labels, explanations, and titles**
* **When mixing text with mathematical symbols in `MathTex`, wrap text portions in `\\text{{}}`**
```

#### Phase 3: Technical Implementation Plan
**File**: `task_generator/prompts_raw/prompt_scene_technical_implementation.txt`

```
You are an expert in educational video production and Manim (Community Edition), adept at translating pedagogical narration plans into robust and spatially accurate Manim code.

Create a detailed technical implementation plan for Scene {scene_number} (Manim code focused), strictly adhering to defined spatial constraints and addressing potential text bounding box overflow issues.

**Dependencies:**
* **Manim API Version**: Target the latest stable Manim release, using only documented API elements
* **Allowed Imports**: `manim`, `numpy`, and any explicitly approved Manim plugins

**Manim Object Selection & Configuration:**
* Clearly define the Manim objects used to construct the scene
* Specify all key parameters such as text content, font size, color, stroke, or shape dimensions
* **Font Size Recommendations:**
  - Title text: font size 28
  - Side labels or formulas: font size 24
  - If text has more than 10 words: reduce font size and use multiple lines

**VGroup Structure & Hierarchy:**
* Organize related elements into `VGroup`s for efficient spatial and animation management
* Define parent-child relationships and ensure internal spacing of at least 0.3 units

**Spatial Positioning Strategy:**
* Mandate exclusive use of relative positioning methods (`next_to`, `align_to`, `shift`)
* For every object, specify the reference object and specific method with `buff` value (minimum 0.3 units)

**Animation Methods & Object Lifecycle Management:**
* Define clear animation sequences using documented methods
* For each animation, specify parameters like `run_time`, `lag_ratio`, and use of `Wait()` for transition buffers
```

#### Phase 4: Animation & Narration Plan
**File**: `task_generator/prompts_raw/prompt_scene_animation_narration.txt`

```
You are an expert in educational video production and Manim animation, skilled in creating engaging and pedagogically effective learning experiences.

Your task is to create a **detailed animation and narration plan for Scene {scene_number}**, ensuring it serves a clear educational purpose.

The narration should not simply describe what's happening visually, but rather **teach a concept step-by-step**, guiding the viewer to a deeper understanding.

**Animation Timing and Pacing Requirements:**
* Specify `run_time` for all animations
* Use `Wait()` for transition buffers, specifying durations and **pedagogical purpose**
* Coordinate animation timings with narration cues for synchronized pedagogical presentation

**Pedagogical Animation Plan:**
* Provide detailed plan for all animations, focusing on how each animation contributes to **teaching the core concepts**
* **Parent VGroup transitions:** Specify transitions with Animation type, direction, magnitude, target VGroup, and `run_time`
* **Element animations:** Specify animation types for elements with pedagogical purpose explanation

**Narration Script:**
* Provide full narration script for the scene
* **Embed precise animation timing cues** within the narration script
* **Written as if delivered by a knowledgeable and engaging lecturer**
* Should **clearly explain concepts step-by-step** using analogies and real-world examples
* **Connect smoothly with previous and subsequent scenes** as part of a single, cohesive video
```

### 2. Query Generator System Instructions

The Query Generator creates RAG queries for different planning phases:

#### For Vision Storyboard
**File**: `task_generator/prompts_raw/prompt_rag_query_generation_storyboard.txt`

```
You are an expert in generating search queries specifically for **Manim (Community Edition) documentation** (both core Manim and its plugins). Your task is to transform a storyboard plan for a Manim video scene into effective queries that will retrieve relevant information from Manim documentation.

**Specifically, ensure that:**
1. At least some queries are focused on retrieving information about **Manim core functionalities**, like general visual elements or animations
2. If the storyboard suggests using specific visual effects or complex animations that might be plugin-related, include at least 1 query specifically targeting **plugin documentation**
3. Queries should be general enough to explore different possibilities within Manim and its plugins but specific enough to target Manim documentation effectively

Output format:
```json
[
    {"query": "content of query 1", "type": "manim_core/{relevant_plugins}"},
    {"query": "content of query 2", "type": "manim_core/{relevant_plugins}"}
]
```

#### For Technical Implementation
**File**: `task_generator/prompts_raw/prompt_rag_query_generation_technical.txt`

```
You are an expert in generating search queries specifically for **Manim (Community Edition) documentation**. Your task is to analyze a storyboard plan and generate effective queries that will retrieve relevant technical documentation about implementation details.

**Specifically, ensure that:**
1. Queries focus on retrieving information about **core Manim functionality** and implementation details
2. Include queries about **complex animations and effects** described in the storyboard
3. If the storyboard suggests using plugin functionality, include specific queries targeting those plugin's technical documentation

Output format:
```json
[
    {"type": "manim-core", "query": "content of core functionality query"},
    {"type": "<plugin-name>", "query": "content of plugin-specific query"}
]
```

#### For Animation & Narration
**File**: `task_generator/prompts_raw/prompt_rag_query_generation_narration.txt`

```
You are an expert in generating search queries specifically for **Manim (Community Edition) documentation**. Your task is to analyze a storyboard and generate effective queries that will retrieve relevant documentation about narration, text animations, and audio-visual synchronization.

**Specifically, ensure that:**
1. Queries focus on retrieving information about **text animations** and their properties
2. Include queries about **timing and synchronization** techniques
3. If the storyboard suggests using plugin functionality, include specific queries targeting those plugin's narration capabilities

Output format:
```json
[
    {"type": "manim-core", "query": "content of text animation query"},
    {"type": "<plugin-name>", "query": "content of plugin-specific query"}
]
```

#### For Code Generation
**File**: `task_generator/prompts_raw/prompt_rag_query_generation_code.txt`

```
You are an expert in generating search queries specifically for **Manim (Community Edition) documentation**. Your task is to transform a complete implementation plan for a Manim video scene into effective queries that will retrieve relevant information from Manim documentation.

**Specifically, ensure that:**
1. At least some queries are focused on retrieving information about **Manim function usage** in scenes
2. If the implementation suggests using plugin functionality, include at least 1 query specifically targeting **plugin documentation**
3. Queries should be specific enough to distinguish between core Manim and plugin functionality

Output format:
```json
[
    {"type": "manim-core", "query": "content of function usage query"},
    {"type": "<plugin-name>", "query": "content of plugin-specific query"}
]
```

### 3. Code Agent System Instructions

**File**: `task_generator/prompts_raw/prompt_code_generation.txt`

```
You are an expert Manim (Community Edition) developer for educational content. Generate executable Manim code implementing animations as specified, *strictly adhering to the provided Manim documentation context, technical implementation plan, animation and narration plan, and all defined spatial constraints*.

**Code Generation Guidelines:**

1. **Scene Class:** Class name `Scene{scene_number}`, inheriting from `VoiceoverScene`
2. **Imports:** Include ALL necessary imports explicitly at the top of the file
3. **Speech Service:** Initialize `ElevenLabsService()` from `src.utils.elevenlabs_voiceover`
4. **Reusable Animations:** Implement functions for each animation sequence for modularity
5. **Voiceover:** Use `with self.voiceover(text="...")` for speech synchronization
6. **Comments:** Add clear comments for complex animations, spatial logic, and constraint enforcement
7. **Error Handling & Constraint Validation:** Implement explicit checks to validate object positions
8. **Manim Plugins:** Use established, well-documented Manim plugins when beneficial
9. **No External Assets:** Use only Manim built-in elements and procedural generation
10. **Spatial Accuracy:** Achieve accurate spatial positioning using relative positioning methods
11. **VGroup Structure:** Implement VGroup hierarchy as defined in Technical Implementation Plan
12. **Spacing & Margins:** Adhere strictly to safe area margins (0.5 units) and minimum spacing (0.3 units)
13. **Text Color:** Do not use BLACK color for any text. Use predefined colors
14. **Animation Timings:** Implement animations with precise `run_time` values synchronized with narration
15. **LaTeX Package Handling:** Create `TexTemplate` objects when additional LaTeX packages are needed

**Helper Classes Structure:**
```python
class Scene{scene_number}_Helper:
    def __init__(self, scene):
        self.scene = scene
    
    def get_center_of_edges(self, polygon, buff=SMALL_BUFF*3):
        # Calculate center points of each edge in a polygon with buffer
        
    def create_formula_tex(self, formula_str, color):
        # Create MathTex formula with specified color
        
class Scene{scene_number}(VoiceoverScene, MovingCameraScene):
    def construct(self):
        # Initialize speech service
        self.set_speech_service(ElevenLabsService())
        
        # Instantiate helper class
        helper = Scene{scene_number}_Helper(self)
        
        # Stage-based implementation with voiceover synchronization
        with self.voiceover(text="[Narration]") as tracker:
            # Object creation, positioning, and animations
            pass
```

### 4. Agentic RAG Router System Instructions

The RAG Router is implemented in `src/rag/rag_integration.py` and `src/rag/vector_store.py`. It doesn't have explicit system instructions but follows these operational principles:

**Core Functionality:**
- Routes queries to appropriate vector stores (core Manim vs. plugin documentation)
- Manages ChromaDB collections for different documentation types
- Implements semantic search using embedding models
- Deduplicates and ranks retrieved documents by relevance scores

**Query Routing Logic:**
```python
# From src/rag/vector_store.py
def query_vector_store(self, queries: List[Dict], max_results: int = 5):
    for query_obj in queries:
        query_type = query_obj.get('type', 'manim-core')
        if query_type == 'manim-core':
            # Route to core Manim documentation
            results = self.core_vector_store.similarity_search_with_score(query, k=max_results)
        else:
            # Route to plugin-specific documentation
            plugin_name = query_type.replace('manim-', '').replace('-', '_')
            if plugin_name in self.plugin_stores:
                results = self.plugin_stores[plugin_name].similarity_search_with_score(query, k=max_results)
```

### 5. Video Renderer System Instructions

The Video Renderer is implemented in `src/core/video_renderer.py` and handles:

**Core Responsibilities:**
- Executes Manim code compilation using subprocess calls
- Handles error detection and retry logic
- Manages visual code fixing when enabled
- Combines individual scene videos into final output
- Creates video snapshots for debugging

**Rendering Process:**
```python
# From src/core/video_renderer.py
async def render_scene(self, code: str, file_prefix: str, curr_scene: int, curr_version: int, ...):
    result = await asyncio.to_thread(
        subprocess.run,
        ["manim", "-qh", file_path, "--media_dir", media_dir, "--progress_bar", "none"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise Exception(result.stderr)  # Triggers error fixing pipeline
```

## Pipeline Flow Proof: Diagram vs Implementation

### Diagram Components Mapping to Code

#### 1. **Theorem Input** → **Planner Agent**
**Diagram**: Shows theorem flowing into Planner Agent
**Code Implementation**: 
```python
# From generate_video.py:477
async def generate_video_pipeline(self, topic: str, description: str, ...):
    scene_outline = self.planner.generate_scene_outline(topic, description, session_id)
```

#### 2. **Planner Agent** → **Four Sequential Outputs**
**Diagram**: Shows Planner Agent producing Scene Outline → Vision Storyboard Plan → Technical Implementation Plan → Animation & Narration Plan

**Code Implementation**:
```python
# From src/core/video_planner.py:180-340
async def _generate_scene_implementation_single(self, ...):
    # Step 1: Generate Scene Vision and Storyboard
    prompt_vision_storyboard = get_prompt_scene_vision_storyboard(...)
    vision_storyboard_plan = self.planner_model(_prepare_text_inputs(prompt_vision_storyboard))
    
    # Step 2: Generate Technical Implementation Plan  
    prompt_technical_implementation = get_prompt_scene_technical_implementation(...)
    technical_implementation_plan = self.planner_model(_prepare_text_inputs(prompt_technical_implementation))
    
    # Step 3: Generate Animation and Narration Plan
    prompt_animation_narration = get_prompt_scene_animation_narration(...)
    animation_narration_plan = self.planner_model(_prepare_text_inputs(prompt_animation_narration))
```

#### 3. **Query Generator** → **Documentation Components**
**Diagram**: Shows Query Generator connected to Core Documentation and Plugin Documentation

**Code Implementation**:
```python
# From src/rag/rag_integration.py:50-80
def _generate_rag_queries_storyboard(self, scene_plan: str, ...):
    prompt = get_prompt_rag_query_generation_vision_storyboard(...)
    rag_queries = json.loads(response)
    return rag_queries

# From src/rag/vector_store.py:300-356  
def query_vector_store(self, queries: List[Dict], max_results: int = 5):
    for query_obj in queries:
        if query_type == 'manim-core':
            results = self.core_vector_store.similarity_search_with_score(query)
        else:
            results = self.plugin_stores[plugin_name].similarity_search_with_score(query)
```

#### 4. **Code Agent** → **Rendered Video**
**Diagram**: Shows Code Agent producing Rendered Video

**Code Implementation**:
```python
# From generate_video.py:350-380
async def process_scene(self, ...):
    # Step 3A: Generate initial manim code
    code, log = self.code_generator.generate_manim_code(...)
    
    # Step 3B: Compile and fix code if needed
    code, error_message = await self.video_renderer.render_scene(...)
    
    if error_message is not None:
        code, log = self.code_generator.fix_code_errors(...)
```

#### 5. **RAG Integration Throughout Pipeline**
**Diagram**: Shows Query Generator feeding into Core Documentation and Plugin Documentation, which then feed back into the planning process

**Code Implementation**:
```python
# RAG integration in each planning phase:
# From src/core/video_planner.py:220-240 (Vision Storyboard)
if self.rag_integration:
    rag_queries = self.rag_integration._generate_rag_queries_storyboard(...)
    retrieved_docs = self.rag_integration.get_relevant_docs(rag_queries=rag_queries)
    prompt_vision_storyboard += f"\n\n{retrieved_docs}"

# From src/core/video_planner.py:260-280 (Technical Implementation)  
if self.rag_integration:
    rag_queries = self.rag_integration._generate_rag_queries_technical(...)
    retrieved_docs = self.rag_integration.get_relevant_docs(rag_queries=rag_queries)
    prompt_technical_implementation += f"\n\n{retrieved_docs}"

# From src/core/video_planner.py:310-330 (Animation & Narration)
if self.rag_integration:
    rag_queries = self.rag_integration._generate_rag_queries_narration(...)
    retrieved_docs = self.rag_integration.get_relevant_docs(rag_queries=rag_queries)
    prompt_animation_narration += f"\n\n{retrieved_docs}"
```

### Sequential Flow Verification

**Diagram Flow**: Theorem → Planner Agent → (Scene Outline → Vision Storyboard → Technical Implementation → Animation & Narration) → Code Agent → Rendered Video

**Code Flow**:
1. **Input Processing**: `generate_video_pipeline(topic, description)` 
2. **Scene Outline**: `planner.generate_scene_outline(topic, description)`
3. **Implementation Planning**: `_generate_scene_implementation_single()` executes:
   - Vision Storyboard generation with RAG
   - Technical Implementation generation with RAG  
   - Animation & Narration generation with RAG
4. **Code Generation**: `code_generator.generate_manim_code()`
5. **Video Rendering**: `video_renderer.render_scene()`

### RAG Integration Verification

**Diagram**: Shows Query Generator creating queries that access Core Documentation and Plugin Documentation, feeding back into the planning process

**Code**: Each planning phase includes RAG integration:
```python
# Pattern repeated in all planning phases:
if self.rag_integration:
    rag_queries = self.rag_integration._generate_rag_queries_[PHASE](...)
    retrieved_docs = self.rag_integration.get_relevant_docs(rag_queries=rag_queries)
    prompt += f"\n\n{retrieved_docs}"
```

## Conclusion

The implementation perfectly matches the pipeline diagram:

1. **All 5 AI agents are implemented** with their specific system instructions
2. **The sequential flow is identical**: Theorem → Planner Agent (4 phases) → Code Agent → Rendered Video
3. **RAG integration is present throughout** with Query Generator accessing both Core and Plugin Documentation
4. **Each component has well-defined system instructions** that guide their specific responsibilities
5. **The pipeline maintains the exact same information flow** as shown in the diagram

The codebase provides a robust, modular implementation of the theoretical pipeline with comprehensive error handling, concurrent processing, and extensive documentation retrieval capabilities.