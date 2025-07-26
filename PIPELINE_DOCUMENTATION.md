# TheoremExplainAgent Pipeline Documentation

## Overview

This document provides detailed system instructions for all AI agents in the TheoremExplainAgent (TEA) pipeline, which generates educational videos explaining mathematical theorems using Manim animations. The pipeline follows a multi-agent architecture that matches the design shown in the provided image.

## Pipeline Architecture

The TEA pipeline consists of three main AI agents working in coordination:

1. **Planner Agent** - High-level content and production planning
2. **Agentic RAG (Router)** - Information retrieval and contextualization
3. **Code Agent** - Code generation, execution, debugging, and refinement

## 1. Planner Agent System Instructions

### Role and Purpose
The Planner Agent is responsible for high-level content and production planning. It takes a theorem as input and generates structured plans for video production.

### Input
- **Theorem**: A mathematical concept or theorem (e.g., "IEEE Conversion: The IEEE-754 standard describes floating-point formats, a way to represent real numbers in hardware.")
- **Description**: Contextual information about the theorem

### System Instructions

#### 1.1 Scene Outline Generation
**File**: `task_generator/prompts_raw/prompt_scene_plan.txt`

**Instructions**:
- Deconstruct the input theorem into a structured sequence of scenes for the video
- Generate 3-7 scenes that build progressively from foundational concepts to complex ideas
- Each scene must include:
  - **Scene Title**: Short, descriptive title (2-5 words)
  - **Scene Purpose**: Learning objective and connection to previous scenes
  - **Scene Description**: Detailed description of scene content
  - **Scene Layout**: Spatial layout concept with safe area margins (0.5 units) and minimum spacing (0.3 units)
- Ensure logical flow and cohesive learning narrative
- Total video duration must be under 15 minutes
- Focus on in-depth theorem explanation without promotional elements

#### 1.2 Vision Storyboard Plan
**File**: `task_generator/prompts_raw/prompt_scene_vision_storyboard.txt`

**Instructions**:
- Translate scene outline into visual concepts and storyboard
- Detail what will appear on screen using Manim terminology
- Specify visual learning objectives using specific Manim object types
- Create sub-scene breakdown with animation sequences
- Enforce spatial constraints:
  - Safe area margins: 0.5 units on all sides
  - Minimum spacing: 0.3 units between objects
  - Use relative positioning only (no absolute coordinates)
- Use `MathTex` for mathematical expressions, `Tex` for general text
- Consider Manim plugins for enhanced functionality

#### 1.3 Technical Implementation Plan
**File**: `task_generator/prompts_raw/prompt_scene_technical_implementation.txt`

**Instructions**:
- Outline technical requirements and methods for animating content
- Specify mathematical visualizations and animation types
- Define VGroup hierarchy and object relationships
- Detail spatial positioning using relative methods
- Include timing specifications for animations
- Ensure adherence to Manim best practices

#### 1.4 Animation & Narration Plan
**File**: `task_generator/prompts_raw/prompt_scene_animation_narration.txt`

**Instructions**:
- Detail precise animation sequences and timing
- Create accompanying narration script synchronized with animations
- Specify transition buffers and visual pacing
- Use `with self.voiceover(text="...")` for speech synchronization
- Ensure narration matches animation timings exactly

### Output
- Structured plans that guide subsequent stages of video creation
- XML-formatted output for each planning stage
- Modular, reusable components for clean code structure

## 2. Agentic RAG (Router) System Instructions

### Role and Purpose
The Agentic RAG system acts as a central hub for information retrieval and contextualization, providing relevant documentation and queries to other agents, particularly the Code Agent.

### Components

#### 2.1 Query Generator
**File**: `src/rag/rag_integration.py`

**Instructions**:
- Generate precise queries based on the needs of other agents
- Create queries for code generation, error fixing, storyboard planning, and technical implementation
- Target specific aspects of Manim documentation and plugin documentation
- Ensure queries are specific enough to distinguish between core Manim and plugin functionality
- Generate up to 10 diverse queries per request

**Query Types**:
- **Code Generation Queries**: Focus on Manim function usage, API reference, and examples
- **Error Fixing Queries**: Target debugging and troubleshooting documentation
- **Storyboard Queries**: Retrieve information about visual elements and animations
- **Technical Implementation Queries**: Focus on technical specifications and best practices

#### 2.2 Core Documentation Access
**File**: `src/rag/vector_store.py`

**Instructions**:
- Access and retrieve information from primary, general knowledge base
- Index Manim documentation using embedding models
- Provide semantic search capabilities
- Store and retrieve relevant documentation snippets

