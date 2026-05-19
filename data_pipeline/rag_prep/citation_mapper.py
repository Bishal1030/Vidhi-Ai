import re
import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("citation_mapper")

class LegalCitationMapper:
    """
    Parses LLM-generated legal answers, maps inline citation markers (e.g., [CITATION 1])
    back to their exact act database references, and structures citation sidebars.
    """
    def __init__(self):
        pass

    def map_citations(self, llm_answer: str, retrieved_hits: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Parses LLM response, replaces [CITATION X] tags with clean legal citations,
        and compiles a structured list of exact references used in the response.
        """
        if not llm_answer or not retrieved_hits:
            return llm_answer, []

        used_citations = []
        mapped_answer = llm_answer
        
        # Regex to locate markers like [CITATION 1], [CITATION 2], etc.
        citation_pattern = re.compile(r'\[CITATION\s*(\d+)\]', re.IGNORECASE)
        
        # Find all unique citation indices mentioned in the text
        matches = citation_pattern.findall(llm_answer)
        unique_indices = sorted(list(set(int(idx) for idx in matches)))
        
        for idx in unique_indices:
            hit_index = idx - 1  # 0-indexed in the hits list
            if 0 <= hit_index < len(retrieved_hits):
                hit = retrieved_hits[hit_index]
                payload = hit["payload"]
                
                citation_name = payload.get("citation", "सन्दर्भ")
                act_title = payload.get("nepali_title", payload.get("act_title", ""))
                sec_id = payload.get("section_id", "")
                
                # Standardize anchor URL tag for UI links
                anchor_link = f"#{act_title.replace(' ', '_')}_धारा_{sec_id}"
                
                # Premium Markdown format
                replacement_text = f"**[{citation_name}]({anchor_link})**"
                
                # Replace inline marker in answer
                pattern_to_replace = re.compile(rf'\[CITATION\s*{idx}\]', re.IGNORECASE)
                mapped_answer = pattern_to_replace.sub(replacement_text, mapped_answer)
                
                # Record in the used sources list
                source_meta = {
                    "citation_index": idx,
                    "citation_text": citation_name,
                    "act_title": act_title,
                    "section_id": sec_id,
                    "section_title": payload.get("section_title", ""),
                    "subsection_id": payload.get("subsection_id", ""),
                    "clause_id": payload.get("clause_id", ""),
                    "raw_text": payload.get("raw_text", ""),
                    "score": hit.get("score", 0.0),
                    "anchor": anchor_link
                }
                used_citations.append(source_meta)
                
        return mapped_answer, used_citations


