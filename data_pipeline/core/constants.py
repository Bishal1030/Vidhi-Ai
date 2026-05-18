import re

# Nepali numerals to standard digits mapping
NEPALI_DIGITS = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
}

STANDARD_TO_NEPALI_DIGITS = {v: k for k, v in NEPALI_DIGITS.items()}

def nepali_to_int(nepali_str: str) -> int:
    """Converts a string of Nepali numerals to a standard integer."""
    if not nepali_str:
        return 0
    clean_str = ''.join(NEPALI_DIGITS.get(char, '') for char in str(nepali_str) if char in NEPALI_DIGITS)
    return int(clean_str) if clean_str else 0

def int_to_nepali(num: int) -> str:
    """Converts a standard integer or string to Nepali numerals."""
    return ''.join(STANDARD_TO_NEPALI_DIGITS.get(char, char) for char in str(num))

# Legal structure keywords in Nepali
KEYWORDS = {
    'PART': 'भाग',
    'CHAPTER': 'परिच्छेद',
    'CHAPTER_ALT': 'अध्याय',
    'SECTION': 'दफा',
    'ARTICLE': 'धारा',  # Used in Constitution
    'SUBSECTION': 'उपदफा',
    'SUBARTICLE': 'उपधारा',  # Used in Constitution
    'CLAUSE': 'खण्ड',
    'SUBCLAUSE': 'उपखण्ड',
    'SCHEDULE': 'अनुसूची'
}

# Regex patterns for matching hierarchical units in Nepali text
# E.g., "भाग १", "परिच्छेद २", "धारा ३", "दफा ४"
# Note that we use unicode ranges and flexible whitespace patterns.
PART_PATTERN = re.compile(r'^\s*भाग\s+([०-९१-९]+)\s*$', re.IGNORECASE)
CHAPTER_PATTERN = re.compile(r'^\s*(परिच्छेद|अध्याय)\s+([०-९१-९]+)\s*$', re.IGNORECASE)
# Sections/Articles usually start with a number followed by a period or dot, or start with "धारा" or "दफा"
# Constitution: "धारा १. ... " or "१. ... " inside a chapter
# Acts: "दफा ३. ... " or "३. ... "
SECTION_OR_ARTICLE_PATTERN = re.compile(r'^\s*(धारा|दफा)\s+([०-९१-९]+)\s*[\.\:]?\s*(.*)$')
# Standalone number pattern for sections: "१. नेपालको संविधान..."
STANDALONE_SECTION_PATTERN = re.compile(r'^\s*([०-९१-९]+)\s*[\.\:]\s*(.*)$')

# Subsections/Subarticles are usually bracketed numbers: "(१)", "(२)"
SUBSECTION_OR_SUBARTICLE_PATTERN = re.compile(r'^\s*\(([०-९१-९]+)\)\s*(.*)$')

# Clauses are usually bracketed letters: "(क)", "(ख)", "(ग)" etc.
# Nepali alphabet bracketed: (क) to (ह)
CLAUSE_LETTER_PATTERN = re.compile(r'^\s*\(([क-ह])\)\s*(.*)$')

# Sub-clauses are usually bracketed sub-numbers/symbols like (१), (२) under clause
SUBCLAUSE_PATTERN = re.compile(r'^\s*\(([०-९१-९]+)\)\s*(.*)$')