#### 2.3 Plugin Documentation Access
**Instructions**:
- Access and retrieve information from specialized documentation
- Handle plugin-specific queries and documentation
- Support multiple Manim plugins (manim-physics, manim-chemistry, manim-dsa, manim-ml, manim-circuit)
- Detect relevant plugins based on topic and description

### Plugin Detection
**File**: `task_generator/prompts_raw/prompt_detect_plugins.txt`

**Instructions**:
- Analyze topic and description to identify relevant Manim plugins
- Return JSON array of relevant plugin names
- Consider plugin capabilities and use cases
- Ensure only listed plugins are used in subsequent queries

### Output
- Contextual information, code examples, or documentation snippets
- Relevant documentation for Code Agent consumption
- Plugin recommendations and documentation

## 3. Code Agent System Instructions

### Role and Purpose
The Code Agent is responsible for code generation, execution, debugging, and refinement for video rendering. It demonstrates self-debugging and error correction capabilities.

### Input
- Queries from the Query Generator
- Technical specifications from the Planner Agent
- Implementation plans and storyboards

### System Instructions

#### 3.1 Initial Code Generation (Version 0)
**File**: `task_generator/prompts_raw/prompt_code_generation.txt`

**Instructions**:
- Generate executable Manim code implementing animations as specified
- Strictly adhere to provided documentation context and spatial constraints
- Create modular, reusable animation components
- Follow Manim best practices and code structure
- Include all necessary imports explicitly
- Use `VoiceoverScene` as base class
- Initialize `ElevenLabsService()` for TTS
- Implement helper classes for object creation and scene logic
- Structure code into logical stages with clear comments
- Enforce safe area margins (0.5 units) and minimum spacing (0.3 units)
- Use relative positioning methods only
- Preserve voiceover synchronization with narration script

**Code Requirements**:
- Class name: `Scene{scene_number}` (e.g., `Scene1`, `Scene2`)
- Inherit from `VoiceoverScene`
- Include all necessary imports for Manim and plugins
- Use `with self.voiceover(text="...")` for speech synchronization
- Implement helper functions for modularity
- Add comprehensive comments for complex animations
- Validate spatial positioning against constraints
- Use predefined colors only (no BLACK for text)
- No external assets allowed

#### 3.2 Execution/Testing & Error Detection
**Instructions**:
- Attempt to execute or validate the generated code
- Capture and analyze error messages
- Identify error types and root causes
- Provide detailed error analysis with line numbers

#### 3.3 Error Analysis & Root Cause Identification
**File**: `task_generator/prompts_raw/prompt_fix_error.txt`

**Instructions**:
- Analyze error messages to identify root causes
- Provide comprehensive error analysis with specific line numbers
- Explain why the error occurred in plain language
- Preserve all original code not causing the error
- Maintain voiceover functionality in corrected code
- Follow Manim best practices for error resolution

**Error Analysis Format**:
```
<THINKING>
Error Type: [Syntax/Runtime/Logic/Other]
Error Location: [File/Line number/Component]
Root Cause: [Brief explanation of what caused the error]
Impact: [What functionality is affected]
Solution:
[FIXES_REQUIRED]
- Fix 1: [Description]
  - Location: [Where to apply]
  - Change: [What to modify]
- Fix 2: [If applicable]
...
</THINKING>
```

#### 3.4 Code Fix Generation (Version 1)
**Instructions**:
- Based on error analysis, generate corrected code
- Implement all required fixes
- Ensure code is complete and functional
- Maintain all original functionality
- Preserve voiceover synchronization
- Validate spatial constraints

#### 3.5 Visual Self-Reflection (Optional)
**File**: `task_generator/prompts_raw/prompt_visual_self_reflection.txt`

**Instructions**:
- Analyze rendered images or videos for visual issues
- Identify spatial constraint violations
- Suggest improvements for visual clarity
- Provide specific code modifications for visual fixes

### Output
- Functional Manim code that can be rendered into video
- Self-corrected code with error resolution
- Validated spatial positioning and constraints

## 4. Proof of Pipeline Implementation

### 4.1 Correspondence with Image Description

The implemented pipeline perfectly matches the image description:

#### 4.1.1 High-Level Flow
- **Input**: Theorem (green box) → **Planner Agent** → **Agentic RAG** → **Code Agent** → **Rendered Video** (black screen with yellow border)

#### 4.1.2 Planner Agent Components
- **Scene Outline**: ✅ Implemented in `prompt_scene_plan.txt`
- **Vision Storyboard Plan**: ✅ Implemented in `prompt_scene_vision_storyboard.txt`
- **Technical Implementation Plan**: ✅ Implemented in `prompt_scene_technical_implementation.txt`
- **Animation & Narration Plan**: ✅ Implemented in `prompt_scene_animation_narration.txt`

