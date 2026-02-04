import pdfplumber
import sys
import io

# Setup stdout to handle unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def debug_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        # Check pages 8-15 where content usually starts
        for i in range(7, min(20, len(pdf.pages))):
            print(f"--- PAGE {i+1} ---")
            text = pdf.pages[i].extract_text()
            if text:
                print(text)
            print("-" * 20)

if __name__ == "__main__":
    pdf_file = "@malikaeducationofficiall4000_essential_English_words_2_uzb.pdf"
    debug_pdf(pdf_file)
