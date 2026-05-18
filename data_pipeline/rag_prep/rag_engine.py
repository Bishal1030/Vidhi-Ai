import os
import sys
import logging
from typing import Dict, Any, List, Tuple
from dotenv import load_dotenv

# Add workspace to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Load environment variables from data_pipeline/.env
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env"))
load_dotenv(env_path)

from langchain_google_genai import ChatGoogleGenerativeAI
from data_pipeline.rag_prep.context_builder import LegalContextBuilder
from data_pipeline.rag_prep.citation_mapper import LegalCitationMapper

logger = logging.getLogger("rag_engine")

class LegalRAGEngine:
    """
    Unified master RAG engine using LangChain and Google Gemini.
    Retrieves Nepali laws, prompts Gemini for legally precise responses,
    and maps exact citation markers back to source database records.
    """
    def __init__(self, collection_name: str = "vidhi_legal_acts"):
        self.context_builder = LegalContextBuilder(collection_name=collection_name)
        self.citation_mapper = LegalCitationMapper()
        
        # Load API keys from environment
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("No GEMINI_API_KEY or GOOGLE_API_KEY found in .env environment!")
            raise ValueError("Missing Gemini Google API Credentials. Please check your .env file.")
            
        # Initialize LangChain Google Gemini Chat model
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.0,
            max_tokens=2048
        )
        logger.info("Successfully initialized LangChain Gemini RAG Engine.")

    def ask_question(self, query: str, limit: int = 12) -> Dict[str, Any]:
        """
        Executes complete RAG lifecycle: Retrieval -> Prompt assembly -> Gemini generation -> Citation mapping
        """
        logger.info(f"Answering query: '{query}'...")
        
        # Step 1: Retrieval (Fetch top semantic hits from Qdrant Cloud)
        hits = self.context_builder.retrieve_relevant_chunks(query, limit=limit)
        
        # Dynamically detect if the query is in Nepali (contains Devanagari characters)
        query_is_nepali = any(ord(char) >= 0x0900 and ord(char) <= 0x097F for char in query)
        
        if not hits:
            logger.warning("No relevant legal references found in the vector database.")
            fallback_ans = (
                "माफ गर्नुहोस्, तपाईंको प्रश्नसँग सम्बन्धित कुनै पनि कानूनी व्यवस्था हाम्रो डाटाबेसमा भेटिएन।"
                if query_is_nepali else
                "Sorry, no relevant legal provisions were found in our database."
            )
            return {
                "query": query,
                "answer": fallback_ans,
                "sources": []
            }
            
        # Step 2: Build Structured Context
        structured_context = self.context_builder.build_context(hits)
        
        # Step 3: Define RAG Prompt Structure dynamically based on Query Language
        if query_is_nepali:
            system_prompt = (
                "तपाईं 'विधि-एआई' (Vidhi-Ai) नामक एक विशेषज्ञ नेपाली कानूनी सहायक हुनुहुन्छ।\n"
                "तल दिइएको 'STRUCTURED LEGAL REFERENCE CONTEXT' का आधिकारिक कानूनी दस्तावेजहरूको आधारमा मात्र प्रयोगकर्ताको प्रश्नको उत्तर दिनुहोस्।\n\n"
                "कडा नियमहरू:\n"
                "१. उत्तर दिँदा केवल र केवल उपलब्ध गराइएको सन्दर्भ सामग्री (Context) मा आधारित रहनुहोस्। आफ्नो मनगढन्ते कुराहरू नलेख्नुहोस्।\n"
                "२. तपाईंले उल्लेख गर्नुभएको हरेक कानूनी बुँदा वा तथ्यको पछाडि सम्बन्धित सन्दर्भको सूचकांक (Citation Index) अनिवार्य रूपमा राख्नुहोस् (जस्तै: [CITATION 1] वा [CITATION 2])।\n"
                "३. उत्तर पूर्ण रूपमा आधिकारिक र शिष्ट नेपाली भाषामा हुनुपर्दछ।\n"
                "४. यदि दिइएको सन्दर्भ सामग्रीमा सोधिएको प्रश्नको उत्तर छैन भने, सिधै भन्नुहोस्: 'उपलब्ध आधिकारिक दस्तावेजहरूमा यस सम्बन्धमा स्पष्ट व्यवस्था भेटिएन।'\n"
                "५. अनावश्यक कुराहरू वा अनुमानहरू नगर्नुहोस्।\n\n"
                f"{structured_context}"
            )
        else:
            system_prompt = (
                "You are 'Vidhi-Ai', an expert legal assistant specializing in Nepalese law.\n"
                "Answer the user's query in professional, clear, and concise English, based strictly and ONLY on the provided "
                "'STRUCTURED LEGAL REFERENCE CONTEXT' (which contains official Nepalese legal texts in Nepali).\n\n"
                "Strict Rules:\n"
                "1. Base your answer entirely on the provided Context. Do not make up facts or use external legal knowledge.\n"
                "2. For every legal point or fact you state, you MUST append its corresponding Citation Index token (e.g. [CITATION 1] or [CITATION 2]) exactly at the end of the sentence.\n"
                "3. Your response must be entirely in professional and clear English.\n"
                "4. If the provided context does not contain the answer to the query, respond exactly with: "
                "'The requested legal provision was not found in the official documents.'\n"
                "5. Do not speculate or add conversational filler.\n\n"
                f"{structured_context}"
            )
        
        # Step 4: Execute Gemini Model Generation via LangChain
        messages = [
            ("system", system_prompt),
            ("user", query)
        ]
        
        try:
            logger.info("Invoking Google Gemini model via LangChain...")
            response = self.llm.invoke(messages)
            raw_answer = response.content
            logger.info("Gemini generated response successfully.")
        except Exception as e:
            logger.error(f"Gemini API invocation failed: {e}")
            err_ans = (
                f"त्रुटि: जेमिनी मोडेलसँग सम्पर्क स्थापित गर्न सकिएन। विवरण: {e}"
                if query_is_nepali else
                f"Error: Could not connect to Gemini model. Details: {e}"
            )
            return {
                "query": query,
                "answer": err_ans,
                "sources": []
            }
            
        # Step 5: Map Inline Citation Tokens to Anchor Anchors & Sidebar References
        mapped_answer, sources = self.citation_mapper.map_citations(raw_answer, hits)
        
        return {
            "query": query,
            "answer": mapped_answer,
            "sources": sources
        }