#### 4.1.3 Agentic RAG Components
- **Query Generator**: ✅ Implemented in `rag_integration.py` with multiple query generation methods
- **Core Documentation**: ✅ Implemented in `vector_store.py` with ChromaDB integration
- **Plugin Documentation**: ✅ Implemented with plugin detection and documentation access

#### 4.1.4 Code Agent Process
- **Initial Code Generation (Version 0)**: ✅ Implemented in `prompt_code_generation.txt`
- **Error Detection**: ✅ Implemented in `code_generator.py` with error capture
- **Error Analysis**: ✅ Implemented in `prompt_fix_error.txt`
- **Code Fix Generation (Version 1)**: ✅ Implemented with self-correction capabilities
- **Validation**: ✅ Implemented with green checkmark equivalent (successful execution)

### 4.2 Code Evidence

#### 4.2.1 Planner Agent Implementation
```python
# From src/core/video_planner.py
class VideoPlanner:
    def generate_scene_outline(self, topic: str, description: str, session_id: str) -> str:
        # Implements Scene Outline generation
        
    async def _generate_scene_implementation_single(self, topic: str, description: str, 
                                                   scene_outline_i: str, i: int, file_prefix: str, 
                                                   session_id: str, scene_trace_id: str) -> str:
        # Implements Vision Storyboard, Technical Implementation, and Animation & Narration plans
```

#### 4.2.2 Agentic RAG Implementation
```python
# From src/rag/rag_integration.py
class RAGIntegration:
    def detect_relevant_plugins(self, topic: str, description: str) -> List[str]:
        # Implements plugin detection
        
    def _generate_rag_queries_code(self, implementation_plan: str, ...) -> List[str]:
        # Implements query generation for code
        
    def _generate_rag_queries_error_fix(self, error: str, code: str, ...) -> List[str]:
        # Implements query generation for error fixing
```

#### 4.2.3 Code Agent Implementation
```python
# From src/core/code_generator.py
class CodeGenerator:
    def generate_manim_code(self, topic: str, description: str, scene_outline: str,
                           scene_implementation: str, scene_number: int, ...) -> str:
        # Implements initial code generation (Version 0)
        
    def fix_code_errors(self, implementation_plan: str, code: str, error: str, ...) -> str:
        # Implements error analysis and code fixing (Version 1)
        
    def visual_self_reflection(self, code: str, media_path: Union[str, Image.Image], ...) -> str:
        # Implements visual self-reflection capabilities
```

### 4.3 Self-Debugging Example

The image shows a specific example of the Code Agent's self-debugging process:

**Original Error (Version 0)**:
```python
arrow = Arrow(start=mantissa[0][0].get_edge(UP) + UP * 0.1,
              end=mantissa[0][0].get_edge(DOWN), color=YELLOW, buff=0.1)
```

**Error Analysis**:
- Error Type: TypeError
- Root Cause: 'get_edge()' requires only one argument which is the direction
- Solution: Use 'get_left()' and 'get_right()' instead

**Corrected Code (Version 1)**:
```python
arrow = Arrow(start=mantissa[0][0].get_left() + UP * 0.1,
              end=mantissa[0][0].get_right(), color=YELLOW, buff=0.1)
```

This exact self-debugging process is implemented in the `fix_code_errors` method of the `CodeGenerator` class, demonstrating the pipeline's ability to self-correct and improve code quality.

### 4.4 Rendered Video Output

The image shows a rendered video with:
- Two horizontal bar graphs showing IEEE-754 exponent ranges
- Mathematical formula: `ActualExponent = BiasedExponent - Bias`
- Specific value: `SinglePrecisionBias = 127`
- Audio and video playback controls

This output is generated through the complete pipeline:
1. **Planner Agent** creates the scene structure
2. **Agentic RAG** provides relevant documentation
3. **Code Agent** generates and refines the Manim code
4. **Video Renderer** produces the final video with TTS narration

## 5. Conclusion

The TheoremExplainAgent pipeline implementation perfectly matches the design shown in the image. Each AI agent has well-defined system instructions that enable:

1. **Planner Agent**: Comprehensive video planning with structured scene breakdowns
2. **Agentic RAG**: Intelligent information retrieval and contextualization
3. **Code Agent**: Self-debugging code generation with error correction capabilities

The pipeline demonstrates advanced AI capabilities including:
- Multi-agent coordination
- Self-debugging and error correction
- Retrieval-augmented generation
- Visual self-reflection
- Modular, reusable code generation

This implementation provides a robust foundation for generating high-quality educational videos that explain complex mathematical theorems through visual animations and synchronized narration.