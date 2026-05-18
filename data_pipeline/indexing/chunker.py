import os
import sys
import json
import hashlib
from typing import List, Dict, Any, Optional

# Add workspace to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

class LegalChunker:
    """
    Transforms a hierarchical Act JSON structure into semantic, metadata-rich, 
    RAG-ready text chunks.
    """
    def __init__(self, act_data: Dict[str, Any]):
        self.act_data = act_data
        self.act_title = act_data.get("title", "अज्ञात ऐन")
        self.nepali_title = act_data.get("nepali_title", self.act_title)
        
    def generate_chunks(self) -> List[Dict[str, Any]]:
        """
        Traverses the Act tree and produces flat chunks for Qdrant/FAISS indexing.
        """
        chunks = []
        
        # 1. Process Parts
        for part in self.act_data.get("parts", []):
            part_id = part.get("identifier", "")
            part_title = part.get("title", "")
            
            for chap in part.get("chapters", []):
                chap_id = chap.get("identifier", "")
                chap_title = chap.get("title", "")
                
                for sec in chap.get("sections", []):
                    chunks.extend(self._process_section(sec, part_id, part_title, chap_id, chap_title))
                    
        # 2. Process Direct Chapters (if any)
        for chap in self.act_data.get("chapters", []):
            chap_id = chap.get("identifier", "")
            chap_title = chap.get("title", "")
            
            for sec in chap.get("sections", []):
                chunks.extend(self._process_section(sec, "", "", chap_id, chap_title))
                
        # 3. Process Direct Sections (if any)
        for sec in self.act_data.get("sections", []):
            chunks.extend(self._process_section(sec, "", "", "", ""))
            
        # 4. Process Schedules
        for sch in self.act_data.get("schedules", []):
            chunks.append(self._process_schedule(sch))
            
        return chunks

    def _process_section(
        self, 
        sec: Dict[str, Any], 
        part_id: str, 
        part_title: str, 
        chap_id: str, 
        chap_title: str
    ) -> List[Dict[str, Any]]:
        sec_chunks = []
        sec_id = sec.get("identifier", "")
        sec_title = sec.get("title", "")
        sec_text = sec.get("text", "")
        
        # Determine basic section citation prefix
        sec_ref = f"धारा {sec_id}" if "संविधान" in self.act_title else f"दफा {sec_id}"
        
        # Base metadata dictionary
        base_meta = {
            "act_title": self.act_title,
            "nepali_title": self.nepali_title,
            "part_id": part_id,
            "part_title": part_title,
            "chapter_id": chap_id,
            "chapter_title": chap_title,
            "section_id": sec_id,
            "section_title": sec_title
        }

        # Case A: Section has direct text and no subsections or clauses
        subsections = sec.get("subsections", [])
        clauses = sec.get("clauses", [])
        
        if sec_text and not subsections and not clauses:
            # Entire section is a single chunk
            citation = f"{self.nepali_title}, {sec_ref} ({sec_title})"
            chunk_text = f"{self.nepali_title}, {sec_ref}. {sec_title} : {sec_text}"
            
            meta = base_meta.copy()
            meta.update({
                "citation": citation,
                "type": "section"
            })
            
            sec_chunks.append(self._create_chunk(chunk_text, sec_text, meta))
            return sec_chunks
            
        # Case B: Section has direct clauses (and no subsections)
        if clauses and not subsections:
            # We index the main section text first if present
            if sec_text:
                citation = f"{self.nepali_title}, {sec_ref} ({sec_title})"
                chunk_text = f"{self.nepali_title}, {sec_ref}. {sec_title} : {sec_text}"
                meta = base_meta.copy()
                meta.update({"citation": citation, "type": "section"})
                sec_chunks.append(self._create_chunk(chunk_text, sec_text, meta))
                
            for cl in clauses:
                cl_id = cl.get("identifier", "")
                cl_text = cl.get("text", "")
                sub_cl = cl.get("sub_clauses", [])
                
                citation = f"{self.nepali_title}, {sec_ref} को खण्ड {cl_id} ({sec_title})"
                chunk_text = f"{self.nepali_title}, {sec_ref}. {sec_title}, खण्ड {cl_id} : {cl_text}"
                
                meta = base_meta.copy()
                meta.update({
                    "clause_id": cl_id,
                    "citation": citation,
                    "type": "clause"
                })
                
                sec_chunks.append(self._create_chunk(chunk_text, cl_text, meta))
                
                # Check for sub-clauses
                for sc in sub_cl:
                    sc_id = sc.get("identifier", "")
                    sc_text = sc.get("text", "")
                    sc_citation = f"{self.nepali_title}, {sec_ref} को खण्ड {cl_id} को उपखण्ड {sc_id}"
                    sc_chunk_text = f"{self.nepali_title}, {sec_ref}. {sec_title}, खण्ड {cl_id}, उपखण्ड {sc_id} : {sc_text}"
                    
                    sc_meta = meta.copy()
                    sc_meta.update({
                        "sub_clause_id": sc_id,
                        "citation": sc_citation,
                        "type": "sub_clause"
                    })
                    sec_chunks.append(self._create_chunk(sc_chunk_text, sc_text, sc_meta))
            return sec_chunks

        # Case C: Section has subsections
        for sub in subsections:
            sub_id = sub.get("identifier", "")
            sub_text = sub.get("text", "")
            sub_clauses = sub.get("clauses", [])
            
            # Subsections represent a semantic unit
            sub_citation = f"{self.nepali_title}, {sec_ref} को उपधारा {sub_id} ({sec_title})"
            sub_chunk_text = f"{self.nepali_title}, {sec_ref}. {sec_title}, उपधारा {sub_id} : {sub_text}"
            
            meta = base_meta.copy()
            meta.update({
                "subsection_id": sub_id,
                "citation": sub_citation,
                "type": "subsection"
            })
            
            # If subsection has no clauses, index it as is
            if not sub_clauses:
                sec_chunks.append(self._create_chunk(sub_chunk_text, sub_text, meta))
            else:
                # If subsection has clauses, index each clause with full parent context
                for cl in sub_clauses:
                    cl_id = cl.get("identifier", "")
                    cl_text = cl.get("text", "")
                    sub_cl = cl.get("sub_clauses", [])
                    
                    cl_citation = f"{self.nepali_title}, {sec_ref} को उपधारा {sub_id} को खण्ड {cl_id} ({sec_title})"
                    cl_chunk_text = f"{self.nepali_title}, {sec_ref}. {sec_title}, उपधारा {sub_id}, खण्ड {cl_id} : {cl_text}"
                    
                    cl_meta = meta.copy()
                    cl_meta.update({
                        "clause_id": cl_id,
                        "citation": cl_citation,
                        "type": "clause"
                    })
                    sec_chunks.append(self._create_chunk(cl_chunk_text, cl_text, cl_meta))
                    
                    # Sub-clauses under this clause
                    for sc in sub_cl:
                        sc_id = sc.get("identifier", "")
                        sc_text = sc.get("text", "")
                        sc_citation = f"{self.nepali_title}, {sec_ref} को उपधारा {sub_id} को खण्ड {cl_id} को उपखण्ड {sc_id}"
                        sc_chunk_text = f"{self.nepali_title}, {sec_ref}. {sec_title}, उपधारा {sub_id}, खण्ड {cl_id}, उपखण्ड {sc_id} : {sc_text}"
                        
                        sc_meta = cl_meta.copy()
                        sc_meta.update({
                            "sub_clause_id": sc_id,
                            "citation": sc_citation,
                            "type": "sub_clause"
                        })
                        sec_chunks.append(self._create_chunk(sc_chunk_text, sc_text, sc_meta))
                        
        return sec_chunks

    def _process_schedule(self, sch: Dict[str, Any]) -> Dict[str, Any]:
        sch_id = sch.get("identifier", "")
        sch_title = sch.get("title", "")
        sch_text = sch.get("text", "")
        
        citation = f"{self.nepali_title}, अनुसूची {sch_id} ({sch_title})"
        chunk_text = f"{self.nepali_title}, अनुसूची {sch_id}. {sch_title} : {sch_text}"
        
        meta = {
            "act_title": self.act_title,
            "nepali_title": self.nepali_title,
            "schedule_id": sch_id,
            "schedule_title": sch_title,
            "citation": citation,
            "type": "schedule"
        }
        
        return self._create_chunk(chunk_text, sch_text, meta)

    def _create_chunk(self, text: str, raw_text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        # Generate a unique stable ID based on the text hash
        chunk_id = hashlib.md5(text.encode("utf-8")).hexdigest()
        return {
            "id": chunk_id,
            "text": text,
            "raw_text": raw_text,
            "metadata": metadata
        }

def chunk_file(json_path: str) -> List[Dict[str, Any]]:
    """Loads a structured JSON file and generates RAG chunks."""
    with open(json_path, "r", encoding="utf-8") as f:
        act_data = json.load(f)
    chunker = LegalChunker(act_data)
    return chunker.generate_chunks()

if __name__ == "__main__":
    # Test chunking on Constitution structured JSON
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from data_pipeline.ingestion.config import STRUCTURED_ACTS_DIR
    
    test_json = os.path.join(STRUCTURED_ACTS_DIR, "नेपालको_संविधान.json")
    if os.path.exists(test_json):
        chunks = chunk_file(test_json)
        print(f"Generated {len(chunks)} chunks successfully.")
        if chunks:
            print("First chunk sample:")
            print(json.dumps(chunks[0], indent=2, ensure_ascii=False))
            print("\nMiddle chunk sample (containing clause):")
            # Let's find a chunk that is a clause
            for chunk in chunks:
                if chunk["metadata"]["type"] == "clause":
                    print(json.dumps(chunk, indent=2, ensure_ascii=False))
                    break
    else:
        print("JSON file not found. Run structurer first.")
