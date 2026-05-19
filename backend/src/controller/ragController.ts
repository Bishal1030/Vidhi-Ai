import type { Request, Response } from 'express';
import { RAGService } from '../service/ragService.js';

export class RAGController {
    /**
     * Handles /api/chat POST requests by validating input, passing
     * it to RAGService, and sending the verified JSON output to client.
     */
    public static async chat(req: Request, res: Response): Promise<void> {
        try {
            const { query } = req.body;
            
            if (!query || typeof query !== 'string' || query.trim() === '') {
                res.status(400).json({
                    error: "Query parameter is required"
                });
                return;
            }
            
            const result = await RAGService.askQuestion(query);
            res.status(200).json(result);
        } catch (error: any) {
            console.error(`Controller Error: ${error.message}`);
            res.status(500).json({
                error: "something went wrong",
                details: error.message
            });
        }
    }
}
