"""Example: Extract OCR results with confidence scores and bounding boxes."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "Document_Extraction"))

from src.image_extract import get_ocr_details


def main():
    """Extract and display OCR data with confidence scores."""
    
    # Example image path - update with your actual file
    image_path = Path("data/input/example.png")
    
    if not image_path.exists():
        print(f"Note: Update image_path in this script to point to your image file")
        print(f"Expected: {image_path}")
        return
    
    print(f"\nExtracting OCR data from: {image_path.name}\n")
    
    # Get all OCR results (no confidence threshold)
    ocr_results = get_ocr_details(image_path, min_confidence=0.0)
    
    # Display results
    print(f"{'Text':<35} | {'Confidence':<10} | {'Box Coordinates'}")
    print("-" * 100)
    
    for item in ocr_results:
        text = item['text']
        text_display = text[:32] + "..." if len(text) > 35 else text
        confidence = item['confidence']
        box = item['box']
        print(f"{text_display:<35} | {confidence:.3f}      | {box}")
    
    print(f"\n✓ Total detections: {len(ocr_results)}")
    
    # Filter by confidence threshold
    high_confidence = get_ocr_details(image_path, min_confidence=0.7)
    print(f"✓ High confidence (≥0.7): {len(high_confidence)}")
    
    # Access individual fields
    if ocr_results:
        print("\n--- Example: First detected text ---")
        first = ocr_results[0]
        print(f"Text: {first['text']}")
        print(f"Confidence: {first['confidence']:.3f}")
        print(f"Bounding box: {first['box']}")


if __name__ == "__main__":
    main()
