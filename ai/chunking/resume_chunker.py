import re


class ResumeChunker:

    @staticmethod
    def chunk_resume(text: str):

        if not text:
            return []

        # Normalize whitespace while preserving line breaks
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Common resume section headers
        section_keywords = [
            "experience", "work history", "employment",
            "education", "academic",
            "skills", "technical skills", "technologies", "expertise",
            "projects", "personal projects",
            "certifications", "awards", "achievements",
            "summary", "objective", "profile",
            "contact", "information", "links"
        ]

        # Improved regex for section headers: 
        # Since some PDFs might extract text without newlines, we look for:
        # 1. Keywords in ALL CAPS (common for headers)
        # 2. Keywords at the start of the text
        # 3. Keywords preceded by a newline (if present)
        
        pattern = r'(?:^|\s)(' + '|'.join(re.escape(k.upper()) for k in section_keywords) + r')(?:\s|$)'
        section_regex = re.compile(pattern)

        chunks = []
        current_section = "general"
        last_idx = 0

        # Find all section matches
        for match in section_regex.finditer(text):
            start, end = match.span()
            
            # Extract the text before this section
            prev_text = text[last_idx:start].strip()
            if prev_text:
                chunks.append({
                    "section": current_section,
                    "text": prev_text
                })
            
            current_section = match.group(0).strip().lower()
            last_idx = end

        # Add the remaining text
        remaining_text = text[last_idx:].strip()
        if remaining_text:
            chunks.append({
                "section": current_section,
                "text": remaining_text
            })

        # Final sanity check: if chunks are too large or we only have one chunk,
        # perform sub-chunking based on length to stay within embedding limits
        MAX_CHUNK_CHARS = 1500
        final_chunks = []

        for chunk in chunks:
            if len(chunk["text"]) > MAX_CHUNK_CHARS:
                # Split by double newline first, then single
                paragraphs = re.split(r'\n\n', chunk["text"])
                current_sub_text = ""
                
                for para in paragraphs:
                    if len(current_sub_text) + len(para) < MAX_CHUNK_CHARS:
                        current_sub_text += (para + "\n\n")
                    else:
                        if current_sub_text:
                            final_chunks.append({
                                "section": chunk["section"],
                                "text": current_sub_text.strip()
                            })
                        current_sub_text = para + "\n\n"
                
                if current_sub_text:
                    final_chunks.append({
                        "section": chunk["section"],
                        "text": current_sub_text.strip()
                    })
            else:
                final_chunks.append(chunk)

        # Fallback if no chunks were created (shouldn't happen with the logic above)
        if not final_chunks and text:
            final_chunks.append({
                "section": "general",
                "text": text.strip()
            })

        return final_chunks