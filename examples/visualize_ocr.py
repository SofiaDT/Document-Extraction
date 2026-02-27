#!/usr/bin/env python3
"""
Visualize OCR results with bounding boxes and confidence scores on images.

Usage:
    python visualize_ocr.py data/input/document.jpg
    python visualize_ocr.py data/input/document.png --save data/output/visualization.png
    python visualize_ocr.py data/input/document.jpg --min-confidence 0.5 --details
    python visualize_ocr.py data/input/document.png --no-show
"""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "Document_Extraction"))

from src.image_extract import visualize_ocr_results, get_ocr_details


def main():
    parser = argparse.ArgumentParser(description="Visualize OCR bounding boxes with confidence scores")
    parser.add_argument("input", type=Path, help="Path to input image (jpg, png)")
    parser.add_argument("--save", type=Path, help="Save visualization to this path")
    parser.add_argument("--no-show", action="store_true", help="Don't display the plot")
    parser.add_argument("--min-confidence", type=float, default=0.0, 
                        help="Minimum confidence threshold (0.0-1.0, default: 0.0)")
    parser.add_argument("--details", action="store_true", 
                        help="Print detailed OCR results with confidence scores")
    
    args = parser.parse_args()
    
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        return 1
    
    if args.input.suffix.lower() not in {".jpg", ".jpeg", ".png"}:
        print(f"Error: Only JPG and PNG images are supported for visualization", file=sys.stderr)
        return 1
    
    try:
        # Print detailed OCR results if requested
        if args.details:
            print(f"\n{'Text':<30} | {'Confidence':<10} | {'Box Coordinates'}")
            print("-" * 80)
            ocr_data = get_ocr_details(args.input, min_confidence=args.min_confidence)
            for item in ocr_data:
                text = item['text'][:27] + "..." if len(item['text']) > 30 else item['text']
                score = item['confidence']
                coords = item['box']
                print(f"{text:<30} | {score:.3f}      | {coords}")
            print(f"\nTotal detections: {len(ocr_data)}")
            print()
        
        # Generate visualization
        visualize_ocr_results(
            args.input,
            output_path=args.save,
            show=not args.no_show,
            min_confidence=args.min_confidence
        )
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
