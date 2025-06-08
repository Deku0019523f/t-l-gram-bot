import express from 'express';
import cors from 'cors';
import fetch from 'node-fetch';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
const port = process.env.PORT || 8080;

// ✅ Activer CORS pour GitHub Pages
app.use(cors({
  origin: 'https://deku0019523f.github.io', // <-- ton vrai domaine GitHub Pages
  methods: ['GET', 'POST', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json());

app.post('/generate', async (req, res) => {
  const prompt = req.body.prompt;

  if (!prompt) {
    return res.status(400).json({ error: 'Prompt manquant.' });
  }

  try {
    const response = await fetch('https://api.openai.com/v1/images/generations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`
      },
      body: JSON.stringify({
        prompt,
        n: 1,
        size: "512x512"
      })
    });

    const data = await response.json();

    if (data && data.data && data.data[0]) {
      return res.status(200).json({ image: data.data[0].url });
    } else {
      return res.status(500).json({ error: 'Réponse invalide de l’API OpenAI.' });
    }
  } catch (error) {
    console.error("Erreur serveur :", error);
    return res.status(500).json({ error: 'Erreur serveur.' });
  }
});

app.listen(port, () => {
  console.log(`✅ Serveur démarré sur le port ${port}`);
});
