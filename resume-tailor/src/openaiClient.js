// src/openaiClient.js
import "dotenv/config"; // <-- ensure .env is loaded before reading envs
import OpenAI from "openai";

// Fail fast with helpful error if key is missing
const key = process.env.OPENAI_API_KEY?.trim();
if (!key) {
  throw new Error(
    "OPENAI_API_KEY is missing. Create a .env in the project root with OPENAI_API_KEY=sk-... (no quotes)."
  );
}

export const openai = new OpenAI({ apiKey: key });
