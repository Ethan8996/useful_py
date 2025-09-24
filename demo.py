#!/usr/bin/env python3
"""
Demo script for i18n_extractor.py

This script demonstrates how to use the I18nExtractor class to process
IDEA inspection XML files and extract hardcoded strings for i18n conversion.
"""

from i18n_extractor import I18nExtractor


def main():
    """Demo the i18n_extractor functionality."""
    print("=== i18n_extractor.py Demo ===\n")
    
    # Create an extractor instance with custom settings
    extractor = I18nExtractor(
        batch_size=3,  # Small batch size for demo
        translation_delay=0.5,  # Short delay for demo
        output_dir="demo_output"
    )
    
    # Process the sample XML file
    xml_files = ["sample_inspection.xml"]
    
    print("Processing sample XML file...")
    print(f"XML files to process: {xml_files}")
    
    # Run the extraction and translation process
    extractor.run(
        xml_paths=xml_files,
        translate=True,  # Enable translation
        markdown_output="demo_hardcoded_strings.md",
        excel_output="demo_hardcoded_strings.xlsx"
    )
    
    print("\nDemo completed! Check the 'demo_output' directory for results:")
    print("- demo_hardcoded_strings.md (Markdown report)")
    print("- demo_hardcoded_strings.xlsx (Excel report)")
    print("- i18n_extractor.log (Processing log)")
    print("- translation_progress_*.json (Translation progress files)")


if __name__ == "__main__":
    main()