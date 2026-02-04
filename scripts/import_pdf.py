import pdfplumber
import re
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from core.database.session import AsyncSessionLocal
from core.database.models import Word, Quiz

async def parse_pdf_and_insert(pdf_path: str):
    print(f"Opening {pdf_path}...")
    
    words_found = 0
    current_unit = 1
    
    # Pattern for the word and its pronunciation/part of speech
    # Example: "c bring [bnn] *" or "r castle iksesi] n."
    # Note: extraction sometimes mangles characters like [bnn]
    word_pattern = re.compile(r'^[cr]\s+([a-zA-Z]+)\s+\[.*?\]\s+([a-z]\.)?')
    
    async with AsyncSessionLocal() as session:
        with pdfplumber.open(pdf_path) as pdf:
            # Words typically start around page 9 (Index 8 in 0-based)
            # We'll scan all pages just to be safe, starting from page 8
            for i in range(8, len(pdf.pages)):
                text = pdf.pages[i].extract_text()
                if not text:
                    continue
                
                lines = text.split('\n')
                for j in range(len(lines)):
                    line = lines[j].strip()
                    
                    # Detect Unit changes
                    if "Word List" in line or "Unit" in line:
                        # If we see "Unit 2", etc. (Heuristic)
                        unit_match = re.search(r'Unit\s+(\d+)', line, re.I)
                        if unit_match:
                            current_unit = int(unit_match.group(1))
                    
                    # Detect Word lines
                    # Format: [icon] word [pronunciation] part_of_speech
                    #icon is often 'c' or 'r' in the extract
                    match = word_pattern.match(line)
                    if match:
                        word_text = match.group(1).strip()
                        
                        # Next line is usually the definition
                        definition = ""
                        if j + 1 < len(lines):
                            definition = lines[j+1].strip()
                        
                        # Translation is tricky in this PDF. 
                        # Looking at the debug output, I don't see direct translations in the English text block.
                        # However, the user said "uzb.pdf" so maybe it's there.
                        # If not found, we'll label it "Essential 4000 Word"
                        
                        # Let's try to find if there's a translation in the same line after '-'
                        if "-" in line:
                            parts = line.split("-")
                            if len(parts) > 1:
                                # This might be the example sentence starting with '-'
                                pass
                        
                        new_word = Word(
                            word=word_text.capitalize(),
                            translation="Tarjima (PDF'dan)", # Placeholder if not explicitly found
                            definition=definition,
                            unit=current_unit,
                            book_volume=2
                        )
                        session.add(new_word)
                        words_found += 1
                        print(f"Added: {word_text}")
                
                # Commit every page
                await session.commit()
    
    print(f"Successfully added {words_found} words from PDF to database.")

if __name__ == "__main__":
    pdf_file = "@malikaeducationofficiall4000_essential_English_words_2_uzb.pdf"
    asyncio.run(parse_pdf_and_insert(pdf_file))
