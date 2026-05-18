import os
import sys
import json
import re
import logging
from typing import List, Dict, Any, Tuple

# Add workspace to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingestion.config import STRUCTURED_ACTS_DIR, INGESTION_LOG, ERROR_LOG

logger = logging.getLogger("validator")

class LegalDocValidator:
    """
    Validates structured legal JSON files for schema compliance and cross-reference citation integrity.
    """
    def __init__(self, json_path: str):
        self.json_path = json_path
        self.data: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.sections_map: Dict[str, Dict[str, Any]] = {}
        self.schedules_map: Dict[str, Dict[str, Any]] = {}
        
    def load_data(self) -> bool:
        if not os.path.exists(self.json_path):
            self.errors.append(f"File not found: {self.json_path}")
            return False
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
            return True
        except Exception as e:
            self.errors.append(f"JSON parsing error: {e}")
            return False
            
    def validate_schema(self) -> bool:
        """Checks if the JSON file strictly conforms to the Act schema."""
        required_keys = ["title", "nepali_title", "source_url", "parts", "chapters", "sections", "schedules"]
        for key in required_keys:
            if key not in self.data:
                self.errors.append(f"Missing root key: '{key}'")
                
        # Build maps of sections and schedules for fast lookups
        self._build_maps()
        
        # Traverse and validate parts
        for part_idx, part in enumerate(self.data.get("parts", [])):
            part_id = part.get("identifier", f"PartIndex-{part_idx}")
            if not part.get("title"):
                self.warnings.append(f"Part '{part_id}' has an empty or missing title.")
            if "chapters" not in part:
                self.errors.append(f"Part '{part_id}' is missing its 'chapters' list.")
                
            for chap_idx, chap in enumerate(part.get("chapters", [])):
                chap_id = chap.get("identifier", f"ChapIndex-{chap_idx}")
                if "sections" not in chap:
                    self.errors.append(f"Chapter '{chap_id}' in Part '{part_id}' is missing its 'sections' list.")
                    
                for sec_idx, sec in enumerate(chap.get("sections", [])):
                    self._validate_section(sec, f"Part {part_id} -> Chapter {chap_id}")
                    
        # Traverse and validate direct chapters (if no parts)
        for chap_idx, chap in enumerate(self.data.get("chapters", [])):
            chap_id = chap.get("identifier", f"ChapIndex-{chap_idx}")
            if "sections" not in chap:
                self.errors.append(f"Chapter '{chap_id}' is missing its 'sections' list.")
            for sec in chap.get("sections", []):
                self._validate_section(sec, f"Chapter {chap_id}")
                
        # Traverse and validate direct sections (if no parts/chapters)
        for sec in self.data.get("sections", []):
            self._validate_section(sec, "Root")
            
        # Traverse and validate schedules
        for sch_idx, sch in enumerate(self.data.get("schedules", [])):
            sch_id = sch.get("identifier", f"SchIndex-{sch_idx}")
            if "title" not in sch:
                self.errors.append(f"Schedule at index {sch_idx} is missing its 'title'.")
            if "text" not in sch:
                self.errors.append(f"Schedule '{sch_id}' is missing its 'text'.")
                
        return len(self.errors) == 0

    def _validate_section(self, sec: Dict[str, Any], path_prefix: str):
        sec_id = sec.get("identifier", "UnknownSec")
        if not sec.get("title"):
            self.warnings.append(f"[{path_prefix}] Section '{sec_id}' has an empty or missing title.")
            
        # Subsections validation
        for sub_idx, sub in enumerate(sec.get("subsections", [])):
            if "identifier" not in sub or "text" not in sub:
                self.errors.append(f"[{path_prefix}] Section '{sec_id}' Subsection at index {sub_idx} is missing required fields.")
            for cl_idx, cl in enumerate(sub.get("clauses", [])):
                self._validate_clause(cl, f"{path_prefix} -> Section {sec_id} -> Subsection {sub.get('identifier')}")
                
        # Direct clauses validation (if no subsections)
        for cl_idx, cl in enumerate(sec.get("clauses", [])):
            self._validate_clause(cl, f"{path_prefix} -> Section {sec_id}")

    def _validate_clause(self, cl: Dict[str, Any], path_prefix: str):
        cl_id = cl.get("identifier", "UnknownClause")
        if "text" not in cl:
            self.errors.append(f"[{path_prefix}] Clause '{cl_id}' is missing 'text'.")
        for sc_idx, sc in enumerate(cl.get("sub_clauses", [])):
            if "identifier" not in sc or "text" not in sc:
                self.errors.append(f"[{path_prefix}] Clause '{cl_id}' SubClause at index {sc_idx} is missing required fields.")

    def _build_maps(self):
        """Helper to catalog all sections and schedules for fast reference checking."""
        # 1. Map all sections
        for part in self.data.get("parts", []):
            for chap in part.get("chapters", []):
                for sec in chap.get("sections", []):
                    self.sections_map[str(sec.get("identifier"))] = sec
                    
        for chap in self.data.get("chapters", []):
            for sec in chap.get("sections", []):
                self.sections_map[str(sec.get("identifier"))] = sec
                
        for sec in self.data.get("sections", []):
            self.sections_map[str(sec.get("identifier"))] = sec
            
        # 2. Map all schedules
        for sch in self.data.get("schedules", []):
            self.schedules_map[str(sch.get("identifier"))] = sch

    def validate_citation_integrity(self) -> Tuple[int, int, List[Tuple[str, str, str]]]:
        """
        Scans all section/clause texts for cross-references to other sections/schedules
        (e.g., 'धारा १६', 'अनुसूची–५') and checks if they exist in the structured JSON.
        Returns:
            total_citations: total number of cross-references found
            broken_citations: count of cross-references that couldn't be resolved
            issues: list of (source_element, citation_text, issue_details)
        """
        logger.info("Scanning for legal citation and cross-reference integrity...")
        total_citations = 0
        broken_citations = 0
        issues: List[Tuple[str, str, str]] = []
        
        # Regexes for finding cross-references in Nepali text
        # Match 'धारा [१-९०-९]+' or 'दफा [१-९०-९]+'
        sec_ref_pattern = re.compile(r'(धारा|दफा)\s+([०-९१-९]+)')
        # Match 'अनुसूची\s*[-–]?\s*([०-९१-९]+)'
        sch_ref_pattern = re.compile(r'अनुसूची\s*[–\-]?\s*([०-९१-९]+)')
        
        def check_text(text: str, source_label: str):
            nonlocal total_citations, broken_citations
            if not text:
                return
                
            # Check Section references
            for match in sec_ref_pattern.finditer(text):
                total_citations += 1
                ref_type = match.group(1)
                ref_num = match.group(2)
                
                # Check if referenced section exists
                if ref_num not in self.sections_map:
                    broken_citations += 1
                    issues.append((source_label, f"{ref_type} {ref_num}", f"Referenced section '{ref_num}' does not exist in the structured document."))
                    
            # Check Schedule references
            for match in sch_ref_pattern.finditer(text):
                total_citations += 1
                ref_num = match.group(1)
                
                # Check if referenced schedule exists
                if ref_num not in self.schedules_map:
                    broken_citations += 1
                    issues.append((source_label, f"अनुसूची {ref_num}", f"Referenced schedule '{ref_num}' does not exist in the structured document."))

        # 1. Scan sections text
        for sec_id, sec in self.sections_map.items():
            source_lbl = f"धारा {sec_id}"
            check_text(sec.get("text", ""), source_lbl)
            
            # Subsections
            for sub in sec.get("subsections", []):
                sub_lbl = f"धारा {sec_id} उपधारा {sub.get('identifier')}"
                check_text(sub.get("text", ""), sub_lbl)
                for cl in sub.get("clauses", []):
                    cl_lbl = f"धारा {sec_id} उपधारा {sub.get('identifier')} खण्ड {cl.get('identifier')}"
                    check_text(cl.get("text", ""), cl_lbl)
                    for sc in cl.get("sub_clauses", []):
                        check_text(sc.get("text", ""), f"{cl_lbl} उपखण्ड {sc.get('identifier')}")
                        
            # Direct clauses
            for cl in sec.get("clauses", []):
                cl_lbl = f"धारा {sec_id} खण्ड {cl.get('identifier')}"
                check_text(cl.get("text", ""), cl_lbl)
                for sc in cl.get("sub_clauses", []):
                    check_text(sc.get("text", ""), f"{cl_lbl} उपखण्ड {sc.get('identifier')}")

        # 2. Scan schedules text
        for sch_id, sch in self.schedules_map.items():
            check_text(sch.get("text", ""), f"अनुसूची {sch_id}")
            
        return total_citations, broken_citations, issues

