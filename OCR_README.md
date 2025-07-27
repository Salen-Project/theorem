# OCR LaTeX Extraction System

This system provides advanced OCR functionality for extracting LaTeX code from images with a verification feedback loop. It's designed to handle complex mathematical content, diagrams, tables, and geometric shapes by converting everything visible in images into precise LaTeX code.

## Features

### Core Capabilities
- **Complete LaTeX Extraction**: Extracts ALL content from images including:
  - Mathematical formulas and equations
  - Tables and data structures
  - Graphs and charts (using pgfplots)
  - Complex geometric shapes (using tikz)
  - Text content with proper formatting
  - Diagrams and technical illustrations

### Verification System
- **Iterative Refinement**: Up to 5 iterations of improvement
- **Image Comparison**: Converts LaTeX back to images for verification
- **Similarity Scoring**: Automated assessment of extraction accuracy
- **Feedback Loop**: Uses comparison results to refine LaTeX code

### Integration
- **Lesson Script Generation**: Automatically generates educational content from extracted LaTeX
- **Pipeline Integration**: Seamlessly integrates with existing video generation workflow
- **Batch Processing**: Handle multiple images efficiently

## System Architecture

```
Input Image → OCR Extraction → LaTeX Code → LaTeX Compiler → Generated Image
     ↑                                                              ↓
     └── Comparison & Refinement ← Image Comparison ←──────────────┘
                    ↓
              Lesson Script Generation
```

### Components

1. **OCRLatexExtractor** (`src/core/ocr_latex_extractor.py`)
   - Main OCR engine with verification loop
   - Handles LaTeX extraction and refinement
   - Manages iteration control and similarity thresholds

2. **LatexCompiler** (`src/utils/latex_compiler.py`)
   - Compiles LaTeX code to images using system tools
   - Supports multiple conversion methods (ImageMagick, pdf2image)
   - Handles fallback scenarios

3. **OCRPipelineIntegration** (`src/core/ocr_integration.py`)
   - Connects OCR with the broader system
   - Generates lesson scripts from LaTeX
   - Manages batch processing and statistics

4. **Command Line Interface** (`ocr_latex_cli.py`)
   - User-friendly CLI for OCR operations
   - Single image and batch processing modes
   - Configurable parameters and output formats

## Installation

### System Dependencies

The OCR system requires LaTeX and ImageMagick to be installed on your system:

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install texlive-full imagemagick
```

#### macOS
```bash
brew install --cask mactex
brew install imagemagick
```

#### Windows
1. Install MiKTeX: https://miktex.org/download
2. Install ImageMagick: https://imagemagick.org/script/download.php#windows

### Python Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

The OCR system adds these specific dependencies:
- `pdf2image~=1.17.0` - For LaTeX PDF to image conversion
- `pypdf~=5.1.0` - For PDF handling

## Usage

### Command Line Interface

#### Single Image Processing
```bash
python ocr_latex_cli.py --image path/to/image.png --model gemini/gemini-1.5-pro-002
```

#### Batch Processing
```bash
python ocr_latex_cli.py --batch ./images/ --model vertex_ai/gemini-1.5-flash-002 --topic "calculus"
```

#### Advanced Options
```bash
python ocr_latex_cli.py --image diagram.png \
                        --model gemini/gemini-1.5-pro-002 \
                        --output ./results/ \
                        --max-iterations 3 \
                        --threshold 0.85 \
                        --topic "linear algebra" \
                        --save-summary
```

### Python API

#### Basic Usage
```python
from mllm_tools.litellm import LiteLLMWrapper
from src.core.ocr_integration import create_ocr_pipeline

# Initialize model
model = LiteLLMWrapper(model_name="gemini/gemini-1.5-pro-002")

# Create OCR pipeline
ocr_pipeline = create_ocr_pipeline(model, output_dir="./results")

# Process image
result = ocr_pipeline.process_image_to_lesson_script(
    image_path="math_formula.png",
    topic="calculus"
)

print(f"LaTeX: {result['latex_code']}")
print(f"Lesson: {result['lesson_script']}")
```

#### Advanced Usage
```python
from src.core.ocr_latex_extractor import create_ocr_latex_extractor

# Create OCR extractor with custom settings
ocr_extractor = create_ocr_latex_extractor(
    vision_model=model,
    max_iterations=5,
    similarity_threshold=0.8
)

# Extract LaTeX with detailed results
ocr_results = ocr_extractor.extract_latex_from_image("complex_diagram.png")

print(f"Success: {ocr_results['success']}")
print(f"Iterations: {ocr_results['iterations']}")
print(f"Similarity: {ocr_results['similarity_score']}")
print(f"LaTeX: {ocr_results['latex_code']}")
```

## Configuration

### OCR Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_iterations` | 5 | Maximum refinement iterations |
| `similarity_threshold` | 0.8 | Minimum similarity score to accept |
| `dpi` | 300 | Image resolution for LaTeX compilation |
| `output_format` | "png" | Output image format |

### Model Selection

Supported vision models:
- `gemini/gemini-1.5-pro-002` - Best accuracy for complex content
- `gemini/gemini-1.5-flash-002` - Faster processing
- `vertex_ai/gemini-1.5-pro-002` - Enterprise version
- `vertex_ai/gemini-1.5-flash-002` - Enterprise fast version

### Environment Variables

Set up your model credentials:
```bash
export GOOGLE_API_KEY="your-api-key"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
```

## Output Files

The system generates several output files for each processed image:

