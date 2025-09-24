# useful_py

A collection of useful Python utilities and tools.

## i18n_extractor.py

A comprehensive tool for extracting hardcoded strings from JetBrains IDEA inspection XML files and converting them for i18n (internationalization) purposes.

### Features

- **XML Parsing**: Parse IDEA inspection XML files containing hardcoded string violations
- **String Extraction**: Extract file paths, package names, line numbers, and hardcoded strings
- **Language Detection**: Automatically detect Chinese vs English/format strings
- **Batch Translation**: Translate Chinese strings to English with configurable batch processing
- **Progress Tracking**: Real-time progress bar for translation operations
- **Error Handling**: Robust error handling with fallback translation services
- **Multiple Output Formats**: Export results to both Markdown and Excel formats
- **Incremental Progress**: Save translation progress after each batch
- **Comprehensive Logging**: Detailed logging of all operations

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Ethan8996/useful_py.git
cd useful_py
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Usage

#### Command Line Interface

Basic usage:
```bash
python i18n_extractor.py inspection.xml
```

Advanced usage with options:
```bash
python i18n_extractor.py file1.xml file2.xml --batch-size 5 --delay 2.0 --output-dir ./results
```

Skip translation (extract only):
```bash
python i18n_extractor.py inspection.xml --no-translate
```

#### Python API

```python
from i18n_extractor import I18nExtractor

# Create extractor with custom settings
extractor = I18nExtractor(
    batch_size=10,
    translation_delay=1.0,
    output_dir="output"
)

# Process XML files
extractor.run(
    xml_paths=["inspection1.xml", "inspection2.xml"],
    translate=True,
    markdown_output="strings.md",
    excel_output="strings.xlsx"
)
```

#### Demo

Run the included demo to see the tool in action:
```bash
python demo.py
```

### Command Line Arguments

- `xml_files`: One or more XML inspection files to process (required)
- `--no-translate`: Skip translation of Chinese strings
- `--batch-size`: Number of strings to translate per batch (default: 10)
- `--delay`: Delay between translation batches in seconds (default: 1.0)
- `--output-dir`: Output directory for results (default: output)
- `--markdown-output`: Markdown output filename (default: hardcoded_strings.md)
- `--excel-output`: Excel output filename (default: hardcoded_strings.xlsx)

### Output Files

The tool generates several output files:

1. **Markdown Report** (`hardcoded_strings.md`):
   - Statistics summary
   - Table of all extracted strings with translations

2. **Excel Report** (`hardcoded_strings.xlsx`):
   - "Hardcoded Strings" sheet: All extracted data
   - "Statistics" sheet: Summary statistics
   - "Chinese Strings" sheet: Chinese strings only for review

3. **Log File** (`i18n_extractor.log`):
   - Detailed processing logs
   - Translation attempts and results
   - Error messages and warnings

4. **Progress Files** (`translation_progress_*.json`):
   - Incremental progress saves after each batch
   - Useful for resuming interrupted translations

### XML Format

The tool expects IDEA inspection XML files with the following structure:

```xml
<problems>
  <problem>
    <file>file://$PROJECT_DIR$/src/main/java/package/Class.java</file>
    <line>55</line>
    <module>module-name</module>
    <package>com.example.package</package>
    <problem_class id="HardCodedStringLiteral" severity="WARNING">Hardcoded strings</problem_class>
    <description>Hardcoded string literal: "并发任务异常："</description>
    <highlighted_element>"并发任务异常："</highlighted_element>
    <language>JAVA</language>
  </problem>
</problems>
```

### Translation Services

The tool uses multiple translation services with automatic fallback:
1. Google Translate (primary)
2. Bing Translator (fallback)
3. Baidu Translate (fallback)

Translation failures are logged and marked in the output for manual review.

### String Categorization

Strings are automatically categorized as:
- **Chinese**: Contains Chinese characters (CJK Unified Ideographs)
- **English**: Regular text without Chinese characters
- **Format**: Contains format specifiers (%s, %d, {}, etc.)

### Error Handling

The tool includes comprehensive error handling:
- Invalid XML files are skipped with logging
- Translation failures don't stop the entire process
- Network issues are handled with service fallbacks
- Progress is saved incrementally to prevent data loss

### Dependencies

- `lxml>=4.9.0`: XML parsing
- `pandas>=1.5.0`: Data manipulation and Excel export
- `openpyxl>=3.1.0`: Excel file handling
- `tqdm>=4.64.0`: Progress bars
- `translators>=5.6.0`: Translation services
- `requests>=2.28.0`: HTTP requests

### License

This project is open source and available under the MIT License.
