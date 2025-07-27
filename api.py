#!/usr/bin/env python3
"""
OCR LaTeX Extraction API Service

This FastAPI service provides REST endpoints for the OCR LaTeX extraction system.
It uses Gemini 2.5 Flash as the OCR model and incorporates the OCR_README.md
content as system instructions for enhanced performance.

Endpoints:
- POST /ocr/extract - Extract LaTeX from a single image
- POST /ocr/batch - Process multiple images
- GET /ocr/status - Check service status
- GET /ocr/models - List available models
"""

import os
import tempfile
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import traceback

from fastapi import FastAPI, File, UploadFile, HTTPException, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from mllm_tools.litellm import LiteLLMWrapper
from src.core.ocr_integration import create_ocr_pipeline
from src.core.ocr_latex_extractor import create_ocr_latex_extractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OCR LaTeX Extraction API",
    description="Advanced OCR service for extracting LaTeX from images with verification feedback loop",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
DEFAULT_MODEL = "gemini/gemini-2.5-flash"
ocr_service = None
system_instructions = None

# Pydantic models for request/response
class OCRRequest(BaseModel):
    topic: Optional[str] = Field(None, description="Optional topic context for lesson script generation")
    max_iterations: int = Field(5, description="Maximum refinement iterations", ge=1, le=10)
    similarity_threshold: float = Field(0.8, description="Similarity threshold for verification", ge=0.1, le=1.0)
    model_name: Optional[str] = Field(None, description="Vision model to use (defaults to Gemini 2.5 Flash)")

class OCRResponse(BaseModel):
    success: bool
    latex_code: Optional[str] = None
    lesson_script: Optional[str] = None
    similarity_score: Optional[float] = None
    iterations: Optional[int] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None
    trace_id: str

class BatchOCRRequest(BaseModel):
    topic: Optional[str] = Field(None, description="Optional topic context")
    max_iterations: int = Field(5, description="Maximum refinement iterations", ge=1, le=10)
    similarity_threshold: float = Field(0.8, description="Similarity threshold", ge=0.1, le=1.0)
    model_name: Optional[str] = Field(None, description="Vision model to use")

class BatchOCRResponse(BaseModel):
    success: bool
    total_images: int
    successful: int
    failed: int
    success_rate: float
    average_iterations: Optional[float] = None
    average_similarity: Optional[float] = None
    processing_time: float
    results: List[OCRResponse]
    batch_id: str

class StatusResponse(BaseModel):
    service: str = "OCR LaTeX Extraction API"
    status: str = "running"
    version: str = "1.0.0"
    default_model: str
    system_instructions_loaded: bool
    timestamp: str

def load_system_instructions() -> str:
    """Load system instructions from OCR_README.md file."""
    try:
        readme_path = os.path.join(os.path.dirname(__file__), "OCR_README.md")
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info("System instructions loaded from OCR_README.md")
            return content
        else:
            logger.warning("OCR_README.md not found, using default instructions")
            return get_default_system_instructions()
    except Exception as e:
        logger.error(f"Error loading system instructions: {e}")
        return get_default_system_instructions()

def get_default_system_instructions() -> str:
    """Get default system instructions if README file is not available."""
    return """You are an expert OCR system specialized in extracting LaTeX code from images. 

CRITICAL REQUIREMENTS:
1. Extract EVERYTHING from the image - leave nothing out
2. All content must be described in LaTeX: text, formulas, tables, graphs, geometric shapes, diagrams, etc.
3. Use appropriate LaTeX packages and environments for different content types
4. Maintain the exact structure, layout, and positioning from the original image
5. For complex diagrams, use tikz to recreate the exact shapes, lines, and annotations
6. For graphs, use pgfplots with accurate data points, axes, labels, and styling
7. Include all text labels, captions, titles, and annotations exactly as shown
8. Preserve spacing, alignment, and visual hierarchy
9. Use proper LaTeX syntax and ensure compilability

Extract the LaTeX now:"""

