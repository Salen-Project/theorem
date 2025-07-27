#!/usr/bin/env python3
"""
OCR LaTeX Extraction Command Line Interface

This script provides a command-line interface for extracting LaTeX from images
using the OCR system with verification feedback loop.

Usage:
    python ocr_latex_cli.py --image path/to/image.png --model gemini/gemini-1.5-pro-002
    python ocr_latex_cli.py --batch path/to/images/ --model vertex_ai/gemini-1.5-flash-002
"""

import os
import argparse
import glob
import json
from typing import List, Dict, Any
import uuid

from mllm_tools.litellm import LiteLLMWrapper
from src.core.ocr_integration import create_ocr_pipeline


def setup_model(model_name: str) -> LiteLLMWrapper:
    """Setup and return the vision model."""
    print(f"Initializing model: {model_name}")
    
    # Default to Gemini 2.5 Flash if not specified
    if not model_name:
        model_name = "gemini/gemini-2.5-flash"
        print(f"Using default model: {model_name}")
    
    model = LiteLLMWrapper(model_name=model_name)
    
    # Test the model
    try:
        test_response = model([{"type": "text", "content": "Hello, this is a test."}])
        print("Model initialized successfully")
        return model
    except Exception as e:
        print(f"Error initializing model: {e}")
        raise


def process_single_image(image_path: str, 
                        model: LiteLLMWrapper, 
                        output_dir: str,
                        topic: str = None) -> Dict[str, Any]:
    """Process a single image through the OCR pipeline."""
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    print(f"\n{'='*50}")
    print(f"Processing: {image_path}")
    print(f"{'='*50}")
    
    # Create OCR pipeline
    ocr_pipeline = create_ocr_pipeline(model, output_dir)
    
    # Generate unique IDs for tracing
    trace_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    # Process the image
    result = ocr_pipeline.process_image_to_lesson_script(
        image_path=image_path,
        topic=topic,
        trace_id=trace_id,
        session_id=session_id
    )
    
    # Print results summary
    if result['success']:
        print(f"\n✅ SUCCESS!")
        print(f"LaTeX extracted after {result['ocr_results']['iterations']} iterations")
        print(f"Similarity score: {result['ocr_results']['similarity_score']:.3f}")
        print(f"LaTeX length: {len(result['latex_code'])} characters")
        print(f"Lesson script length: {len(result['lesson_script'])} characters")
    else:
        print(f"\n❌ FAILED!")
        print(f"Error: {result.get('error', 'Unknown error')}")
    
    return result


def process_batch_images(image_dir: str, 
                        model: LiteLLMWrapper, 
                        output_dir: str,
                        topic: str = None,
                        extensions: List[str] = None) -> List[Dict[str, Any]]:
    """Process multiple images from a directory."""
    
    if extensions is None:
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif', '*.tiff']
    
    # Find all image files
    image_paths = []
    for ext in extensions:
        pattern = os.path.join(image_dir, '**', ext)
        image_paths.extend(glob.glob(pattern, recursive=True))
    
    if not image_paths:
        print(f"No images found in directory: {image_dir}")
        return []
    
    print(f"Found {len(image_paths)} images to process")
    
    # Create OCR pipeline
    ocr_pipeline = create_ocr_pipeline(model, output_dir)
    
    # Generate unique IDs for tracing
    trace_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())
    
    # Process all images
    results = ocr_pipeline.batch_process_images(
        image_paths=image_paths,
        topic=topic,
        trace_id=trace_id,
        session_id=session_id
    )
    
    # Print batch statistics
    stats = ocr_pipeline.get_ocr_statistics(results)
    print(f"\n{'='*50}")
    print(f"BATCH PROCESSING RESULTS")
    print(f"{'='*50}")
    print(f"Total images: {stats['total']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success rate: {stats['success_rate']:.1%}")
    
    if stats['successful'] > 0:
        print(f"Average iterations: {stats['average_iterations']:.1f}")
        print(f"Average similarity: {stats['average_similarity_score']:.3f}")
    
    return results


def save_batch_summary(results: List[Dict[str, Any]], output_file: str) -> None:
    """Save batch processing summary to JSON file."""
    
    summary = {
        'total_processed': len(results),
        'successful': sum(1 for r in results if r.get('success', False)),
        'failed': sum(1 for r in results if not r.get('success', False)),
        'results': []
    }
    
    for result in results:
        result_summary = {
            'image_path': result.get('image_path', 'unknown'),
            'success': result.get('success', False),
            'error': result.get('error'),
            'latex_length': len(result['latex_code']) if result.get('latex_code') else 0,
            'script_length': len(result['lesson_script']) if result.get('lesson_script') else 0
        }
        
        if result.get('ocr_results'):
            result_summary.update({
                'iterations': result['ocr_results'].get('iterations', 0),
                'similarity_score': result['ocr_results'].get('similarity_score', 0.0),
                'threshold_met': result['ocr_results'].get('threshold_met', False)
            })
        
        summary['results'].append(result_summary)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"Batch summary saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract LaTeX from images using OCR with verification feedback loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single image
  python ocr_latex_cli.py --image math_formula.png --model gemini/gemini-1.5-pro-002

  # Process batch of images
  python ocr_latex_cli.py --batch ./images/ --model vertex_ai/gemini-1.5-flash-002 --topic "calculus"

  # Custom output directory and settings
  python ocr_latex_cli.py --image diagram.png --model gemini/gemini-1.5-pro-002 \\
                          --output ./results/ --max-iterations 3 --threshold 0.85
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--image', type=str, help='Path to single image file')
    input_group.add_argument('--batch', type=str, help='Path to directory containing images')
    
    # Model configuration
    parser.add_argument('--model', type=str, default='gemini/gemini-2.5-flash',
                       help='Model name (default: gemini/gemini-2.5-flash)')
    
    # Optional parameters
    parser.add_argument('--output', type=str, default='./ocr_output',
                       help='Output directory for results (default: ./ocr_output)')
    parser.add_argument('--topic', type=str,
                       help='Topic context for lesson script generation')
    parser.add_argument('--max-iterations', type=int, default=5,
                       help='Maximum OCR refinement iterations (default: 5)')
    parser.add_argument('--threshold', type=float, default=0.8,
                       help='Similarity threshold for verification (default: 0.8)')
    parser.add_argument('--extensions', nargs='+', 
                       default=['png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff'],
                       help='Image file extensions to process (default: png jpg jpeg bmp gif tiff)')
    parser.add_argument('--save-summary', action='store_true',
                       help='Save batch processing summary to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    try:
        # Setup model
        model = setup_model(args.model)
        
        # Process images
        if args.image:
            # Single image processing
            result = process_single_image(
                image_path=args.image,
                model=model,
                output_dir=args.output,
                topic=args.topic
            )
            
            if args.save_summary:
                summary_file = os.path.join(args.output, 'single_image_result.json')
                save_batch_summary([result], summary_file)
        
        else:
            # Batch processing
            extensions = [f"*.{ext}" for ext in args.extensions]
            results = process_batch_images(
                image_dir=args.batch,
                model=model,
                output_dir=args.output,
                topic=args.topic,
                extensions=extensions
            )
            
            if args.save_summary or len(results) > 1:
                summary_file = os.path.join(args.output, 'batch_processing_summary.json')
                save_batch_summary(results, summary_file)
    
    except KeyboardInterrupt:
        print("\n\nProcessing interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    print(f"\nProcessing complete. Results saved to: {args.output}")
    return 0


if __name__ == "__main__":
    exit(main())