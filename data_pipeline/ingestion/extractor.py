import os
import sys
import pdfplumber
import pypdf
import re
import logging
from typing import Optional

# Add workspace to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingestion.config import RAW_DOCS_DIR, PROCESSED_TEXT_DIR, INGESTION_LOG, ERROR_LOG

logger = logging.getLogger("extractor")

# Mappings of common OCR/ligature errors in Nepali Law Commission PDFs to correct standard Unicode Nepali
NEPALI_LIGATURE_REPLACEMENTS = [
    # 1. New custom healers for newly identified PDF encoding scrambles
    (r'जजल्ला', 'जिल्ला'),
    (r'अदालििरू', 'अदालतहरू'),
    (r'अदालिहरू', 'अदालतहरू'),
    (r'अदालिको', 'अदालतको'),
    (r'अदालिका', 'अदालतका'),
    (r'अदालि', 'अदालत'),
    (r'बिस\s+पैरिी', 'बहस पैरवी'),
    (r'बिस', 'बहस'),
    (r'पैरिी', 'पैरवी'),
    (r'सेिामनित्तृ', 'सेवानिवृत्त'),
    (r'सेिामनिवृत्त', 'सेवानिवृत्त'),
    (r'सेिा', 'सेवा'),
    (r'मािििका', 'मातहतका'),
    (r'सिोच्च', 'सर्वोच्च'),
    (r'उपजस्थि', 'उपस्थित'),
    (r'कोिैमसयिमा', 'को हैसियतमा'),
    (r'कोिैमसयि', 'को हैसियत'),
    (r'िैमसयिमा', 'हैसियतमा'),
    (r'िैमसयि', 'हैसियत'),
    (r'अमभलेख', 'अभिलेख'),
    (r'राख्\s*ने\s*िथा', 'राख्ने तथा'),
    (r'राख्\s*ने', 'राख्ने'),
    (r'गन\s*व', 'गर्न'),
    (r'पिरचय', 'परिचय'),

    # 2. Very common specific words
    (r'नागररकिा', 'नागरिकता'),
    (r'नागररकिाको', 'नागरिकताको'),
    (r'नागररकिासम्बन्धी', 'नागरिकतासम्बन्धी'),
    (r'नागररक', 'नागरिक'),
    (r'नागररकहरू', 'नागरिकहरू'),
    (r'नागररकिाहरू', 'नागरिकताहरू'),
    (r'प्रारजम्भक', 'प्रारम्भिक'),
    (r'अनसु\s+ूची', 'अनुसूची'),
    (r'अनसु\s*ूची', 'अनुसूची'),
    
    (r'स्ििन्त्रिा', 'स्वतन्त्रता'),
    (r'स्विन्त्रिा', 'स्वतन्त्रता'),
    (r'स्िाधीनिा', 'स्वाधीनता'),
    (r'स्िाधीन', 'स्वाधीन'),
    (r'स्वाधीनिा', 'स्वाधीनता'),
    
    (r'मौमलक िक', 'मौलिक हक'),
    (r'मौमलक िकहरू', 'मौलिक हकहरू'),
    (r'िक र किव्वय', 'हक र कर्तव्य'),
    (r'िकः', 'हकः'),
    (r'िक\s+', 'हक '),
    
    (r'किव्वय', 'कर्तव्य'),
    (r'किव्व य', 'कर्तव्य'),
    (r'किव्वयहरू', 'कर्तव्यहरू'),
    
    (r'सम्मानपूिकव', 'सम्मानपूर्वक'),
    (r'मत्ृ यदु ण्डको', 'मृत्युदण्डको'),
    (r'िज‍ चि', 'वञ्चित'),
    (r'देिायको', 'देहायको'),
    (r'देिाय', 'देहाय'),
    (r'िाििमियार', 'हातहतियार'),
    (r'पविचान', 'पहचान'),
    (r'लैंविक', 'लैंगिक'),
    (r'सविको', 'सहितको'),
    
    (r'प्राजप्ि', 'प्राप्ति'),
    (r'समामित', 'समाप्ति'),
    (r'पुनःप्राजप्ि', 'पुनःप्राप्ति'),
    (r'िंशीय', 'वंशीय'),
    (r'िंशज', 'वंशज'),
    (r'अंगीकृ ि', 'अंगीकृत'),
    (r'अंिीकृ ि', 'अंगीकृत'),
    
    (r'राविय', 'राष्ट्रिय'),
    (r'रावियिा', 'राष्ट्रियता'),
    (r'सािभव ौम', 'सार्वभौम'),
    (r'सािभव ौमसत्ता', 'सार्वभौमसत्ता'),
    (r'भौगोमलक', 'भौगोलिक'),
    (r'अखण्डिा', 'अखण्डता'),
    (r'अमभव्यजक्त', 'अभिव्यक्ति'),
    (r'व्यजक्त', 'व्यक्ति'),
    (r'व्यजक्तलाई', 'व्यक्तिलाई'),
    (r'व्यजक्तले', 'व्यक्तिले'),
    (r'व्यजक्तको', 'व्यक्तिको'),
    (r'राजनीमिक', 'राजनीतिक'),
    (r'प्रमिमनमध', 'प्रतिनिधि'),
    (r'प्रमिमनमधलाई', 'प्रतिनिधिलाई'),
    (r'प्रमि', 'प्रति'),
    (r'भेदभाि', 'भेदभाव'),
    (r'दुरुत्सािन', 'दुरुत्साहन'),
    (r'दरुु त्सािन', 'दुरुत्साहन'),
    (r'अििेलना', 'अवहेलना'),
    (r'विंसात्मक', 'हिंसात्मक'),
    (r'िंसात्मक', 'हिंसात्मक'),
    (r'मनामसब', 'मनासिब'),
    (r'प्रमिबन्ध', 'प्रतिबन्ध'),
    (r'प्रमिकू ल', 'प्रतिकूल'),
    
    (r'कायव', 'कार्य'),
    (r'कार्यमा', 'कार्यमा'),
    (r'कार्रयमव ा', 'कार्यमा'),
    (r'मत्ृ यु', 'मृत्यु'),
    (r'मत्ृ यदु ण्ड', 'मृत्युदण्ड'),
    (r'मलु क', 'मुलुक'),
    (r'मलु कु को', 'मुलुकको'),
    (r'मनजले', 'निजले'),
    (r'मनजको', 'निजको'),
    (r'मनज', 'निज'),
    (r'रिेछन्', 'रहेछन्'),
    (r'रिेछन ्', 'रहेछन्'),
    
    # 2. Frequent pattern/ligature corrections
    (r'िुनेछ', 'हुनेछ'),
    (r'िुनेछन्', 'हुनेछन्'),
    (r'िनु ेछ', 'हुनेछ'),
    (r'िनु ेछन्', 'हुनेछन्'),
    (r'िुन', 'हुन'),
    (r'िुने', 'हुने'),
    (r'िनु े', 'हुने'),
    (r'िुँदा', 'हुँदा'),
    (r'िुनेगरी', 'हुनेगरी'),
    
    # 3. Clean up loose vowel signs or ligatures
    (r'\s+्', '्'),
    (r'\s+ु', 'ु'),
    (r'\s+ि', 'ि'),
    (r'\s+ी', 'ी'),
    (r'\s+ो', 'ो'),
    (r'\s+ौ', 'ौ'),
    (r'\s+ा', 'ा'),
]

