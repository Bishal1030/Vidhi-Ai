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
                    error: "कृपया प्रश्न प्रविष्ट गर्नुहोस् (Query parameter is required)."
                });
                return;
            }
            
            const result = await RAGService.askQuestion(query);
            res.status(200).json(result);
        } catch (error: any) {
            console.error(`Controller Error: ${error.message}`);
            res.status(500).json({
                error: "आन्तरिक त्रुटि उत्पन्न भयो।",
                details: error.message
            });
        }
    }
}
