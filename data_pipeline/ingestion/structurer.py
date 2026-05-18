import os
import sys
import re
import json
import logging
from typing import List, Dict, Any, Optional

# Add workspace to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.constants import nepali_to_int, int_to_nepali
from core.models import Act, Part, Chapter, Section, Subsection, Clause, SubClause
from ingestion.config import PROCESSED_TEXT_DIR, STRUCTURED_ACTS_DIR, INGESTION_LOG, ERROR_LOG

logger = logging.getLogger("structurer")

# Bracketed nepali numeral pattern: (१), (१०), etc.
SUBSECTION_PATTERN = re.compile(r'^\s*\(([०-९१-९]+)\)\s*(.*)$')
# Bracketed nepali letter pattern: (क) to (ह)
CLAUSE_PATTERN = re.compile(r'^\s*\(([क-ह])\)\s*(.*)$')

def clean_title(title: str) -> str:
    """Cleans section/part titles of ending colons and whitespace."""
    if not title:
        return ""
    title = title.strip()
    # Remove ending colons or punctuation commonly used in headers
    title = re.sub(r'[\sः\:\-\–]+$', '', title)
    return title.strip()

def parse_section_body(body_text: str) -> tuple:
    """
    Parses a section's raw body text into Subsections and direct Clauses.
    """
    subsections: List[Subsection] = []
    direct_clauses: List[Clause] = []
    
    if not body_text:
        return subsections, direct_clauses
        
    lines = [line.strip() for line in body_text.split('\n') if line.strip()]
    
    current_sub: Optional[Subsection] = None
    current_clause: Optional[Clause] = None
    
    for line in lines:
        # Check if it starts with a subsection identifier like "(१)"
        sub_match = SUBSECTION_PATTERN.match(line)
        if sub_match:
            sub_id = sub_match.group(1)
            sub_text = sub_match.group(2)
            
            current_sub = Subsection(identifier=f"({sub_id})", text=sub_text)
            subsections.append(current_sub)
            current_clause = None # Reset active clause context
            continue
            
        # Check if it starts with a clause identifier like "(क)"
        clause_match = CLAUSE_PATTERN.match(line)
        if clause_match:
            clause_id = clause_match.group(1)
            clause_text = clause_match.group(2)
            
            new_clause = Clause(identifier=f"({clause_id})", text=clause_text)
            if current_sub:
                current_sub.clauses.append(new_clause)
            else:
                direct_clauses.append(new_clause)
            current_clause = new_clause
            continue
            
        # Check if it is a sub-clause identifier like "(१)" under a clause
        # If we have an active clause, and we see a bracketed number, it is a sub-clause!
        if current_clause:
            sub_match_under_clause = SUBSECTION_PATTERN.match(line)
            if sub_match_under_clause:
                subclause_id = sub_match_under_clause.group(1)
                subclause_text = sub_match_under_clause.group(2)
                
                new_subclause = SubClause(identifier=f"({subclause_id})", text=subclause_text)
                current_clause.sub_clauses.append(new_subclause)
                continue
                
        # If it's none of the above, append it to the currently active element
        if current_clause:
            current_clause.text += " " + line
        elif current_sub:
            current_sub.text += " " + line
        else:
            # Fallback if text is found before any subsection/clause starts
            if subsections:
                subsections[-1].text += " " + line
            elif direct_clauses:
                direct_clauses[-1].text += " " + line
            else:
                # Direct clause text
                direct_clauses.append(Clause(identifier="", text=line))
                
    return subsections, direct_clauses

