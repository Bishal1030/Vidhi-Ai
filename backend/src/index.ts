import express from 'express';
import type { Request, Response } from 'express';
import ragRoutes from './routes/ragRoutes.js';
import cors from 'cors';

const app = express();
const PORT = process.env.PORT || 4001;

// Middleware to parse JSON bodies
app.use(express.json());

app.use(cors({ origin: "*" }));

// Routes
app.use('/api', ragRoutes);

app.get('/', (req: Request, res: Response) => {
    res.send('Hello, TypeScript Express!');
});

app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});