def get_enhanced_system_instructions(base_instructions: str) -> str:
    """Enhance system instructions with OCR_README.md content."""
    enhanced_instructions = f"""
{base_instructions}

ADDITIONAL CONTEXT AND CAPABILITIES:
This OCR system is part of an advanced LaTeX extraction pipeline with the following capabilities:

SYSTEM ARCHITECTURE:
- Iterative refinement with up to 5 improvement cycles
- Image comparison for verification using LaTeX compilation
- Similarity scoring for accuracy assessment
- Automatic lesson script generation from extracted LaTeX

SUPPORTED CONTENT TYPES:
- Mathematical formulas and equations (amsmath, amssymb)
- Tables and data structures (tabular, array, booktabs)
- Graphs and charts (pgfplots with accurate data points)
- Complex geometric shapes (tikz with precise coordinates)
- Technical diagrams and illustrations
- Text content with proper formatting

LATEX PACKAGES AUTOMATICALLY AVAILABLE:
- amsmath, amssymb, amsfonts - Advanced mathematics
- tikz, pgfplots - Graphics and plotting
- array, tabularx, booktabs - Professional tables
- graphicx, xcolor - Images and colors
- geometry - Layout control

QUALITY STANDARDS:
- Aim for similarity scores above 0.8
- Ensure compilable LaTeX code
- Maintain visual hierarchy and structure
- Include all textual and graphical elements
- Use appropriate mathematical notation

Your extraction will be verified by compiling the LaTeX back to an image and comparing it with the original. Focus on accuracy and completeness.
"""
    return enhanced_instructions

