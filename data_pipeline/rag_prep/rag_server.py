import json
import os
import sys
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

# Set logging level to INFO
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("rag_server")

# Load environment variables from data_pipeline/.env
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env"))
load_dotenv(env_path)

# Add workspace to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from data_pipeline.rag_prep.rag_engine import LegalRAGEngine
    # Initialize the RAG engine once (warm loads sentence-transformers in memory)
    logger.info("Initializing RAG Engine inside persistent server context...")
    engine = LegalRAGEngine()
    logger.info("RAG Engine successfully loaded in memory.")
except Exception as e:
    logger.error(f"Critical failure initializing RAG engine: {e}")
    sys.exit(1)

class RAGHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean terminal output by suppressing standard HTTP access logging
        pass
        
    def do_POST(self):
        if self.path == '/query':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                query = data.get('query', '')
                limit = data.get('limit', 12)
                
                if not query:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Query parameter is required.'}).encode('utf-8'))
                    return
                
                # Execute warm in-memory RAG generation (lightning fast)
                result = engine.ask_question(query, limit=limit)
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
                
            except Exception as e:
                logger.error(f"Error handling query: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f"Internal server error: {str(e)}"}, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

def run(port=5001):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, RAGHandler)
    logger.info(f"Persistent RAG Microservice running on http://127.0.0.1:{port}")
    sys.stdout.flush()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Stopping RAG server...")
        httpd.server_close()

if __name__ == '__main__':
    run()
