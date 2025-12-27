import PyPDF2
import os
import sys

files = [
    "HIPAA-Compliant Encrypted Medical Chatbot.pdf",
    "Hackathon Sprint Plan.pdf"
]

output_file = "pdf_content.txt"

with open(output_file, 'w', encoding='utf-8') as outfile:
    for filename in files:
        outfile.write(f"--- START OF {filename} ---\n")
        try:
            if not os.path.exists(filename):
                 outfile.write(f"File not found: {filename}\n")
                 continue
                 
            with open(filename, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                num_pages = len(reader.pages)
                outfile.write(f"Total pages: {num_pages}\n")
                # Read all pages since we are writing to file and view_file can handle it (up to limit)
                # But actually view_file has an 800 line limit per view. I should probably still be concise or just read the first few.
                # The user wants me to "understand what i am going to build".
                # I'll read first 10 pages.
                text = ""
                for i in range(min(10, num_pages)):
                    text += reader.pages[i].extract_text() + "\n"
                outfile.write(text + "\n")
        except Exception as e:
            outfile.write(f"Error reading {filename}: {e}\n")
        outfile.write(f"--- END OF {filename} ---\n")
