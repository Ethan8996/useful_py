#!/usr/bin/env python3
"""
i18n_extractor.py - A tool to extract hardcoded strings from IDEA inspection XML files

This script parses XML files from JetBrains IDEA containing hardcoded string inspections,
extracts file names, package names, and hardcoded strings, detects language types,
translates Chinese strings to English, and outputs results in Markdown and Excel formats.

Features:
- Parse IDEA inspection XML files
- Extract and categorize hardcoded strings
- Detect Chinese vs English/format strings
- Batch translation with error handling
- Progress bar for translation status
- Output to Markdown and Excel formats
- Customizable batch processing
- Comprehensive error handling

Author: Ethan8996
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from xml.etree import ElementTree as ET

import pandas as pd
from tqdm import tqdm

# Set default region for translators to avoid network check during import
os.environ.setdefault("translators_default_region", "EN")

# Try to import translators with fallback
try:
    import translators as ts
    TRANSLATORS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Translators not available: {e}")
    ts = None
    TRANSLATORS_AVAILABLE = False


class I18nExtractor:
    """Main class for extracting and processing hardcoded strings from IDEA inspection XML files."""
    
    def __init__(self, batch_size: int = 10, translation_delay: float = 1.0, output_dir: str = "output"):
        """
        Initialize the I18n extractor.
        
        Args:
            batch_size: Number of strings to process in each batch
            translation_delay: Delay between translation requests in seconds
            output_dir: Directory to save output files
        """
        self.batch_size = batch_size
        self.translation_delay = translation_delay
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.output_dir / 'i18n_extractor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.stats = {
            'total_strings': 0,
            'chinese_strings': 0,
            'english_strings': 0,
            'translated_strings': 0,
            'failed_translations': 0
        }
    
    def is_chinese_string(self, text: str) -> bool:
        """
        Detect if a string contains Chinese characters.
        
        Args:
            text: The string to check
            
        Returns:
            True if the string contains Chinese characters, False otherwise
        """
        # Remove quotes and whitespace
        text = text.strip().strip('"\'')
        
        # Check for Chinese characters (CJK Unified Ideographs)
        chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
        return bool(chinese_pattern.search(text))
    
    def is_format_string(self, text: str) -> bool:
        """
        Detect if a string is likely a format string (contains placeholders).
        
        Args:
            text: The string to check
            
        Returns:
            True if the string appears to be a format string
        """
        text = text.strip().strip('"\'')
        
        # Common format string patterns
        format_patterns = [
            r'%[sdifg]',  # printf-style
            r'\{[^}]*\}',  # Python/Java format strings
            r'\$\{[^}]*\}',  # Template strings
            r'%[0-9]*[sdifg]',  # printf with width
        ]
        
        for pattern in format_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def categorize_string(self, text: str) -> str:
        """
        Categorize a string as Chinese, English, or Format.
        
        Args:
            text: The string to categorize
            
        Returns:
            Category: 'Chinese', 'English', or 'Format'
        """
        if self.is_format_string(text):
            return 'Format'
        elif self.is_chinese_string(text):
            return 'Chinese'
        else:
            return 'English'
    
    def translate_text(self, text: str, from_lang: str = 'zh', to_lang: str = 'en') -> Optional[str]:
        """
        Translate text using multiple translation services with fallback.
        
        Args:
            text: Text to translate
            from_lang: Source language code
            to_lang: Target language code
            
        Returns:
            Translated text or None if translation fails
        """
        if not TRANSLATORS_AVAILABLE:
            self.logger.warning("Translation services not available - skipping translation")
            return f"[TRANSLATION_UNAVAILABLE] {text}"
        
        # Clean the text
        clean_text = text.strip().strip('"\'')
        
        if not clean_text:
            return None
        
        # Try multiple translation services
        translation_services = ['google', 'bing', 'baidu']
        
        for service in translation_services:
            try:
                result = ts.translate_text(clean_text, translator=service, from_language=from_lang, to_language=to_lang)
                if result and result != clean_text:
                    self.logger.debug(f"Translated '{clean_text}' to '{result}' using {service}")
                    return result
            except Exception as e:
                self.logger.debug(f"Translation failed with {service}: {e}")
                continue
        
        self.logger.warning(f"Failed to translate: {clean_text}")
        return None
    
    def parse_xml_file(self, xml_path: str) -> List[Dict]:
        """
        Parse an IDEA inspection XML file and extract hardcoded string information.
        
        Args:
            xml_path: Path to the XML file
            
        Returns:
            List of dictionaries containing extracted string information
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except ET.ParseError as e:
            self.logger.error(f"Error parsing XML file {xml_path}: {e}")
            return []
        
        strings_data = []
        
        for problem in root.findall('problem'):
            # Extract file information
            file_elem = problem.find('file')
            file_path = file_elem.text if file_elem is not None else ''
            
            # Extract package information
            package_elem = problem.find('package')
            package_name = package_elem.text if package_elem is not None else ''
            
            # Extract line number
            line_elem = problem.find('line')
            line_number = line_elem.text if line_elem is not None else ''
            
            # Extract module information
            module_elem = problem.find('module')
            module_name = module_elem.text if module_elem is not None else ''
            
            # Extract the hardcoded string from description or highlighted_element
            description_elem = problem.find('description')
            highlighted_elem = problem.find('highlighted_element')
            
            hardcoded_string = ''
            if highlighted_elem is not None:
                hardcoded_string = highlighted_elem.text
            elif description_elem is not None:
                # Extract string from description like: Hardcoded string literal: "并发任务异常："
                desc_text = description_elem.text
                if desc_text:
                    match = re.search(r'Hardcoded string literal:\s*(.+)$', desc_text)
                    if match:
                        hardcoded_string = match.group(1)
            
            if hardcoded_string:
                # Clean file path (remove file:// prefix and $PROJECT_DIR$)
                clean_file_path = file_path.replace('file://$PROJECT_DIR$/', '').replace('file://', '')
                
                string_info = {
                    'file_path': clean_file_path,
                    'package': package_name,
                    'module': module_name,
                    'line': line_number,
                    'original_string': hardcoded_string,
                    'category': self.categorize_string(hardcoded_string),
                    'translated_string': '',
                    'translation_status': 'Pending'
                }
                
                strings_data.append(string_info)
                self.stats['total_strings'] += 1
                
                # Update category statistics
                if string_info['category'] == 'Chinese':
                    self.stats['chinese_strings'] += 1
                elif string_info['category'] == 'English':
                    self.stats['english_strings'] += 1
        
        self.logger.info(f"Extracted {len(strings_data)} hardcoded strings from {xml_path}")
        return strings_data
    
    def translate_strings_batch(self, strings_data: List[Dict]) -> List[Dict]:
        """
        Translate Chinese strings in batches with progress tracking.
        
        Args:
            strings_data: List of string information dictionaries
            
        Returns:
            Updated list with translation results
        """
        chinese_strings = [item for item in strings_data if item['category'] == 'Chinese']
        
        if not chinese_strings:
            self.logger.info("No Chinese strings found for translation")
            return strings_data
        
        self.logger.info(f"Starting translation of {len(chinese_strings)} Chinese strings")
        
        # Process in batches
        total_batches = (len(chinese_strings) + self.batch_size - 1) // self.batch_size
        
        with tqdm(total=len(chinese_strings), desc="Translating strings") as pbar:
            for batch_idx in range(0, len(chinese_strings), self.batch_size):
                batch = chinese_strings[batch_idx:batch_idx + self.batch_size]
                
                for item in batch:
                    try:
                        translated = self.translate_text(item['original_string'])
                        if translated:
                            item['translated_string'] = translated
                            item['translation_status'] = 'Success'
                            self.stats['translated_strings'] += 1
                        else:
                            item['translation_status'] = 'Failed'
                            self.stats['failed_translations'] += 1
                    except Exception as e:
                        self.logger.error(f"Translation error for '{item['original_string']}': {e}")
                        item['translation_status'] = 'Error'
                        self.stats['failed_translations'] += 1
                    
                    pbar.update(1)
                
                # Save progress after each batch
                if batch_idx + self.batch_size < len(chinese_strings):
                    self.save_progress(strings_data, batch_idx // self.batch_size + 1, total_batches)
                
                # Delay between batches to avoid rate limiting
                if batch_idx + self.batch_size < len(chinese_strings):
                    time.sleep(self.translation_delay)
        
        return strings_data
    
    def save_progress(self, strings_data: List[Dict], batch_num: int, total_batches: int):
        """
        Save translation progress to a JSON file.
        
        Args:
            strings_data: Current strings data
            batch_num: Current batch number
            total_batches: Total number of batches
        """
        progress_file = self.output_dir / f'translation_progress_batch_{batch_num}_of_{total_batches}.json'
        
        try:
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'batch_info': f'Batch {batch_num} of {total_batches}',
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'statistics': self.stats,
                    'strings_data': strings_data
                }, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Progress saved to {progress_file}")
        except Exception as e:
            self.logger.error(f"Failed to save progress: {e}")
    
    def export_to_markdown(self, strings_data: List[Dict], output_file: str = 'hardcoded_strings.md'):
        """
        Export strings data to Markdown format.
        
        Args:
            strings_data: List of string information dictionaries
            output_file: Output file name
        """
        output_path = self.output_dir / output_file
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("# Hardcoded Strings Analysis\n\n")
                
                # Write statistics
                f.write("## Statistics\n\n")
                f.write(f"- Total strings: {self.stats['total_strings']}\n")
                f.write(f"- Chinese strings: {self.stats['chinese_strings']}\n")
                f.write(f"- English strings: {self.stats['english_strings']}\n")
                f.write(f"- Successfully translated: {self.stats['translated_strings']}\n")
                f.write(f"- Failed translations: {self.stats['failed_translations']}\n\n")
                
                # Write strings table
                f.write("## Extracted Strings\n\n")
                f.write("| File Path | Package | Line | Category | Original String | Translated String | Status |\n")
                f.write("|-----------|---------|------|----------|-----------------|-------------------|--------|\n")
                
                for item in strings_data:
                    file_path = item['file_path'][:50] + '...' if len(item['file_path']) > 50 else item['file_path']
                    package = item['package'][:30] + '...' if len(item['package']) > 30 else item['package']
                    original = item['original_string'][:40] + '...' if len(item['original_string']) > 40 else item['original_string']
                    translated = item['translated_string'][:40] + '...' if len(item['translated_string']) > 40 else item['translated_string']
                    
                    f.write(f"| {file_path} | {package} | {item['line']} | {item['category']} | {original} | {translated} | {item['translation_status']} |\n")
            
            self.logger.info(f"Markdown report exported to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to export Markdown: {e}")
    
    def export_to_excel(self, strings_data: List[Dict], output_file: str = 'hardcoded_strings.xlsx'):
        """
        Export strings data to Excel format.
        
        Args:
            strings_data: List of string information dictionaries
            output_file: Output file name
        """
        output_path = self.output_dir / output_file
        
        try:
            # Create DataFrame
            df = pd.DataFrame(strings_data)
            
            # Reorder columns for better readability
            columns_order = [
                'file_path', 'package', 'module', 'line', 'category',
                'original_string', 'translated_string', 'translation_status'
            ]
            df = df[columns_order]
            
            # Create Excel writer with multiple sheets
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Main data sheet
                df.to_excel(writer, sheet_name='Hardcoded Strings', index=False)
                
                # Statistics sheet
                stats_df = pd.DataFrame([
                    ['Total strings', self.stats['total_strings']],
                    ['Chinese strings', self.stats['chinese_strings']],
                    ['English strings', self.stats['english_strings']],
                    ['Successfully translated', self.stats['translated_strings']],
                    ['Failed translations', self.stats['failed_translations']]
                ], columns=['Metric', 'Value'])
                stats_df.to_excel(writer, sheet_name='Statistics', index=False)
                
                # Chinese strings only (for translation review)
                chinese_df = df[df['category'] == 'Chinese']
                chinese_df.to_excel(writer, sheet_name='Chinese Strings', index=False)
            
            self.logger.info(f"Excel report exported to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to export Excel: {e}")
    
    def process_xml_files(self, xml_paths: List[str], translate: bool = True) -> List[Dict]:
        """
        Process multiple XML files and extract hardcoded strings.
        
        Args:
            xml_paths: List of paths to XML files
            translate: Whether to translate Chinese strings
            
        Returns:
            Combined list of all extracted strings
        """
        all_strings = []
        
        for xml_path in xml_paths:
            if not os.path.exists(xml_path):
                self.logger.error(f"XML file not found: {xml_path}")
                continue
            
            strings_data = self.parse_xml_file(xml_path)
            all_strings.extend(strings_data)
        
        if translate and all_strings:
            all_strings = self.translate_strings_batch(all_strings)
        
        return all_strings
    
    def run(self, xml_paths: List[str], translate: bool = True, 
            markdown_output: str = 'hardcoded_strings.md',
            excel_output: str = 'hardcoded_strings.xlsx'):
        """
        Main execution method.
        
        Args:
            xml_paths: List of XML file paths to process
            translate: Whether to translate Chinese strings
            markdown_output: Markdown output filename
            excel_output: Excel output filename
        """
        self.logger.info("Starting i18n extraction process")
        
        # Process XML files
        strings_data = self.process_xml_files(xml_paths, translate)
        
        if not strings_data:
            self.logger.error("No strings were extracted from the provided XML files")
            return
        
        # Export results
        self.export_to_markdown(strings_data, markdown_output)
        self.export_to_excel(strings_data, excel_output)
        
        # Final statistics
        self.logger.info("Extraction completed successfully")
        self.logger.info(f"Statistics: {self.stats}")


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Extract hardcoded strings from IDEA inspection XML files for i18n conversion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python i18n_extractor.py inspection.xml
  python i18n_extractor.py file1.xml file2.xml --no-translate
  python i18n_extractor.py inspection.xml --batch-size 5 --delay 2.0
  python i18n_extractor.py inspection.xml --output-dir ./translations
        """
    )
    
    parser.add_argument('xml_files', nargs='+', help='One or more XML inspection files to process')
    parser.add_argument('--no-translate', action='store_true', help='Skip translation of Chinese strings')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of strings to translate per batch (default: 10)')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between translation batches in seconds (default: 1.0)')
    parser.add_argument('--output-dir', default='output', help='Output directory for results (default: output)')
    parser.add_argument('--markdown-output', default='hardcoded_strings.md', help='Markdown output filename')
    parser.add_argument('--excel-output', default='hardcoded_strings.xlsx', help='Excel output filename')
    
    args = parser.parse_args()
    
    # Validate XML files
    for xml_file in args.xml_files:
        if not os.path.exists(xml_file):
            print(f"Error: XML file not found: {xml_file}")
            sys.exit(1)
    
    # Create extractor and run
    extractor = I18nExtractor(
        batch_size=args.batch_size,
        translation_delay=args.delay,
        output_dir=args.output_dir
    )
    
    extractor.run(
        xml_paths=args.xml_files,
        translate=not args.no_translate,
        markdown_output=args.markdown_output,
        excel_output=args.excel_output
    )


if __name__ == '__main__':
    main()