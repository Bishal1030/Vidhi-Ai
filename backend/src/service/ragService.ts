export interface RAGResponse {
    query: string;
    answer: string;
    sources: any[];
    error?: string;
}

export class RAGService {
    /**
     * Sends query to the persistent local Python RAG microservice.
     */
    public static async askQuestion(query: string): Promise<RAGResponse> {
        const ragUrl = process.env.PYTHON_RAG_URL || 'http://127.0.0.1:5002/query';

        try {
            console.log(`[RAG Service] Dispatching query to: ${ragUrl}`);

            const response = await fetch(ragUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query, limit: 12 })
            });

            if (!response.ok) {
                throw new Error(`Microservice returned status ${response.status}`);
            }

            const result = await response.json() as RAGResponse;
            console.log('[RAG Service] Response received successfully.');
            return result;
        } catch (e: any) {
            console.error('[RAG Service Error]:', e.message);
            return {
                query,
                answer: `Error: Could not reach RAG service. Details: ${e.message}`,
                sources: [],
                error: e.message
            };
        }
    }
}
