#!/usr/bin/env python3
"""
Unit tests for i18n_extractor.py

This file contains basic tests to verify the core functionality
of the I18nExtractor class.
"""

import os
import tempfile
import unittest
from pathlib import Path

from i18n_extractor import I18nExtractor


class TestI18nExtractor(unittest.TestCase):
    """Test cases for I18nExtractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.extractor = I18nExtractor(
            batch_size=2,
            translation_delay=0.1,
            output_dir=self.temp_dir
        )
    
    def test_is_chinese_string(self):
        """Test Chinese string detection."""
        # Chinese strings
        self.assertTrue(self.extractor.is_chinese_string('"并发任务异常："'))
        self.assertTrue(self.extractor.is_chinese_string('"用户信息"'))
        
        # Non-Chinese strings
        self.assertFalse(self.extractor.is_chinese_string('"Database connection established"'))
        self.assertFalse(self.extractor.is_chinese_string('"Hello World"'))
    
    def test_is_format_string(self):
        """Test format string detection."""
        # Format strings
        self.assertTrue(self.extractor.is_format_string('"错误日志: %s"'))
        self.assertTrue(self.extractor.is_format_string('"用户信息: {name: %s, id: %d}"'))
        self.assertTrue(self.extractor.is_format_string('"Value: ${value}"'))
        
        # Non-format strings
        self.assertFalse(self.extractor.is_format_string('"简单字符串"'))
        self.assertFalse(self.extractor.is_format_string('"Simple string"'))
    
    def test_categorize_string(self):
        """Test string categorization."""
        # Chinese strings
        self.assertEqual(self.extractor.categorize_string('"并发任务异常："'), 'Chinese')
        
        # English strings
        self.assertEqual(self.extractor.categorize_string('"Database connection established"'), 'English')
        
        # Format strings (should take precedence over language)
        self.assertEqual(self.extractor.categorize_string('"错误日志: %s"'), 'Format')
        self.assertEqual(self.extractor.categorize_string('"Error: %s"'), 'Format')
    
    def test_parse_xml_file(self):
        """Test XML file parsing."""
        # Create a temporary XML file
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<problems>
  <problem>
    <file>file://$PROJECT_DIR$/src/test/TestClass.java</file>
    <line>25</line>
    <module>test-module</module>
    <package>com.test</package>
    <description>Hardcoded string literal: "测试字符串"</description>
    <highlighted_element>"测试字符串"</highlighted_element>
  </problem>
</problems>'''
        
        temp_xml = Path(self.temp_dir) / 'test.xml'
        with open(temp_xml, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        # Parse the XML file
        results = self.extractor.parse_xml_file(str(temp_xml))
        
        # Verify results
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result['file_path'], 'src/test/TestClass.java')
        self.assertEqual(result['package'], 'com.test')
        self.assertEqual(result['line'], '25')
        self.assertEqual(result['original_string'], '"测试字符串"')
        self.assertEqual(result['category'], 'Chinese')
    
    def test_statistics_tracking(self):
        """Test that statistics are tracked correctly."""
        # Initial state
        self.assertEqual(self.extractor.stats['total_strings'], 0)
        self.assertEqual(self.extractor.stats['chinese_strings'], 0)
        self.assertEqual(self.extractor.stats['english_strings'], 0)
        
        # Create test XML with mixed string types
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<problems>
  <problem>
    <file>file://$PROJECT_DIR$/Test1.java</file>
    <line>10</line>
    <package>com.test</package>
    <highlighted_element>"中文字符串"</highlighted_element>
  </problem>
  <problem>
    <file>file://$PROJECT_DIR$/Test2.java</file>
    <line>20</line>
    <package>com.test</package>
    <highlighted_element>"English string"</highlighted_element>
  </problem>
  <problem>
    <file>file://$PROJECT_DIR$/Test3.java</file>
    <line>30</line>
    <package>com.test</package>
    <highlighted_element>"Format: %s"</highlighted_element>
  </problem>
</problems>'''
        
        temp_xml = Path(self.temp_dir) / 'mixed_test.xml'
        with open(temp_xml, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        # Parse and check statistics
        self.extractor.parse_xml_file(str(temp_xml))
        
        self.assertEqual(self.extractor.stats['total_strings'], 3)
        self.assertEqual(self.extractor.stats['chinese_strings'], 1)
        self.assertEqual(self.extractor.stats['english_strings'], 1)  # Only "English string" counts as English
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestI18nExtractorIntegration(unittest.TestCase):
    """Integration tests using the sample XML file."""
    
    def test_sample_xml_processing(self):
        """Test processing the sample inspection XML file."""
        # Use the sample XML file that should exist
        sample_path = Path(__file__).parent / 'sample_inspection.xml'
        
        if not sample_path.exists():
            self.skipTest("Sample XML file not found")
        
        temp_dir = tempfile.mkdtemp()
        try:
            extractor = I18nExtractor(output_dir=temp_dir)
            results = extractor.process_xml_files([str(sample_path)], translate=False)
            
            # Should extract 5 strings as per the sample file
            self.assertEqual(len(results), 5)
            
            # Check that we have the expected categories
            categories = [item['category'] for item in results]
            self.assertIn('Chinese', categories)
            self.assertIn('English', categories)
            self.assertIn('Format', categories)
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()