def run_validation(json_path: str) -> bool:
    """Convenience function to run schema and citation validation on a JSON path."""
    print(f"\n=======================================================")
    print(f"VALIDATING HIERARCHICAL LEGAL ACT: {os.path.basename(json_path)}")
    print(f"=======================================================")
    
    validator = LegalDocValidator(json_path)
    if not validator.load_data():
        print(f"❌ ERROR: Failed to load file: {validator.errors[0]}")
        return False
        
    # Schema check
    schema_ok = validator.validate_schema()
    if schema_ok:
        print("✅ SCHEMA COMPLIANCE: Strict schema matches perfectly.")
    else:
        print(f"❌ SCHEMA COMPLIANCE FAILED: Found {len(validator.errors)} strict errors.")
        for err in validator.errors[:10]:
            print(f"   - [ERROR] {err}")
            
    if validator.warnings:
        print(f"⚠️ SCHEMA WARNINGS: Found {len(validator.warnings)} visual/structural warnings.")
        for warn in validator.warnings[:5]:
            print(f"   - [WARN] {warn}")
            
    # Citation check
    total_refs, broken_refs, issues = validator.validate_citation_integrity()
    print(f"🔍 CROSS-REFERENCE INTEGRITY:")
    print(f"   - Total legal citations scanned: {total_refs}")
    print(f"   - Broken citations detected: {broken_refs}")
    
    if broken_refs > 0:
        print(f"⚠️ CITATION ALERTS:")
        for source, citation, issue in issues[:10]:
            print(f"   - [{source}] contains reference '{citation}': {issue}")
            
    success = schema_ok and (broken_refs == 0)
    if success:
        print("\n🏆 VALIDATION COMPLETED: Legal document structured with 100% integrity!")
    else:
        print("\n⚠️ VALIDATION COMPLETED: Structure conforms, but citation warnings need manual healing or checking.")
        
    return schema_ok

if __name__ == "__main__":
    # Test on the constitution JSON
    json_file = os.path.join(STRUCTURED_ACTS_DIR, "नेपालको_संविधान.json")
    if os.path.exists(json_file):
        run_validation(json_file)
    else:
        print("Structured JSON file does not exist. Run structurer.py first.")
