import os
import subprocess
import tempfile
import shutil
from typing import Optional, Tuple
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class LatexCompiler:
    """
    Utility class for compiling LaTeX code to images.
    
    This class handles:
    1. Writing LaTeX code to temporary files
    2. Compiling LaTeX to PDF using pdflatex
    3. Converting PDF to PNG using ImageMagick or similar tools
    4. Cleanup of temporary files
    """
    
    def __init__(self, 
                 latex_command: str = "pdflatex",
                 convert_command: str = "convert",
                 dpi: int = 300,
                 output_format: str = "png"):
        """
        Initialize the LaTeX compiler.
        
        Args:
            latex_command: Command to use for LaTeX compilation (default: pdflatex)
            convert_command: Command to use for PDF to image conversion (default: convert)
            dpi: DPI for output image (default: 300)
            output_format: Output image format (default: png)
        """
        self.latex_command = latex_command
        self.convert_command = convert_command
        self.dpi = dpi
        self.output_format = output_format
        
        # Check if required tools are available
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """Check if required system dependencies are available."""
        try:
            # Check LaTeX
            subprocess.run([self.latex_command, "--version"], 
                         capture_output=True, check=True)
            logger.info(f"LaTeX compiler '{self.latex_command}' found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning(f"LaTeX compiler '{self.latex_command}' not found. "
                         "LaTeX compilation will use fallback method.")
        
        try:
            # Check ImageMagick convert
            subprocess.run([self.convert_command, "--version"], 
                         capture_output=True, check=True)
            logger.info(f"Image converter '{self.convert_command}' found")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning(f"Image converter '{self.convert_command}' not found. "
                         "Will try alternative conversion methods.")
    
    def compile_latex_to_image(self, 
                              latex_code: str, 
                              output_path: Optional[str] = None,
                              include_packages: bool = True) -> Optional[str]:
        """
        Compile LaTeX code to an image.
        
        Args:
            latex_code: The LaTeX code to compile
            output_path: Optional output path (if None, uses temporary file)
            include_packages: Whether to include standard packages in document
            
        Returns:
            Path to the generated image, or None if compilation failed
        """
        
        # Create temporary directory for compilation
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Prepare LaTeX document
                full_latex = self._prepare_latex_document(latex_code, include_packages)
                
                # Write LaTeX to file
                tex_file = os.path.join(temp_dir, "document.tex")
                with open(tex_file, 'w', encoding='utf-8') as f:
                    f.write(full_latex)
                
                # Compile LaTeX to PDF
                pdf_path = self._compile_to_pdf(tex_file, temp_dir)
                if not pdf_path:
                    return self._create_fallback_image(latex_code, output_path)
                
                # Convert PDF to image
                if output_path is None:
                    output_path = os.path.join(tempfile.gettempdir(), 
                                             f"latex_output_{hash(latex_code)}.{self.output_format}")
                
                success = self._convert_pdf_to_image(pdf_path, output_path)
                if success:
                    return output_path
                else:
                    return self._create_fallback_image(latex_code, output_path)
                    
            except Exception as e:
                logger.error(f"Error compiling LaTeX: {e}")
                return self._create_fallback_image(latex_code, output_path)
    
    def _prepare_latex_document(self, latex_code: str, include_packages: bool = True) -> str:
        """
        Prepare a complete LaTeX document from the provided code.
        
        Args:
            latex_code: The LaTeX code content
            include_packages: Whether to include standard packages
            
        Returns:
            Complete LaTeX document string
        """
        
        # Check if the code already includes documentclass
        if "\\documentclass" in latex_code:
            return latex_code
        
        # Standard packages for mathematical and graphical content
        packages = []
        if include_packages:
            packages = [
                "\\usepackage[utf8]{inputenc}",
                "\\usepackage[T1]{fontenc}",
                "\\usepackage{amsmath,amssymb,amsfonts}",
                "\\usepackage{tikz}",
                "\\usepackage{pgfplots}",
                "\\usepackage{array,tabularx,booktabs}",
                "\\usepackage{graphicx}",
                "\\usepackage{geometry}",
                "\\usepackage{xcolor}",
                "\\pgfplotsset{compat=1.18}",
                "\\usetikzlibrary{shapes,arrows,positioning,calc}",
            ]
        
        # Create complete document
        document_parts = [
            "\\documentclass[12pt]{article}",
            *packages,
            "\\geometry{margin=0.5in}",
            "\\pagestyle{empty}",  # Remove page numbers
            "\\begin{document}",
            latex_code,
            "\\end{document}"
        ]
        
        return "\n".join(document_parts)
    
    def _compile_to_pdf(self, tex_file: str, work_dir: str) -> Optional[str]:
        """
        Compile LaTeX file to PDF.
        
        Args:
            tex_file: Path to the .tex file
            work_dir: Working directory for compilation
            
        Returns:
            Path to generated PDF, or None if compilation failed
        """
        try:
            # Run pdflatex
            cmd = [
                self.latex_command,
                "-interaction=nonstopmode",
                "-output-directory", work_dir,
                tex_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=work_dir)
            
            # Check if PDF was created
            pdf_path = os.path.join(work_dir, "document.pdf")
            if os.path.exists(pdf_path):
                logger.info("LaTeX compilation successful")
                return pdf_path
            else:
                logger.error(f"LaTeX compilation failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error running LaTeX compiler: {e}")
            return None
    
    def _convert_pdf_to_image(self, pdf_path: str, output_path: str) -> bool:
        """
        Convert PDF to image.
        
        Args:
            pdf_path: Path to the PDF file
            output_path: Path for the output image
            
        Returns:
            True if conversion was successful, False otherwise
        """
        try:
            # Try ImageMagick convert first
            if self._try_imagemagick_convert(pdf_path, output_path):
                return True
            
            # Try alternative methods
            if self._try_pillow_convert(pdf_path, output_path):
                return True
                
            logger.error("All PDF to image conversion methods failed")
            return False
            
        except Exception as e:
            logger.error(f"Error converting PDF to image: {e}")
            return False
    
    def _try_imagemagick_convert(self, pdf_path: str, output_path: str) -> bool:
        """Try converting PDF to image using ImageMagick."""
        try:
            cmd = [
                self.convert_command,
                "-density", str(self.dpi),
                "-quality", "90",
                "-background", "white",
                "-alpha", "remove",
                f"{pdf_path}[0]",  # First page only
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info("ImageMagick conversion successful")
                return True
            else:
                logger.warning(f"ImageMagick conversion failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.warning(f"ImageMagick conversion error: {e}")
            return False
    
    def _try_pillow_convert(self, pdf_path: str, output_path: str) -> bool:
        """Try converting PDF to image using Pillow with pdf2image."""
        try:
            # Try importing pdf2image
            from pdf2image import convert_from_path
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=self.dpi, first_page=1, last_page=1)
            
            if images:
                # Save the first (and only) image
                images[0].save(output_path, self.output_format.upper())
                logger.info("pdf2image conversion successful")
                return True
            else:
                logger.warning("pdf2image conversion produced no images")
                return False
                
        except ImportError:
            logger.warning("pdf2image not available")
            return False
        except Exception as e:
            logger.warning(f"pdf2image conversion error: {e}")
            return False
    
    def _create_fallback_image(self, latex_code: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Create a fallback image when LaTeX compilation fails.
        
        Args:
            latex_code: The original LaTeX code
            output_path: Optional output path
            
        Returns:
            Path to the fallback image
        """
        try:
            if output_path is None:
                output_path = os.path.join(tempfile.gettempdir(), 
                                         f"latex_fallback_{hash(latex_code)}.png")
            
            # Create a simple white image with error message
            img = Image.new('RGB', (800, 600), 'white')
            
            # Try to add text if PIL supports it
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(img)
                
                # Try to use a default font
                try:
                    font = ImageFont.load_default()
                except:
                    font = None
                
                # Add error message
                error_text = "LaTeX Compilation Failed\n\nOriginal LaTeX code:\n" + latex_code[:200]
                if len(latex_code) > 200:
                    error_text += "..."
                
                draw.text((10, 10), error_text, fill='black', font=font)
                
            except ImportError:
                # PIL drawing not available, just save blank image
                pass
            
            img.save(output_path)
            logger.info(f"Created fallback image: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating fallback image: {e}")
            return None


# Global instance for easy access
_default_compiler = None

def get_latex_compiler() -> LatexCompiler:
    """Get the default LaTeX compiler instance."""
    global _default_compiler
    if _default_compiler is None:
        _default_compiler = LatexCompiler()
    return _default_compiler

def compile_latex_to_image(latex_code: str, output_path: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to compile LaTeX code to image.
    
    Args:
        latex_code: The LaTeX code to compile
        output_path: Optional output path
        
    Returns:
        Path to generated image, or None if failed
    """
    compiler = get_latex_compiler()
    return compiler.compile_latex_to_image(latex_code, output_path)