class OCRService:
    """OCR service wrapper with enhanced system instructions."""
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.model = None
        self.system_instructions = system_instructions
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the vision model."""
        try:
            self.model = LiteLLMWrapper(model_name=self.model_name)
            logger.info(f"OCR model initialized: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize model {self.model_name}: {e}")
            raise
    
    def create_ocr_extractor(self, max_iterations: int = 5, similarity_threshold: float = 0.8):
        """Create OCR extractor with enhanced system instructions."""
        extractor = create_ocr_latex_extractor(
            vision_model=self.model,
            max_iterations=max_iterations,
            similarity_threshold=similarity_threshold
        )
        
        # Override system instructions with enhanced version
        if self.system_instructions:
            enhanced_instructions = get_enhanced_system_instructions(self.system_instructions)
            extractor.ocr_system_instruction = enhanced_instructions
        
        return extractor
    
    def create_pipeline(self, output_dir: str = None):
        """Create OCR pipeline with enhanced system instructions."""
        pipeline = create_ocr_pipeline(self.model, output_dir)
        
        # Override system instructions in the extractor
        if self.system_instructions:
            enhanced_instructions = get_enhanced_system_instructions(self.system_instructions)
            pipeline.ocr_extractor.ocr_system_instruction = enhanced_instructions
        
        return pipeline

@app.on_event("startup")
async def startup_event():
    """Initialize the OCR service on startup."""
    global ocr_service, system_instructions
    
    logger.info("Starting OCR LaTeX Extraction API...")
    
    # Load system instructions
    system_instructions = load_system_instructions()
    
    # Initialize OCR service
    try:
        ocr_service = OCRService(DEFAULT_MODEL)
        logger.info("OCR service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OCR service: {e}")
        raise

@app.get("/", response_model=StatusResponse)
async def root():
    """Root endpoint - returns service status."""
    return StatusResponse(
        default_model=DEFAULT_MODEL,
        system_instructions_loaded=system_instructions is not None,
        timestamp=datetime.now().isoformat()
    )

@app.get("/ocr/status", response_model=StatusResponse)
async def get_status():
    """Get service status."""
    return StatusResponse(
        default_model=DEFAULT_MODEL,
        system_instructions_loaded=system_instructions is not None,
        timestamp=datetime.now().isoformat()
    )

@app.get("/ocr/models")
async def get_available_models():
    """Get list of available models."""
    return {
        "available_models": [
            "gemini/gemini-2.5-flash",
            "gemini/gemini-1.5-pro-002",
            "gemini/gemini-1.5-flash-002",
            "vertex_ai/gemini-2.5-flash",
            "vertex_ai/gemini-1.5-pro-002",
            "vertex_ai/gemini-1.5-flash-002"
        ],
        "default_model": DEFAULT_MODEL,
        "recommended": "gemini/gemini-2.5-flash"
    }

@app.post("/ocr/extract", response_model=OCRResponse)
async def extract_latex_from_image(
    file: UploadFile = File(..., description="Image file to process"),
    topic: Optional[str] = Form(None, description="Optional topic context"),
    max_iterations: int = Form(5, description="Maximum refinement iterations"),
    similarity_threshold: float = Form(0.8, description="Similarity threshold"),
    model_name: Optional[str] = Form(None, description="Vision model to use")
):
    """Extract LaTeX from a single image."""
    
    start_time = datetime.now()
    trace_id = str(uuid.uuid4())
    
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Use custom model if specified
        if model_name and model_name != ocr_service.model_name:
            custom_service = OCRService(model_name)
            pipeline = custom_service.create_pipeline()
        else:
            pipeline = ocr_service.create_pipeline()
        
        # Process the image
        result = pipeline.process_image_to_lesson_script(
            image_path=temp_file_path,
            topic=topic,
            trace_id=trace_id,
            session_id=str(uuid.uuid4())
        )
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return OCRResponse(
            success=result['success'],
            latex_code=result.get('latex_code'),
            lesson_script=result.get('lesson_script'),
            similarity_score=result.get('ocr_results', {}).get('similarity_score') if result.get('ocr_results') else None,
            iterations=result.get('ocr_results', {}).get('iterations') if result.get('ocr_results') else None,
            processing_time=processing_time,
            error=result.get('error'),
            trace_id=trace_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        logger.error(traceback.format_exc())
        
        # Clean up temporary file if it exists
        try:
            if 'temp_file_path' in locals():
                os.unlink(temp_file_path)
        except:
            pass
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return OCRResponse(
            success=False,
            error=str(e),
            processing_time=processing_time,
            trace_id=trace_id
        )

@app.post("/ocr/batch", response_model=BatchOCRResponse)
async def batch_extract_latex(
    files: List[UploadFile] = File(..., description="Image files to process"),
    topic: Optional[str] = Form(None, description="Optional topic context"),
    max_iterations: int = Form(5, description="Maximum refinement iterations"),
    similarity_threshold: float = Form(0.8, description="Similarity threshold"),
    model_name: Optional[str] = Form(None, description="Vision model to use")
):
    """Process multiple images in batch."""
    
    start_time = datetime.now()
    batch_id = str(uuid.uuid4())
    temp_files = []
    
    try:
        # Validate files
        for file in files:
            if not file.content_type or not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail=f"File {file.filename} must be an image")
        
        # Save all uploaded files temporarily
        image_paths = []
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_files.append(temp_file.name)
                image_paths.append(temp_file.name)
        
        # Use custom model if specified
        if model_name and model_name != ocr_service.model_name:
            custom_service = OCRService(model_name)
            pipeline = custom_service.create_pipeline()
        else:
            pipeline = ocr_service.create_pipeline()
        
        # Process all images
        results = pipeline.batch_process_images(
            image_paths=image_paths,
            topic=topic,
            trace_id=batch_id,
            session_id=str(uuid.uuid4())
        )
        
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        
        # Calculate processing time and statistics
        processing_time = (datetime.now() - start_time).total_seconds()
        stats = pipeline.get_ocr_statistics(results)
        
        # Convert results to response format
        ocr_responses = []
        for i, result in enumerate(results):
            ocr_responses.append(OCRResponse(
                success=result['success'],
                latex_code=result.get('latex_code'),
                lesson_script=result.get('lesson_script'),
                similarity_score=result.get('ocr_results', {}).get('similarity_score') if result.get('ocr_results') else None,
                iterations=result.get('ocr_results', {}).get('iterations') if result.get('ocr_results') else None,
                processing_time=processing_time / len(results),  # Average per image
                error=result.get('error'),
                trace_id=f"{batch_id}-{i}"
            ))
        
        return BatchOCRResponse(
            success=True,
            total_images=stats['total'],
            successful=stats['successful'],
            failed=stats['failed'],
            success_rate=stats['success_rate'],
            average_iterations=stats.get('average_iterations'),
            average_similarity=stats.get('average_similarity_score'),
            processing_time=processing_time,
            results=ocr_responses,
            batch_id=batch_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        logger.error(traceback.format_exc())
        
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return BatchOCRResponse(
            success=False,
            total_images=len(files),
            successful=0,
            failed=len(files),
            success_rate=0.0,
            processing_time=processing_time,
            results=[],
            batch_id=batch_id
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if app.debug else "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OCR LaTeX Extraction API Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="Default model to use")
    
    args = parser.parse_args()
    
    # Update default model if specified
    if args.model != DEFAULT_MODEL:
        DEFAULT_MODEL = args.model
        logger.info(f"Using model: {DEFAULT_MODEL}")
    
    # Run the server
    uvicorn.run(
        "api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level="info"
    )