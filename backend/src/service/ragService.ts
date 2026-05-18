import { exec } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export interface RAGResponse {
    query: string;
    answer: string;
    sources: any[];
    error?: string;
}

export class RAGService {
    /**
     * Spawns the python RAG pipeline process to run semantic search and
     * get a structured, citation-mapped response from Google Gemini 2.5.
     */
    public static async askQuestion(query: string): Promise<RAGResponse> {
        return new Promise((resolve, reject) => {
            // Absolute path to the python RAG engine script
            const scriptPath = path.join(__dirname, '../../../data_pipeline/rag_prep/rag_engine.py');
            
            // Escape query string for shell execution
            const escapedQuery = query.replace(/(["'$`\\])/g, '\\$1');
            
            // Run child process to fetch answer
            exec(`python3 "${scriptPath}" "${escapedQuery}"`, (error, stdout, stderr) => {
                if (error) {
                    console.error(`RAG Execution error: ${error.message}`);
                    return resolve({
                        query,
                        answer: "माफ गर्नुहोस्, प्रणालीमा आन्तरिक समस्या उत्पन्न भयो। कृपया फेरि प्रयास गर्नुहोस्।",
                        sources: [],
                        error: error.message
                    });
                }
                
                try {
                    // Parse the clean JSON printed to stdout
                    const result = JSON.parse(stdout.trim()) as RAGResponse;
                    resolve(result);
                } catch (parseError: any) {
                    console.error(`JSON Parse error on output: ${stdout}`);
                    resolve({
                        query,
                        answer: "उत्तर प्रशोधन गर्दा प्राविधिक त्रुटि देखा पर्यो।",
                        sources: [],
                        error: parseError.message
                    });
                }
            });
        });
    }
}