def structure_nepali_act(text: str, title: str, source_url: str, pdf_url: Optional[str] = None) -> Act:
    """
    Core structuring engine. Parses raw text into hierarchical parts, chapters, sections, and clauses.
    """
    logger.info(f"Structuring legal document: {title}")
    
    act = Act(title=title, nepali_title=title, source_url=source_url, pdf_url=pdf_url)
    
    # Split text into lines
    raw_lines = text.split('\n')
    
    # Pre-process lines: remove empty lines and page dividers
    lines = []
    for line in raw_lines:
        line = line.strip()
        if not line or line.startswith("--- PAGE"):
            continue
        lines.append(line)
        
    current_part: Optional[Part] = None
    current_chapter: Optional[Chapter] = None
    
    # We will buffer section lines before parsing them to handle multi-line sections easily
    section_buffers = [] # list of (section_id, section_title, section_body_lines)
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 1. Detect Part: e.g. "भाग–१" or "भाग १८"
        part_match = re.match(r'^भाग\s*[–\-]?\s*([०-९१-९]+)\s*$', line)
        if part_match:
            part_id = part_match.group(1)
            # Part title is typically on the next line
            part_title = ""
            if i + 1 < len(lines) and not re.match(r'^भाग\s*[–\-]?\s*([०-९१-९]+)\s*$', lines[i+1]) and not re.match(r'^\s*[०-९१-९]+\.\s+', lines[i+1]):
                i += 1
                part_title = clean_title(lines[i])
                
            current_part = Part(identifier=part_id, title=part_title)
            act.parts.append(current_part)
            current_chapter = None # Reset chapter context
            i += 1
            continue
            
        # 2. Detect Chapter: e.g. "परिच्छेद–१" or "अध्याय १"
        chapter_match = re.match(r'^(परिच्छेद|अध्याय)\s*[–\-]?\s*([०-९१-९]+)\s*$', line)
        if chapter_match:
            chapter_id = chapter_match.group(2)
            chapter_title = ""
            if i + 1 < len(lines) and not re.match(r'^\s*[०-९१-९]+\.\s+', lines[i+1]):
                i += 1
                chapter_title = clean_title(lines[i])
                
            current_chapter = Chapter(identifier=chapter_id, title=chapter_title)
            if current_part:
                current_part.chapters.append(current_chapter)
            else:
                act.chapters.append(current_chapter)
            i += 1
            continue
            
        # 3. Detect Schedule: e.g. "अनुसूची–१" or "अनुसूची १"
        schedule_match = re.match(r'^अनुसूची\s*[–\-]?\s*([०-९१-९]+)\s*$', line)
        if schedule_match:
            sch_id = schedule_match.group(1)
            sch_title = ""
            if i + 1 < len(lines) and not re.match(r'^अनुसूची\s*', lines[i+1]) and not re.match(r'^भाग\s*', lines[i+1]):
                i += 1
                sch_title = clean_title(lines[i])
                
            # Accumulate all subsequent lines for this schedule until next schedule or new part/chapter
            sch_lines = []
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if re.match(r'^अनुसूची\s*[–\-]?\s*([०-९१-९]+)\s*$', next_line) or \
                   re.match(r'^भाग\s*[–\-]?\s*([०-९१-९]+)\s*$', next_line):
                    break
                sch_lines.append(next_line)
                i += 1
                
            from core.models import Schedule
            new_schedule = Schedule(
                identifier=sch_id,
                title=sch_title,
                text="\n".join(sch_lines)
            )
            act.schedules.append(new_schedule)
            continue

        # 4. Detect Section start: e.g. "१. संविधान मूल कानूनः ..."
        section_match = re.match(r'^([०-९१-९]+)\.\s+(.*)$', line)
        if section_match:
            sec_id = section_match.group(1)
            rest = section_match.group(2)
            
            # Split section title and first text by colon
            sec_title = ""
            first_text = ""
            if "ः" in rest:
                parts = rest.split("ः", 1)
                sec_title = clean_title(parts[0])
                first_text = parts[1].strip()
            elif ":" in rest:
                parts = rest.split(":", 1)
                sec_title = clean_title(parts[0])
                first_text = parts[1].strip()
            else:
                # If no colon, check for bracketed text start
                paren_match = re.search(r'\s*(\(.*?\))', rest)
                if paren_match:
                    sec_title = clean_title(rest[:paren_match.start()])
                    first_text = rest[paren_match.start():].strip()
                else:
                    sec_title = clean_title(rest)
                    first_text = ""
                    
            # Gather subsequent lines belonging to this section until next Part, Chapter, or Section
            body_lines = []
            if first_text:
                body_lines.append(first_text)
                
            i += 1
            while i < len(lines):
                next_line = lines[i]
                if re.match(r'^भाग\s*[–\-]?\s*([०-९१-९]+)\s*$', next_line) or \
                   re.match(r'^(परिच्छेद|अध्याय)\s*[–\-]?\s*([०-९१-९]+)\s*$', next_line) or \
                   re.match(r'^अनुसूची\s*[–\-]?\s*([०-९१-९]+)\s*$', next_line) or \
                   re.match(r'^([०-९१-९]+)\.\s+', next_line):
                    break
                body_lines.append(next_line)
                i += 1
                
            body_text = "\n".join(body_lines)
            subsections, clauses = parse_section_body(body_text)
            
            # Create section
            section = Section(
                identifier=sec_id,
                title=sec_title,
                text=body_text if not subsections and not clauses else None,
                subsections=subsections,
                clauses=clauses
            )
            
            # Add to proper structural parent
            if current_chapter:
                current_chapter.sections.append(section)
            elif current_part:
                # If part has no chapters, sections go directly under part!
                # We can create a dummy chapter or add support directly. Let's add directly to Part if wanted,
                # but to conform with models.py, parts have chapters.
                # Let's create a dummy Chapter for Part if no chapter exists to maintain strict tree!
                if not current_part.chapters:
                    current_part.chapters.append(Chapter(identifier="", title=""))
                current_part.chapters[-1].sections.append(section)
            else:
                # Direct section of the Act
                act.sections.append(section)
                
            continue
            
        # Fallback increment to avoid infinite loop
        i += 1
        
    return act

