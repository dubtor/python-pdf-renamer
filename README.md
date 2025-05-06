# PDF Document Renamer

A Python script that automatically renames PDF documents based on their content using AI. It extracts the date and content description from scanned documents and renames them accordingly.

Note: currently exports German language titles. Edit in `renamer.py` for other languages

## How it Works

1. Each PDF is converted to an image using pdf2image
2. The first page of the document is analyzed using OpenAI's o4-mini model
3. The AI model extracts the date and content description directly from the image (no OCR)
4. Files are renamed using the extracted information

## Requirements

- Python 3.6+
- Poppler (for PDF processing)
- OpenAI API key

## Installation

1. Install Poppler:
   ```bash
   # macOS
   brew install poppler
   
   # Ubuntu/Debian
   sudo apt-get install poppler-utils
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project directory:
   ```bash
   # Create .env file
   echo "OPENAI_API_KEY=your-api-key-here" > .env
   ```
   
   Replace `your-api-key-here` with your actual OpenAI API key.

## Usage

```bash
python renamer.py <folder_with_pdfs>
```

The script will:
- Process all PDFs in the specified folder
- Create a "renamed" subfolder
- Copy renamed PDFs to the subfolder
- Use format: "YYYY-MM-DD Description.pdf"

If date or content cannot be determined, it will use "XXXX-XX-XX" and "Unknown" respectively. 