def clean_extracted_text(text: str) -> str:
    """
    Cleans and normalizes common OCR and ligatures errors extracted from Nepal Law Commission PDFs.
    """
    if not text:
        return ""
        
    cleaned = text
    
    # Run the regex-based ligature and OCR spelling corrections
    for pattern, replacement in NEPALI_LIGATURE_REPLACEMENTS:
        cleaned = re.sub(pattern, replacement, cleaned)
        
    # Separate merged Part 1 title "प्रारम्भिक" from Section 1 "१."
    cleaned = re.sub(r'प्रारम्भहक\s+([०-९१-९]+\.)', r'प्रारम्भिक\n\1', cleaned)
    cleaned = re.sub(r'प्रारम्भिक\s+([०-९१-९]+\.)', r'प्रारम्भिक\n\1', cleaned)
        
    # Clean redundant spaces before punctuation
    cleaned = re.sub(r'\s+([।\:\,\.\?])', r'\1', cleaned)
    
    # Strip Law Commission header/footer watermark standard patterns
    cleaned = re.sub(r'www\.lawcommission\.gov\.np', '', cleaned, flags=re.IGNORECASE)
    
    # Normalize double spaces
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    
    return cleaned

def extract_text_from_pdf(pdf_path: str) -> Optional[str]:
    """
    Extracts raw text from a PDF, cleans OCR/ligature issues, and returns the full text.
    Uses pdfplumber with a fallback to pypdf.
    """
    logger.info(f"Extracting text from PDF: {pdf_path}")
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file does not exist: {pdf_path}")
        return None
        
    full_text = []
    
    # Try pdfplumber first (typically has better structural extraction)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            logger.info(f"Using pdfplumber to parse {len(pdf.pages)} pages...")
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    cleaned_page = clean_extracted_text(page_text)
                    full_text.append(f"--- PAGE {i+1} ---\n{cleaned_page}")
    except Exception as plumber_err:
        logger.warning(f"pdfplumber failed: {plumber_err}. Falling back to pypdf.")
        full_text = [] # Reset
        try:
            reader = pypdf.PdfReader(pdf_path)
            logger.info(f"Using pypdf to parse {len(reader.pages)} pages...")
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    cleaned_page = clean_extracted_text(page_text)
                    full_text.append(f"--- PAGE {i+1} ---\n{cleaned_page}")
        except Exception as pypdf_err:
            logger.error(f"pypdf fallback also failed: {pypdf_err}")
            with open(ERROR_LOG, "a") as err_f:
                err_f.write(f"Failed extracting text from {pdf_path}: {pypdf_err}\n")
            return None
            
    if not full_text:
        logger.warning("No text could be extracted from PDF.")
        return None
        
    extracted_text = "\n\n".join(full_text)
    
    # Save the processed text
    pdf_filename = os.path.basename(pdf_path)
    text_filename = os.path.splitext(pdf_filename)[0] + ".txt"
    dest_path = os.path.join(PROCESSED_TEXT_DIR, text_filename)
    
    try:
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)
        logger.info(f"Saved processed text to {dest_path}")
        return extracted_text
    except Exception as e:
        logger.error(f"Failed to save processed text to {dest_path}: {e}")
        return extracted_text