def process_extracted_text_file(txt_path: str, title: str, source_url: str, pdf_url: Optional[str] = None) -> Optional[str]:
    """
    Loads clean text file, structures it, and saves structured hierarchical JSON output.
    """
    if not os.path.exists(txt_path):
        logger.error(f"Text file does not exist: {txt_path}")
        return None
        
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        act = structure_nepali_act(text, title, source_url, pdf_url)
        
        # Save output JSON
        output_filename = os.path.splitext(os.path.basename(txt_path))[0] + ".json"
        dest_path = os.path.join(STRUCTURED_ACTS_DIR, output_filename)
        
        with open(dest_path, "w", encoding="utf-8") as out_f:
            out_f.write(act.to_json())
            
        logger.info(f"Saved structured hierarchical JSON to {dest_path}")
        return dest_path
    except Exception as e:
        logger.error(f"Failed to structure text file {txt_path}: {e}")
        with open(ERROR_LOG, "a") as err_f:
            err_f.write(f"Failed structuring {txt_path}: {e}\n")
        return None

if __name__ == "__main__":
    # Test on processed constitution text
    txt_file = os.path.join(PROCESSED_TEXT_DIR, "नेपालको_संविधान.txt")
    if os.path.exists(txt_file):
        dest = process_extracted_text_file(
            txt_file,
            "नेपालको संविधान",
            "https://lawcommission.gov.np/category/1807/",
            "https://giwmscdnone.gov.np/media/pdf_upload/%E0%A4%A8%E0%A5%87%E0%A4%AA%E0%A4%BE%E0%A4%B2%E0%A4%95%E0%A5%8B%20%E0%A4%B8_%E0%A4%82%E0%A4%B5%E0%A4%BF%E0%A4%A7%E0%A4%BE%E0%A4%A8%20unicode%20%E0%A4%AD%E0%A4%BE%E0%A4%A6%E0%A5%8D%E0%A4%B0%20%E0%A5%A8%E0%A5%A6%E0%A5%AE%E0%A5%A7_mtbuyjt.pdf"
        )
        print(f"Structured file saved to: {dest}")
        
        # Check structured JSON properties
        if dest and os.path.exists(dest):
            with open(dest, "r", encoding="utf-8") as f:
                data = json.load(f)
            print("Act:", data["title"])
            print("Parts count:", len(data["parts"]))
            if data["parts"]:
                print("Part 1:", data["parts"][0]["identifier"], "-", data["parts"][0]["title"])
                if data["parts"][0]["chapters"] and data["parts"][0]["chapters"][0]["sections"]:
                    print("Section 1 in Part 1:", data["parts"][0]["chapters"][0]["sections"][0]["identifier"], "-", data["parts"][0]["chapters"][0]["sections"][0]["title"])
    else:
        print("Processed text file does not exist. Run extractor.py first.")