if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) > 1:
        # Set all loggers to ERROR to prevent logs from contaminating stdout JSON
        logging.basicConfig(level=logging.ERROR)
        logging.getLogger("rag_engine").setLevel(logging.ERROR)
        logging.getLogger("context_builder").setLevel(logging.ERROR)
        logging.getLogger("vector_store").setLevel(logging.ERROR)
        logging.getLogger("embedder").setLevel(logging.ERROR)
        
        query = sys.argv[1]
        try:
            engine = LegalRAGEngine()
            result = engine.ask_question(query, limit=12)
            print(json.dumps(result, ensure_ascii=False))
        except Exception as err:
            print(json.dumps({"error": str(err)}, ensure_ascii=False))
        sys.exit(0)

    # Test RAG Engine with a real query
    logging.basicConfig(level=logging.INFO)
    try:
        engine = LegalRAGEngine()
        
        # Test Query
        question = "के नेपाली नागरिकलाई नागरिकताबाट वञ्चित गर्न सकिन्छ?"
        result = engine.ask_question(question, limit=4)
        
        print("\n=========================================================")
        print(f"QUESTION: {result['query']}")
        print("=========================================================")
        print("\nANSWER:")
        print(result['answer'])
        print("\n=========================================================")
        print("SOURCES SIDEBAR METADATA:")
        print(json.dumps(result['sources'], indent=2, ensure_ascii=False))
        print("=========================================================")
    except Exception as err:
        print(f"RAG Engine Initialization or execution failed: {err}")
