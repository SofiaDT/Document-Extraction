from pathlib import Path
import easyocr
import cv2
import numpy as np
import matplotlib.pyplot as plt


def extract_text_from_image(image_path: Path) -> str:
    """Extract text from image (JPG, PNG) using OCR."""
    try:
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(str(image_path))
        text = '\n'.join([item[1] for item in results])
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from image {image_path}: {e}")


def visualize_ocr_results(image_path: Path, output_path: Path = None, show: bool = True, min_confidence: float = 0.0) -> None:
    """
    Visualize OCR results with bounding boxes and confidence scores on the image.
    
    Args:
        image_path: Path to the input image
        output_path: Optional path to save the visualization
        show: Whether to display the plot (default: True)
        min_confidence: Minimum confidence threshold (0.0-1.0, default: 0.0)
    """
    try:
        # Read image and perform OCR
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(str(image_path))
        
        # Load image with OpenCV
        img = cv2.imread(str(image_path))
        if img is None:
            raise RuntimeError(f"Failed to load image: {image_path}")
        
        img_plot = img.copy()
        
        # Draw bounding boxes and text labels with confidence scores
        for (box, text, confidence) in results:
            # Skip if below confidence threshold
            if confidence < min_confidence:
                continue
                
            pts = np.array(box, dtype=int)
            cv2.polylines(img_plot, [pts], True, (0, 255, 0), 2)
            x, y = pts[0]
            
            # Display text without confidence score
            cv2.putText(img_plot, text, (x, y - 5), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        # Display or save the result
        plt.figure(figsize=(8, 10))
        plt.imshow(cv2.cvtColor(img_plot, cv2.COLOR_BGR2RGB))
        plt.axis("off")
        plt.title("OCR Bounding Boxes (Detected Text)")
        
        if output_path:
            plt.savefig(output_path, bbox_inches='tight', dpi=150)
            print(f"Visualization saved to: {output_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
            
    except Exception as e:
        raise RuntimeError(f"Failed to visualize OCR results for {image_path}: {e}")


def get_ocr_details(image_path: Path, min_confidence: float = 0.0) -> list[dict]:
    """
    Extract OCR results with detailed information including bounding boxes and confidence scores.
    
    Args:
        image_path: Path to the input image
        min_confidence: Minimum confidence threshold (0.0-1.0, default: 0.0)
    
    Returns:
        List of dictionaries with keys: text, confidence, box (coordinates)
    """
    try:
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(str(image_path))
        
        ocr_data = []
        for (box, text, confidence) in results:
            if confidence >= min_confidence:
                ocr_data.append({
                    'text': text,
                    'confidence': confidence,
                    'box': box.astype(int).tolist() if isinstance(box, np.ndarray) else box
                })
        
        return ocr_data
    except Exception as e:
        raise RuntimeError(f"Failed to extract OCR details from {image_path}: {e}")
