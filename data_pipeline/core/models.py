from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
import json

@dataclass
class SubClause:
    identifier: str  # E.g., "(१)" or "१"
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Clause:
    identifier: str  # E.g., "(क)" or "क"
    text: str
    sub_clauses: List[SubClause] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identifier": self.identifier,
            "text": self.text,
            "sub_clauses": [sc.to_dict() for sc in self.sub_clauses],
            "metadata": self.metadata
        }

@dataclass
class Subsection:
    identifier: str  # E.g., "(१)" or "१"
    text: str
    clauses: List[Clause] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identifier": self.identifier,
            "text": self.text,
            "clauses": [c.to_dict() for c in self.clauses],
            "metadata": self.metadata
        }

@dataclass
class Section:
    identifier: str  # E.g., "१"
    title: str       # E.g., "संक्षिप्त नाम र प्रारम्भ" or "राष्ट्रिय झण्डा"
    text: Optional[str] = None
    subsections: List[Subsection] = field(default_factory=list)
    clauses: List[Clause] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identifier": self.identifier,
            "title": self.title,
            "text": self.text,
            "subsections": [s.to_dict() for s in self.subsections],
            "clauses": [c.to_dict() for c in self.clauses],
            "metadata": self.metadata
        }

@dataclass
class Chapter:
    identifier: str  # E.g., "१"
    title: str       # E.g., "प्रारम्भिक"
    sections: List[Section] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identifier": self.identifier,
            "title": self.title,
            "sections": [s.to_dict() for s in self.sections],
            "metadata": self.metadata
        }

@dataclass
class Part:
    identifier: str  # E.g., "१"
    title: str       # E.g., "प्रारम्भिक"
    chapters: List[Chapter] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "identifier": self.identifier,
            "title": self.title,
            "chapters": [c.to_dict() for c in self.chapters],
            "metadata": self.metadata
        }

@dataclass
class Schedule:
    identifier: str  # E.g., "१" or "अनुसूची–१"
    title: str       # E.g., "नेपालको राष्ट्रिय झण्डा"
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Act:
    title: str
    nepali_title: str
    source_url: str
    pdf_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    parts: List[Part] = field(default_factory=list)
    chapters: List[Chapter] = field(default_factory=list)  # Direct chapters (if no parts)
    sections: List[Section] = field(default_factory=list)  # Direct sections (if no parts/chapters)
    schedules: List[Schedule] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "nepali_title": self.nepali_title,
            "source_url": self.source_url,
            "pdf_url": self.pdf_url,
            "metadata": self.metadata,
            "parts": [p.to_dict() for p in self.parts],
            "chapters": [c.to_dict() for c in self.chapters],
            "sections": [s.to_dict() for s in self.sections],
            "schedules": [s.to_dict() for s in self.schedules]
        }

    def to_json(self, indent: int = 4) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
