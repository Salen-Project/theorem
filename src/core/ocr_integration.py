import os
import tempfile
from typing import Dict, Any, Optional, List
from PIL import Image

from src.core.ocr_latex_extractor import OCRLatexExtractor, create_ocr_latex_extractor
from mllm_tools.utils import _prepare_text_inputs


class OCRPipelineIntegration:
    """
    Integration module that connects OCR LaTeX extraction with the video generation pipeline.
    
    This module:
    1. Provides OCR functionality for extracting LaTeX from images
    2. Integrates with the existing video generation workflow
    3. Passes extracted LaTeX to lesson script generation
    4. Handles OCR results and metadata
    """
    
    def __init__(self, vision_model, output_dir: str = None):
        """
        Initialize the OCR pipeline integration.
        
        Args:
            vision_model: Vision model for OCR tasks
            output_dir: Directory for saving OCR results and intermediate files
        """
        self.vision_model = vision_model
        self.output_dir = output_dir or tempfile.gettempdir()
        
        # Create OCR extractor
        self.ocr_extractor = create_ocr_latex_extractor(
            vision_model=vision_model,
            max_iterations=5,
            similarity_threshold=0.8
        )
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_image_to_lesson_script(self, 
                                     image_path: str, 
                                     topic: str = None,
                                     trace_id: str = None, 
                                     session_id: str = None) -> Dict[str, Any]:
        """
        Complete pipeline: Extract LaTeX from image and generate lesson script.
        
        Args:
            image_path: Path to the input image
            topic: Optional topic for context
            trace_id: Optional trace ID for logging
            session_id: Optional session ID for logging
            
        Returns:
            Dictionary containing:
            - latex_code: Extracted LaTeX code
            - lesson_script: Generated lesson script
            - ocr_results: Full OCR extraction results
            - success: Whether the process was successful
        """
        
        print(f"Starting OCR pipeline for image: {image_path}")
        
        # Step 1: Extract LaTeX from image with verification loop
        ocr_results = self.ocr_extractor.extract_latex_from_image(
            image_path=image_path,
            trace_id=trace_id,
            session_id=session_id
        )
        
        if not ocr_results['success'] or not ocr_results['latex_code']:
            print(f"OCR extraction failed or produced no LaTeX code")
            return {
                'latex_code': None,
                'lesson_script': None,
                'ocr_results': ocr_results,
                'success': False,
                'error': 'OCR extraction failed'
            }
        
        latex_code = ocr_results['latex_code']
        print(f"OCR extraction successful after {ocr_results['iterations']} iterations")
        print(f"Final similarity score: {ocr_results['similarity_score']:.3f}")
        
        # Step 2: Generate lesson script from LaTeX
        lesson_script = self.generate_lesson_script_from_latex(
            latex_code=latex_code,
            topic=topic,
            trace_id=trace_id,
            session_id=session_id
        )
        
        # Step 3: Save results
        self._save_ocr_results(image_path, latex_code, lesson_script, ocr_results)
        
        return {
            'latex_code': latex_code,
            'lesson_script': lesson_script,
            'ocr_results': ocr_results,
            'success': True
        }
    
    def generate_lesson_script_from_latex(self, 
                                        latex_code: str, 
                                        topic: str = None,
                                        trace_id: str = None, 
                                        session_id: str = None) -> str:
        """
        Generate lesson script from extracted LaTeX code.
        
        Args:
            latex_code: The extracted LaTeX code
            topic: Optional topic for context
            trace_id: Optional trace ID for logging
            session_id: Optional session ID for logging
            
        Returns:
            Generated lesson script text
        """
        
        # Create prompt for lesson script generation
        prompt = self._create_lesson_script_prompt(latex_code, topic)
        
        try:
            inputs = _prepare_text_inputs(prompt)
            
            metadata = {
                "generation_name": "lesson_script_from_latex",
                "trace_id": trace_id,
                "tags": ["lesson", "script", "latex"],
                "session_id": session_id
            }
            
            response = self.vision_model(inputs, metadata=metadata)
            
            # Extract lesson script from response
            lesson_script = self._extract_lesson_script_from_response(response)
            return lesson_script
            
        except Exception as e:
            print(f"Error generating lesson script: {e}")
            return f"Error generating lesson script from LaTeX: {e}"
    
    def _create_lesson_script_prompt(self, latex_code: str, topic: str = None) -> str:
        """Create prompt for lesson script generation from LaTeX."""
        
        topic_context = f" on the topic of '{topic}'" if topic else ""
        
        prompt = f"""You are an expert educational content creator. Your task is to generate a comprehensive lesson script based on the provided LaTeX content{topic_context}.

REQUIREMENTS:
1. Create an engaging, educational lesson script that explains all content from the LaTeX
2. Structure the lesson with clear introduction, main content, and conclusion
3. Explain mathematical formulas, diagrams, tables, and any visual elements in detail
4. Use pedagogical best practices: build from simple to complex concepts
5. Include clear explanations of symbols, notation, and terminology
6. Make the content accessible while maintaining accuracy
7. Add context and real-world applications where relevant
8. Include smooth transitions between different topics or sections

LATEX CONTENT TO EXPLAIN:
{latex_code}

LESSON SCRIPT FORMAT:
Generate a detailed lesson script that a teacher could use to explain this content. Include:
- Clear verbal explanations of all mathematical concepts
- Step-by-step walkthroughs of formulas or proofs
- Descriptions of any diagrams, graphs, or visual elements
- Context about why this content is important
- Examples or applications where helpful

Generate the lesson script now:"""

        return prompt
    
    def _extract_lesson_script_from_response(self, response: str) -> str:
        """Extract lesson script from model response."""
        # Clean up the response and return as lesson script
        # Remove any markdown formatting or extra content
        
        # Try to find content between script markers if present
        script_markers = ["LESSON SCRIPT:", "SCRIPT:", "LESSON:"]
        for marker in script_markers:
            if marker in response:
                parts = response.split(marker, 1)
                if len(parts) > 1:
                    return parts[1].strip()
        
        # If no markers found, return the entire response cleaned up
        return response.strip()
    
    def _save_ocr_results(self, 
                         image_path: str, 
                         latex_code: str, 
                         lesson_script: str, 
                         ocr_results: Dict[str, Any]) -> None:
        """Save OCR results and generated content to files."""
        
        try:
            # Create base filename from image path
            image_name = os.path.splitext(os.path.basename(image_path))[0]
            base_path = os.path.join(self.output_dir, f"ocr_{image_name}")
            
            # Save LaTeX code
            latex_file = f"{base_path}_latex.tex"
            with open(latex_file, 'w', encoding='utf-8') as f:
                f.write(latex_code)
            
            # Save lesson script
            script_file = f"{base_path}_lesson_script.txt"
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(lesson_script)
            
            # Save OCR metadata
            import json
            metadata_file = f"{base_path}_ocr_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                # Convert results to JSON-serializable format
                serializable_results = {
                    'latex_code': latex_code,
                    'similarity_score': ocr_results['similarity_score'],
                    'iterations': ocr_results['iterations'],
                    'success': ocr_results['success'],
                    'threshold_met': ocr_results['threshold_met'],
                    'original_image': image_path,
                    'output_files': {
                        'latex': latex_file,
                        'lesson_script': script_file
                    }
                }
                json.dump(serializable_results, f, indent=2)
            
            print(f"OCR results saved:")
            print(f"  LaTeX: {latex_file}")
            print(f"  Lesson Script: {script_file}")
            print(f"  Metadata: {metadata_file}")
            
        except Exception as e:
            print(f"Error saving OCR results: {e}")
    
    def batch_process_images(self, 
                           image_paths: List[str], 
                           topic: str = None,
                           trace_id: str = None, 
                           session_id: str = None) -> List[Dict[str, Any]]:
        """
        Process multiple images in batch.
        
        Args:
            image_paths: List of image paths to process
            topic: Optional topic for context
            trace_id: Optional trace ID for logging
            session_id: Optional session ID for logging
            
        Returns:
            List of results for each image
        """
        
        results = []
        
        for i, image_path in enumerate(image_paths):
            print(f"\nProcessing image {i+1}/{len(image_paths)}: {image_path}")
            
            try:
                result = self.process_image_to_lesson_script(
                    image_path=image_path,
                    topic=topic,
                    trace_id=trace_id,
                    session_id=session_id
                )
                results.append(result)
                
            except Exception as e:
                print(f"Error processing image {image_path}: {e}")
                results.append({
                    'latex_code': None,
                    'lesson_script': None,
                    'ocr_results': None,
                    'success': False,
                    'error': str(e),
                    'image_path': image_path
                })
        
        return results
    
    def get_ocr_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics from OCR processing results."""
        
        if not results:
            return {'total': 0, 'successful': 0, 'failed': 0, 'success_rate': 0.0}
        
        total = len(results)
        successful = sum(1 for r in results if r.get('success', False))
        failed = total - successful
        
        # Calculate average iterations and similarity scores for successful extractions
        successful_results = [r for r in results if r.get('success', False)]
        
        avg_iterations = 0
        avg_similarity = 0
        
        if successful_results:
            avg_iterations = sum(r['ocr_results']['iterations'] for r in successful_results) / len(successful_results)
            avg_similarity = sum(r['ocr_results']['similarity_score'] for r in successful_results) / len(successful_results)
        
        return {
            'total': total,
            'successful': successful,
            'failed': failed,
            'success_rate': successful / total if total > 0 else 0.0,
            'average_iterations': avg_iterations,
            'average_similarity_score': avg_similarity
        }


def create_ocr_pipeline(vision_model, output_dir: str = None) -> OCRPipelineIntegration:
    """Factory function to create OCR pipeline integration."""
    return OCRPipelineIntegration(vision_model, output_dir)