### For image `example.png`:
- `ocr_example_latex.tex` - Extracted LaTeX code
- `ocr_example_lesson_script.txt` - Generated lesson script
- `ocr_example_ocr_metadata.json` - Processing metadata and statistics

### Batch Processing:
- `batch_processing_summary.json` - Overall statistics and results

## LaTeX Packages Support

The system automatically includes comprehensive LaTeX packages:

### Mathematical Content
- `amsmath, amssymb, amsfonts` - Advanced math symbols and environments
- `mathtools` - Extended math functionality

### Graphics and Diagrams
- `tikz` - Vector graphics and diagrams
- `pgfplots` - Data visualization and plotting
- `graphicx` - Image handling

### Tables and Layout
- `array, tabularx, booktabs` - Professional table formatting
- `geometry` - Page layout control

### Specialized Packages
- `xcolor` - Color support
- `inputenc, fontenc` - Character encoding

## Examples

### Mathematical Formula
Input: Image with equation `E = mc²`

Output LaTeX:
```latex
\begin{equation}
E = mc^2
\end{equation}
```

### Complex Diagram
Input: Image with geometric shapes and annotations

Output LaTeX:
```latex
\begin{tikzpicture}
\draw (0,0) -- (3,0) -- (1.5,2.6) -- cycle;
\node at (1.5,-0.3) {Base};
\node at (0.75,1.3) {Height};
\draw[dashed] (1.5,0) -- (1.5,2.6);
\end{tikzpicture}
```

### Data Table
Input: Image with tabular data

Output LaTeX:
```latex
\begin{tabular}{|c|c|c|}
\hline
Name & Age & Score \\
\hline
Alice & 25 & 95 \\
Bob & 30 & 87 \\
Charlie & 28 & 92 \\
\hline
\end{tabular}
```

## Troubleshooting

### Common Issues

#### LaTeX Compilation Errors
- **Issue**: LaTeX compilation fails
- **Solution**: Check that `pdflatex` is installed and in PATH
- **Alternative**: System will use fallback image generation

#### ImageMagick Conversion Errors
- **Issue**: PDF to image conversion fails
- **Solution**: Install ImageMagick or pdf2image package
- **Check**: `convert --version` and `python -c "import pdf2image"`

#### Low Similarity Scores
- **Issue**: OCR produces low similarity scores
- **Solution**: 
  - Try different vision models
  - Adjust similarity threshold
  - Increase max iterations
  - Ensure input image quality

#### Memory Issues
- **Issue**: Out of memory during processing
- **Solution**:
  - Process images in smaller batches
  - Reduce image resolution
  - Use faster models for large batches

### Debugging

Enable verbose output:
```bash
python ocr_latex_cli.py --image test.png --model gemini/gemini-1.5-pro-002 --verbose
```

Check system dependencies:
```bash
pdflatex --version
convert --version
python -c "import pdf2image; print('pdf2image OK')"
```

## Performance Optimization

### Speed Improvements
- Use `gemini-1.5-flash-002` for faster processing
- Reduce `max_iterations` for quicker results
- Lower `similarity_threshold` if high accuracy isn't critical

### Accuracy Improvements
- Use `gemini-1.5-pro-002` for best results
- Increase `max_iterations` for complex content
- Ensure high-quality input images
- Provide relevant `topic` context

### Batch Processing
- Process images in parallel (future enhancement)
- Use appropriate batch sizes based on available memory
- Monitor system resources during large batches

## Integration with Video Generation

The OCR system integrates seamlessly with the existing video generation pipeline:

```python
# In your video generation code
from src.core.ocr_integration import create_ocr_pipeline

# Create OCR pipeline
ocr_pipeline = create_ocr_pipeline(vision_model, output_dir)

# Process image and get lesson script
result = ocr_pipeline.process_image_to_lesson_script(image_path, topic)

# Use the lesson script in your video generation
lesson_script = result['lesson_script']
# ... continue with video generation using lesson_script
```

## API Reference

### OCRLatexExtractor

#### Methods
- `extract_latex_from_image(image_path, trace_id, session_id)` - Main extraction method
- `_extract_latex_initial(image_path, trace_id, session_id)` - Initial LaTeX extraction
- `_latex_to_image(latex_code, trace_id, session_id)` - Convert LaTeX to image
- `_compare_images(original_path, generated_path, latex_code, trace_id, session_id)` - Compare images
- `_refine_latex(current_latex, comparison_result, trace_id, session_id)` - Refine LaTeX based on feedback

### OCRPipelineIntegration

#### Methods
- `process_image_to_lesson_script(image_path, topic, trace_id, session_id)` - Complete pipeline
- `generate_lesson_script_from_latex(latex_code, topic, trace_id, session_id)` - Generate lesson script
- `batch_process_images(image_paths, topic, trace_id, session_id)` - Batch processing
- `get_ocr_statistics(results)` - Calculate processing statistics

### LatexCompiler

#### Methods
- `compile_latex_to_image(latex_code, output_path, include_packages)` - Compile LaTeX to image
- `_prepare_latex_document(latex_code, include_packages)` - Prepare complete LaTeX document
- `_compile_to_pdf(tex_file, work_dir)` - Compile LaTeX to PDF
- `_convert_pdf_to_image(pdf_path, output_path)` - Convert PDF to image

## Contributing

To contribute to the OCR system:

1. Follow the existing code style and patterns
2. Add comprehensive tests for new functionality
3. Update documentation for any API changes
4. Test with various image types and complexity levels

## License

This OCR system is part of the larger video generation project and follows the same license terms.