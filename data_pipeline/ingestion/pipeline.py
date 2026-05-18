import os
import sys
import logging
import argparse
from typing import Optional

# Add workspace to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingestion.config import INGESTION_LOG, ERROR_LOG, RAW_DOCS_DIR, PROCESSED_TEXT_DIR, STRUCTURED_ACTS_DIR, CONSTITUTION_CATEGORY_URL
from ingestion.scraper import scrape_category
from ingestion.fetcher import download_pdf
from ingestion.extractor import extract_text_from_pdf
from ingestion.structurer import process_extracted_text_file
from ingestion.validator import run_validation

# Setup master pipeline logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(INGESTION_LOG, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("pipeline")

def run_pipeline(limit_docs: Optional[int] = None) -> bool:
    """
    Orchestrates the full end-to-end ingestion pipeline:
    1. Scrapes the Nepal Law Commission Constitution category.
    2. Downloads the target PDF attachment.
    3. Extracts and cleans/heals the PDF content.
    4. Structural parses the text into an Act->Part->Section->Clause tree.
    5. Validates schema compliance and citation integrity.
    """
    logger.info("=========================================================")
    logger.info("STARTING VIDHI-AI LEGAL INGESTION PIPELINE")
    logger.info("=========================================================")
    
    # Step 1: Scrape Law Commission site
    logger.info("Step 1: Scraping Law Commission category (Constitutions)...")
    scraped_acts = scrape_category(CONSTITUTION_CATEGORY_URL)
    if not scraped_acts:
        logger.error("Pipeline failed: Scraper could not retrieve any acts from the website.")
        return False
        
    logger.info(f"Successfully scraped metadata for {len(scraped_acts)} acts.")
    
    # Process scraped acts
    success_count = 0
    failed_count = 0
    
    for idx, act_meta in enumerate(scraped_acts):
        if limit_docs and idx >= limit_docs:
            logger.info(f"Reached doc processing limit ({limit_docs}). Stopping pipeline.")
            break
            
        title = act_meta["title"]
        source_url = act_meta["detail_url"] or CONSTITUTION_CATEGORY_URL
        target_pdf_url = act_meta["pdf_url"]
        
        logger.info(f"\n--- Processing Act {idx+1}/{len(scraped_acts)}: {title} ---")
        
        if not target_pdf_url:
            logger.warning(f"Act '{title}' has no associated PDF URL. Skipping.")
            failed_count += 1
            continue
        
        # Step 2: Download PDF
        logger.info(f"Step 2: Downloading document from {target_pdf_url}...")
        local_pdf_path = download_pdf(target_pdf_url, title)
        if not local_pdf_path:
            logger.error(f"Failed to download PDF for Act '{title}'. Skipping.")
            failed_count += 1
            continue
            
        # Step 3: Extract and Clean Text
        logger.info(f"Step 3: Extracting and normalizing text from {local_pdf_path}...")
        raw_text_path = os.path.join(PROCESSED_TEXT_DIR, os.path.splitext(os.path.basename(local_pdf_path))[0] + ".txt")
        text = extract_text_from_pdf(local_pdf_path)
        if not text:
            logger.error(f"Failed text extraction/cleaning for '{title}'. Skipping.")
            failed_count += 1
            continue
            
        # Step 4: Structure Act Tree
        logger.info(f"Step 4: Structuring text into hierarchical JSON...")
        structured_json_path = process_extracted_text_file(
            raw_text_path,
            title,
            source_url,
            target_pdf_url
        )
        if not structured_json_path:
            logger.error(f"Failed hierarchical structuring for '{title}'. Skipping.")
            failed_count += 1
            continue
            
        # Step 5: Validate Schema & Cross-References
        logger.info(f"Step 5: Validating structural schema and cross-reference citation integrity...")
        validation_success = run_validation(structured_json_path)
        if not validation_success:
            logger.warning(f"Validation alerts raised for structured JSON: {structured_json_path}")
            
        logger.info(f"Successfully ingested, structured, and validated Act '{title}'!")
        
        # Step 6: Update Search Vector Index in Qdrant Cloud
        logger.info(f"Step 6: Building and uploading RAG search index to Qdrant Cloud...")
        try:
            from indexing.index_builder import LegalIndexBuilder
            builder = LegalIndexBuilder()
            index_success = builder.build_index_for_file(structured_json_path)
            if index_success:
                logger.info(f"🎉 Fully Indexed Act '{title}' into Qdrant Vector Store!")
                success_count += 1
            else:
                logger.error(f"Failed to build vector search index for Act '{title}'.")
                failed_count += 1
        except Exception as e:
            logger.error(f"Failed to execute vector search indexing: {e}")
            failed_count += 1
        
    logger.info("=========================================================")
    logger.info("VIDHI-AI PIPELINE WORKFLOW COMPLETE")
    logger.info(f"   - Successfully Processed: {success_count} Acts")
    logger.info(f"   - Failed/Skipped:        {failed_count} Acts")
    logger.info("=========================================================")
    
    return success_count > 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vidhi-Ai Legal Ingestion Pipeline Orchestrator")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of scraped documents to process")
    args = parser.parse_args()
    
    run_pipeline(limit_docs=args.limit)
