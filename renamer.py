import os
import sys
from openai import OpenAI
from pdf2image import convert_from_path
import base64
import re
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variable
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("Error: OPENAI_API_KEY environment variable is not set")
    print("Please create a .env file with your OpenAI API key")
    sys.exit(1)

client = OpenAI(api_key=api_key)

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_info_from_image(image_path):
    prompt = """
    Das folgende Bild ist ein eingescanntes offizielles Schreiben (z.B. Rechnung, Steuerbescheid, Behördenbrief).
    Bitte extrahiere:
    1. Das Datum des Dokuments im Format YYYY-MM-DD
    2. Eine kurze deutsche Inhaltsbeschreibung (max. 8 Wörter), z.B. "Bescheid zur Gewerbesteuer 2019", "Apple Care Rechnung", "Büromaterialien Rechnung". Sofern ein Zeitraum angegeben ist, fügen diesen an, z.B. "1&1 Sammelrechnung November 2024"

    Gib die Antwort bitte im Format:
    DATE: YYYY-MM-DD
    CONTENT: <Beschreibung>
    """

    try:
        image_data = image_to_base64(image_path)

        response = client.chat.completions.create(
            model="o4-mini",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_data}"
                        }
                    }
                ]
            }]
        )

        result = response.choices[0].message.content
        date_match = re.search(r"DATE:\s*(\d{4}-\d{2}-\d{2})", result)
        content_match = re.search(r"CONTENT:\s*(.+)", result)

        date = date_match.group(1) if date_match else "XXXX-XX-XX"
        content = content_match.group(1).strip() if content_match else "Unknown"
        
        return date, content
    except Exception as e:
        print(f"Warning: Error during AI extraction: {e}")
        return "XXXX-XX-XX", "Unknown"

def sanitize_filename(text):
    # Replace invalid filename characters with underscores
    # This includes: \ / : * ? " < > |
    # Also replace any control characters
    sanitized = re.sub(r'[\\/:"*?<>|\x00-\x1f]', '_', text)
    # Replace multiple consecutive underscores with a single one
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores and spaces
    sanitized = sanitized.strip('_ ')
    # If the result is empty after sanitization, return "Unknown"
    return sanitized if sanitized else "Unknown"

def process_pdfs(folder):
    renamed_folder = os.path.join(folder, "renamed")
    os.makedirs(renamed_folder, exist_ok=True)

    for filename in os.listdir(folder):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(folder, filename)
            print(f"Processing {filename}")
            try:
                images = convert_from_path(pdf_path)
                temp_image = "temp_page.png"
                images[0].save(temp_image, "PNG")  # assume first page is enough
                date, content = extract_info_from_image(temp_image)
                os.remove(temp_image)

                safe_content = sanitize_filename(content)
                new_filename = f"{date} {safe_content}.pdf"
                new_path = os.path.join(renamed_folder, new_filename)

                # Handle duplicate filenames
                counter = 1
                while os.path.exists(new_path):
                    new_filename = f"{date} {safe_content}_{counter}.pdf"
                    new_path = os.path.join(renamed_folder, new_filename)
                    counter += 1

                shutil.copy2(pdf_path, new_path)  # copy original to renamed folder
                print(f"Copied as: {new_filename}")

            except Exception as e:
                print(f"Error processing {filename}: {e}")
                # Create a fallback filename using the original name
                safe_original = sanitize_filename(os.path.splitext(filename)[0])
                fallback_filename = f"XXXX-XX-XX {safe_original}.pdf"
                fallback_path = os.path.join(renamed_folder, fallback_filename)
                
                # Handle duplicate fallback filenames
                counter = 1
                while os.path.exists(fallback_path):
                    fallback_filename = f"XXXX-XX-XX {safe_original}_{counter}.pdf"
                    fallback_path = os.path.join(renamed_folder, fallback_filename)
                    counter += 1
                
                try:
                    shutil.copy2(pdf_path, fallback_path)
                    print(f"Copied with fallback name: {fallback_filename}")
                except Exception as copy_error:
                    print(f"Failed to copy {filename} even with fallback name: {copy_error}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <folder_with_pdfs>")
        sys.exit(1)

    folder_path = sys.argv[1]
    if not os.path.isdir(folder_path):
        print(f"Error: {folder_path} is not a valid directory")
        sys.exit(1)

    process_pdfs(folder_path)
