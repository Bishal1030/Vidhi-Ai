import express from 'express';
import type { Request, Response } from 'express';
import ragRoutes from './routes/ragRoutes.js';

const app = express();
const PORT = 3000;

// Middleware to parse JSON bodies
app.use(express.json());

// Routes
app.use('/api', ragRoutes);

app.get('/', (req: Request, res: Response) => {
    res.send('Hello, TypeScript Express!');
});

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});
