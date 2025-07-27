#!/usr/bin/env python3
"""
Example script demonstrating the OCR LaTeX Extraction API usage.

This script shows how to:
1. Start the API server
2. Send requests to extract LaTeX from images
3. Process batch requests
4. Handle responses and errors
"""

import requests
import json
import time
import os
from typing import List, Dict, Any


class OCRClient:
    """Client for the OCR LaTeX Extraction API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def check_status(self) -> Dict[str, Any]:
        """Check if the API service is running."""
        try:
            response = self.session.get(f"{self.base_url}/ocr/status")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e), "status": "offline"}
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get list of available models."""
        try:
            response = self.session.get(f"{self.base_url}/ocr/models")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def extract_latex(self, 
                     image_path: str, 
                     topic: str = None,
                     max_iterations: int = 5,
                     similarity_threshold: float = 0.8,
                     model_name: str = None) -> Dict[str, Any]:
        """Extract LaTeX from a single image."""
        
        if not os.path.exists(image_path):
            return {"error": f"Image file not found: {image_path}"}
        
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, 'image/png')}
                data = {
                    'max_iterations': max_iterations,
                    'similarity_threshold': similarity_threshold
                }
                
                if topic:
                    data['topic'] = topic
                if model_name:
                    data['model_name'] = model_name
                
                response = self.session.post(
                    f"{self.base_url}/ocr/extract",
                    files=files,
                    data=data
                )
                response.raise_for_status()
                return response.json()
                
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    def batch_extract_latex(self, 
                           image_paths: List[str],
                           topic: str = None,
                           max_iterations: int = 5,
                           similarity_threshold: float = 0.8,
                           model_name: str = None) -> Dict[str, Any]:
        """Extract LaTeX from multiple images."""
        
        # Check if all files exist
        missing_files = [path for path in image_paths if not os.path.exists(path)]
        if missing_files:
            return {"error": f"Image files not found: {missing_files}"}
        
        try:
            files = []
            for image_path in image_paths:
                files.append(('files', (os.path.basename(image_path), 
                                       open(image_path, 'rb'), 'image/png')))
            
            data = {
                'max_iterations': max_iterations,
                'similarity_threshold': similarity_threshold
            }
            
            if topic:
                data['topic'] = topic
            if model_name:
                data['model_name'] = model_name
            
            response = self.session.post(
                f"{self.base_url}/ocr/batch",
                files=files,
                data=data
            )
            response.raise_for_status()
            result = response.json()
            
            # Close file handles
            for _, file_tuple in files:
                file_tuple[1].close()
            
            return result
            
        except requests.exceptions.RequestException as e:
            # Close any open file handles in case of error
            for _, file_tuple in files:
                try:
                    file_tuple[1].close()
                except:
                    pass
            return {"error": str(e)}


def print_status(status: Dict[str, Any]):
    """Print service status in a formatted way."""
    print("\n" + "="*50)
    print("OCR API SERVICE STATUS")
    print("="*50)
    
    if "error" in status:
        print(f"❌ Service Status: {status.get('status', 'Error')}")
        print(f"Error: {status['error']}")
    else:
        print(f"✅ Service: {status.get('service', 'Unknown')}")
        print(f"Status: {status.get('status', 'Unknown')}")
        print(f"Version: {status.get('version', 'Unknown')}")
        print(f"Default Model: {status.get('default_model', 'Unknown')}")
        print(f"System Instructions Loaded: {status.get('system_instructions_loaded', False)}")
        print(f"Timestamp: {status.get('timestamp', 'Unknown')}")


def print_extraction_result(result: Dict[str, Any], image_name: str = "image"):
    """Print extraction results in a formatted way."""
    print(f"\n{'='*50}")
    print(f"EXTRACTION RESULT: {image_name}")
    print(f"{'='*50}")
    
    if result.get('success'):
        print("✅ Status: SUCCESS")
        print(f"Similarity Score: {result.get('similarity_score', 'N/A'):.3f}")
        print(f"Iterations: {result.get('iterations', 'N/A')}")
        print(f"Processing Time: {result.get('processing_time', 'N/A'):.2f}s")
        print(f"Trace ID: {result.get('trace_id', 'N/A')}")
        
        latex_code = result.get('latex_code', '')
        if latex_code:
            print(f"\nLaTeX Code ({len(latex_code)} chars):")
            print("-" * 30)
            print(latex_code[:500] + ("..." if len(latex_code) > 500 else ""))
        
        lesson_script = result.get('lesson_script', '')
        if lesson_script:
            print(f"\nLesson Script ({len(lesson_script)} chars):")
            print("-" * 30)
            print(lesson_script[:300] + ("..." if len(lesson_script) > 300 else ""))
    else:
        print("❌ Status: FAILED")
        print(f"Error: {result.get('error', 'Unknown error')}")
        print(f"Processing Time: {result.get('processing_time', 'N/A'):.2f}s")


