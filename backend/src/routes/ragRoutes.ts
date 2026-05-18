import { Router } from 'express';
import { RAGController } from '../controller/ragController.js';

const router = Router();

// Route for verified legal RAG chat
router.post('/chat', RAGController.chat);

export default router;
