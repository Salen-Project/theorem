import os
import tempfile
import base64
from typing import Union, Dict, Any, Optional, Tuple
from PIL import Image, ImageChops
import numpy as np
from io import BytesIO

from mllm_tools.utils import _prepare_text_image_inputs
from src.utils.latex_compiler import compile_latex_to_image


class OCRLatexExtractor:
    """
    OCR system that extracts LaTeX from images with verification feedback loop.
    
    This system:
    1. Extracts LaTeX from input images using vision models
    2. Converts LaTeX back to images for verification
    3. Compares original and generated images
    4. Iteratively refines LaTeX until similarity is achieved (max 5 iterations)
    """
    
    def __init__(self, vision_model, latex_to_image_model=None, max_iterations: int = 5, similarity_threshold: float = 0.8):
        """
        Initialize the OCR LaTeX extractor.
        
        Args:
            vision_model: Model for vision tasks (OCR and image comparison)
            latex_to_image_model: Model for LaTeX to image conversion (optional, uses vision_model if None)
            max_iterations: Maximum number of refinement iterations
            similarity_threshold: Similarity threshold for image comparison (0-1)
        """
        self.vision_model = vision_model
        self.latex_to_image_model = latex_to_image_model or vision_model
        self.max_iterations = max_iterations
        self.similarity_threshold = similarity_threshold
        
        # System instructions for different tasks
        self.ocr_system_instruction = self._get_ocr_system_instruction()
        self.latex_to_image_instruction = self._get_latex_to_image_instruction()
        self.comparison_instruction = self._get_comparison_instruction()
        self.refinement_instruction = self._get_refinement_instruction()
    
    def _get_ocr_system_instruction(self) -> str:
        """Get system instruction for OCR LaTeX extraction."""
        return """You are an expert OCR system specialized in extracting LaTeX code from images. Your task is to convert everything visible in the image into precise LaTeX code.

CRITICAL REQUIREMENTS:
1. Extract EVERYTHING from the image - leave nothing out
2. All content must be described in LaTeX: text, formulas, tables, graphs, geometric shapes, diagrams, etc.
3. Use appropriate LaTeX packages and environments for different content types:
   - Mathematical formulas: Use amsmath, amssymb packages
   - Tables: Use tabular, array environments
   - Figures/Diagrams: Use tikz, pgfplots for graphs and geometric shapes
   - Text formatting: Use appropriate text commands and environments
4. Maintain the exact structure, layout, and positioning from the original image
5. For complex diagrams, use tikz to recreate the exact shapes, lines, and annotations
6. For graphs, use pgfplots with accurate data points, axes, labels, and styling
7. Include all text labels, captions, titles, and annotations exactly as shown
8. Preserve spacing, alignment, and visual hierarchy
9. Use proper LaTeX syntax and ensure compilability

OUTPUT FORMAT:
Return only the LaTeX code that would reproduce the image content. Include necessary package declarations at the top if needed.

Example packages you might need:
\\usepackage{amsmath,amssymb,amsfonts}
\\usepackage{tikz}
\\usepackage{pgfplots}
\\usepackage{array,tabularx}
\\usepackage{graphicx}

Extract the LaTeX now:"""

    def _get_latex_to_image_instruction(self) -> str:
        """Get instruction for converting LaTeX to image."""
        return """You are a LaTeX rendering system. Convert the provided LaTeX code into a high-quality image.

REQUIREMENTS:
1. Render the LaTeX code exactly as written
2. Use appropriate document class and packages
3. Ensure proper compilation and rendering
4. Output should be a clear, high-resolution image
5. Maintain proper spacing and formatting
6. Handle any LaTeX packages and environments correctly

If there are compilation errors, fix them minimally while preserving the intended content and structure.

Convert this LaTeX code to an image:"""

    def _get_comparison_instruction(self) -> str:
        """Get instruction for comparing images."""
        return """You are an expert image comparison system. Compare two images and determine if they contain the same content and structure.

COMPARISON CRITERIA:
1. Content accuracy: Do both images contain the same mathematical formulas, text, tables, diagrams?
2. Structural similarity: Is the layout, positioning, and organization similar?
3. Visual elements: Are shapes, graphs, charts, and geometric elements equivalent?
4. Text matching: Is all text content identical or equivalent?
5. Overall fidelity: Does the generated image faithfully represent the original?

IMPORTANT:
- Images don't need to be pixel-perfect identical
- Focus on content and structural equivalence
- Minor styling differences are acceptable if content matches
- "Good enough" similarity is acceptable for practical use

Rate the similarity on a scale of 0.0 to 1.0 where:
- 1.0 = Perfect or near-perfect match
- 0.8+ = Very good match, acceptable for use
- 0.6-0.8 = Good match with minor differences
- 0.4-0.6 = Moderate match, some content missing/different
- 0.0-0.4 = Poor match, significant differences

OUTPUT FORMAT:
{
    "similarity_score": <float between 0.0 and 1.0>,
    "content_match": <boolean>,
    "structure_match": <boolean>,
    "differences": ["list of specific differences found"],
    "overall_assessment": "<brief description of comparison result>"
}

Compare these images:"""

    def _get_refinement_instruction(self) -> str:
        """Get instruction for refining LaTeX based on comparison feedback."""
        return """You are an expert LaTeX editor. Based on the comparison feedback between the original image and the LaTeX-generated image, refine the LaTeX code to better match the original.

REFINEMENT GUIDELINES:
1. Address specific differences mentioned in the feedback
2. Improve content accuracy and structural similarity
3. Fix any missing elements, incorrect formulas, or layout issues
4. Maintain valid LaTeX syntax
5. Focus on the most critical differences first
6. Preserve what was already correct

INPUT:
- Original LaTeX code
- Comparison feedback with differences
- Similarity score and assessment

OUTPUT:
Provide the refined LaTeX code that addresses the identified issues.

Refine this LaTeX code:"""

    def extract_latex_from_image(self, image_path: str, trace_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """
        Extract LaTeX from an image with verification feedback loop.
        
        Args:
            image_path: Path to the input image
            trace_id: Optional trace ID for logging
            session_id: Optional session ID for logging
            
        Returns:
            Dictionary containing:
            - latex_code: Final LaTeX code
            - similarity_score: Final similarity score
            - iterations: Number of iterations performed
            - success: Whether extraction was successful
            - history: List of iteration details
        """
        
        # Load the original image
        original_image = Image.open(image_path)
        
        # Initialize tracking variables
        current_latex = None
        similarity_score = 0.0
        iteration_history = []
        
        for iteration in range(self.max_iterations):
            print(f"OCR Iteration {iteration + 1}/{self.max_iterations}")
            
            # Step 1: Extract LaTeX from original image (first iteration) or refine existing LaTeX
            if iteration == 0:
                # Initial extraction
                latex_code = self._extract_latex_initial(image_path, trace_id, session_id)
            else:
                # Refinement based on previous comparison
                latex_code = self._refine_latex(
                    current_latex, 
                    iteration_history[-1]['comparison_result'],
                    trace_id, 
                    session_id
                )
            
            if not latex_code:
                iteration_history.append({
                    'iteration': iteration + 1,
                    'latex_code': None,
                    'error': 'Failed to extract/refine LaTeX'
                })
                continue
            
            current_latex = latex_code
            
            # Step 2: Convert LaTeX back to image
            generated_image_path = self._latex_to_image(latex_code, trace_id, session_id)
            
            if not generated_image_path:
                iteration_history.append({
                    'iteration': iteration + 1,
                    'latex_code': latex_code,
                    'error': 'Failed to convert LaTeX to image'
                })
                continue
            
            # Step 3: Compare original and generated images
            comparison_result = self._compare_images(
                image_path, 
                generated_image_path, 
                latex_code,
                trace_id, 
                session_id
            )
            
            similarity_score = comparison_result.get('similarity_score', 0.0)
            
            # Store iteration results
            iteration_history.append({
                'iteration': iteration + 1,
                'latex_code': latex_code,
                'generated_image_path': generated_image_path,
                'comparison_result': comparison_result,
                'similarity_score': similarity_score
            })
            
            print(f"Iteration {iteration + 1}: Similarity score = {similarity_score:.3f}")
            
            # Check if similarity threshold is met
            if similarity_score >= self.similarity_threshold:
                print(f"Similarity threshold reached! Final score: {similarity_score:.3f}")
                break
            
            # Clean up temporary generated image
            try:
                os.remove(generated_image_path)
            except:
                pass
        
        success = similarity_score >= self.similarity_threshold
        
        return {
            'latex_code': current_latex,
            'similarity_score': similarity_score,
            'iterations': len(iteration_history),
            'success': success,
            'history': iteration_history,
            'threshold_met': success
        }
    
    def _extract_latex_initial(self, image_path: str, trace_id: str = None, session_id: str = None) -> Optional[str]:
        """Extract LaTeX from image using OCR."""
        try:
            inputs = _prepare_text_image_inputs(self.ocr_system_instruction, image_path)
            
            metadata = {
                "generation_name": "ocr_latex_extraction",
                "trace_id": trace_id,
                "tags": ["ocr", "latex"],
                "session_id": session_id
            }
            
            response = self.vision_model(inputs, metadata=metadata)
            
            # Extract LaTeX code from response
            latex_code = self._extract_latex_from_response(response)
            return latex_code
            
        except Exception as e:
            print(f"Error in initial LaTeX extraction: {e}")
            return None
    
    def _latex_to_image(self, latex_code: str, trace_id: str = None, session_id: str = None) -> Optional[str]:
        """Convert LaTeX code to image."""
        try:
            # Use the proper LaTeX compiler
            output_path = compile_latex_to_image(latex_code)
            return output_path
            
        except Exception as e:
            print(f"Error in LaTeX to image conversion: {e}")
            return None
    

    
    def _compare_images(self, original_path: str, generated_path: str, latex_code: str, 
                       trace_id: str = None, session_id: str = None) -> Dict[str, Any]:
        """Compare original and generated images."""
        try:
            prompt = self.comparison_instruction
            inputs = _prepare_text_image_inputs(prompt, [original_path, generated_path])
            
            metadata = {
                "generation_name": "image_comparison",
                "trace_id": trace_id,
                "tags": ["comparison", "verification"],
                "session_id": session_id
            }
            
            response = self.vision_model(inputs, metadata=metadata)
            
            # Parse comparison result
            comparison_result = self._parse_comparison_response(response)
            comparison_result['latex_code'] = latex_code
            
            return comparison_result
            
        except Exception as e:
            print(f"Error in image comparison: {e}")
            return {
                'similarity_score': 0.0,
                'content_match': False,
                'structure_match': False,
                'differences': [f"Comparison error: {e}"],
                'overall_assessment': 'Error during comparison'
            }
    
    def _refine_latex(self, current_latex: str, comparison_result: Dict[str, Any], 
                     trace_id: str = None, session_id: str = None) -> Optional[str]:
        """Refine LaTeX based on comparison feedback."""
        try:
            feedback = f"""
Similarity Score: {comparison_result.get('similarity_score', 0.0)}
Content Match: {comparison_result.get('content_match', False)}
Structure Match: {comparison_result.get('structure_match', False)}
Differences: {comparison_result.get('differences', [])}
Assessment: {comparison_result.get('overall_assessment', 'No assessment')}

Current LaTeX Code:
{current_latex}
"""
            
            prompt = f"{self.refinement_instruction}\n\n{feedback}"
            inputs = _prepare_text_image_inputs(prompt, [])
            
            metadata = {
                "generation_name": "latex_refinement",
                "trace_id": trace_id,
                "tags": ["refinement", "latex"],
                "session_id": session_id
            }
            
            response = self.vision_model(inputs, metadata=metadata)
            
            # Extract refined LaTeX code
            refined_latex = self._extract_latex_from_response(response)
            return refined_latex
            
        except Exception as e:
            print(f"Error in LaTeX refinement: {e}")
            return current_latex  # Return original if refinement fails
    
    def _extract_latex_from_response(self, response: str) -> str:
        """Extract LaTeX code from model response."""
        # Try to find LaTeX code blocks
        if "```latex" in response:
            start = response.find("```latex") + 8
            end = response.find("```", start)
            if end != -1:
                return response[start:end].strip()
        
        # Try to find code blocks without language specification
        if "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end != -1:
                return response[start:end].strip()
        
        # If no code blocks found, return the entire response (cleaned)
        return response.strip()
    
    def _parse_comparison_response(self, response: str) -> Dict[str, Any]:
        """Parse comparison response from model."""
        try:
            # Try to extract JSON from response
            import json
            
            # Find JSON block
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                result = json.loads(json_str)
                return result
            
        except:
            pass
        
        # Fallback: parse manually or return default
        return {
            'similarity_score': 0.5,  # Default moderate similarity
            'content_match': False,
            'structure_match': False,
            'differences': ['Could not parse comparison result'],
            'overall_assessment': 'Comparison parsing failed'
        }


def create_ocr_latex_extractor(vision_model, **kwargs) -> OCRLatexExtractor:
    """Factory function to create OCR LaTeX extractor."""
    return OCRLatexExtractor(vision_model, **kwargs)