def print_batch_result(result: Dict[str, Any]):
    """Print batch extraction results in a formatted way."""
    print(f"\n{'='*50}")
    print("BATCH EXTRACTION RESULTS")
    print(f"{'='*50}")
    
    if result.get('success'):
        print("✅ Batch Status: SUCCESS")
        print(f"Total Images: {result.get('total_images', 0)}")
        print(f"Successful: {result.get('successful', 0)}")
        print(f"Failed: {result.get('failed', 0)}")
        print(f"Success Rate: {result.get('success_rate', 0.0):.1%}")
        print(f"Average Iterations: {result.get('average_iterations', 0.0):.1f}")
        print(f"Average Similarity: {result.get('average_similarity', 0.0):.3f}")
        print(f"Total Processing Time: {result.get('processing_time', 0.0):.2f}s")
        print(f"Batch ID: {result.get('batch_id', 'N/A')}")
        
        # Show individual results summary
        results = result.get('results', [])
        if results:
            print(f"\nIndividual Results:")
            print("-" * 30)
            for i, res in enumerate(results, 1):
                status = "✅" if res.get('success') else "❌"
                similarity = res.get('similarity_score', 0.0)
                iterations = res.get('iterations', 0)
                print(f"{i:2d}. {status} Similarity: {similarity:.3f} Iterations: {iterations}")
    else:
        print("❌ Batch Status: FAILED")
        print(f"Error: {result.get('error', 'Unknown error')}")


def example_single_image():
    """Example: Extract LaTeX from a single image."""
    print("\n🔍 EXAMPLE: Single Image Extraction")
    print("-" * 40)
    
    client = OCRClient()
    
    # You would replace this with an actual image path
    image_path = "example_math_formula.png"
    
    if not os.path.exists(image_path):
        print(f"⚠️  Example image not found: {image_path}")
        print("Please provide a real image path to test the extraction.")
        return
    
    result = client.extract_latex(
        image_path=image_path,
        topic="mathematics",
        max_iterations=3,
        similarity_threshold=0.8
    )
    
    print_extraction_result(result, os.path.basename(image_path))


def example_batch_processing():
    """Example: Process multiple images in batch."""
    print("\n📚 EXAMPLE: Batch Processing")
    print("-" * 40)
    
    client = OCRClient()
    
    # You would replace these with actual image paths
    image_paths = [
        "example_formula1.png",
        "example_diagram.png",
        "example_table.png"
    ]
    
    existing_paths = [path for path in image_paths if os.path.exists(path)]
    
    if not existing_paths:
        print("⚠️  No example images found. Please provide real image paths to test batch processing.")
        print(f"Expected files: {image_paths}")
        return
    
    print(f"Processing {len(existing_paths)} images...")
    
    result = client.batch_extract_latex(
        image_paths=existing_paths,
        topic="mixed mathematics",
        max_iterations=3,
        similarity_threshold=0.75
    )
    
    print_batch_result(result)


def main():
    """Main function demonstrating API usage."""
    print("OCR LaTeX Extraction API - Example Usage")
    print("=" * 50)
    
    # Initialize client
    client = OCRClient()
    
    # Check service status
    print("🔧 Checking API service status...")
    status = client.check_status()
    print_status(status)
    
    if "error" in status:
        print("\n❌ API service is not running!")
        print("Please start the API server first:")
        print("   python api.py --host 0.0.0.0 --port 8000")
        return
    
    # Get available models
    print("\n🤖 Getting available models...")
    models = client.get_available_models()
    if "error" not in models:
        print("Available models:")
        for model in models.get('available_models', []):
            marker = " (default)" if model == models.get('default_model') else ""
            print(f"  - {model}{marker}")
    
    # Run examples
    example_single_image()
    example_batch_processing()
    
    print(f"\n{'='*50}")
    print("API USAGE EXAMPLES COMPLETED")
    print(f"{'='*50}")
    print("\nTo use the API in your own code:")
    print("1. Start the API server: python api.py")
    print("2. Use the OCRClient class or direct HTTP requests")
    print("3. Check the API documentation at: http://localhost:8000/docs")


if __name__ == "__main__":
    main()