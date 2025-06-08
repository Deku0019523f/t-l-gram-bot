import express from "express";
import fetch from "node-fetch";
import cors from "cors";
import dotenv from "dotenv";
dotenv.config();

const app = express();
const port = process.env.PORT || 8080;

app.use(cors({
  origin: "https://deku0019523f.github.io"  // ✅ Autorise les requêtes venant de GitHub Pages
}));
app.use(express.json());

app.post("/generate", async (req, res) => {
  const prompt = req.body.prompt;
  if (!prompt) {
    return res.status(400).json({ error: "Prompt manquant" });
  }

  try {
    const response = await fetch("https://api.openai.com/v1/images/generations", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`
      },
      body: JSON.stringify({
        prompt,
        n: 1,
        size: "512x512"
      })
    });

    const data = await response.json();
    if (data?.data?.[0]?.url) {
      res.status(200).json({ image: data.data[0].url });
    } else {
      res.status(500).json({ error: "Erreur de génération", details: data });
    }
  } catch (error) {
    res.status(500).json({ error: "Erreur serveur", details: error.message });
  }
});

app.listen(port, () => {
  console.log(`✅ Serveur démarré sur le port ${port}`);
});
