// src/server.js
import express from "express";
import helmet from "helmet";
import morgan from "morgan";
import cors from "cors";
import rateLimit from "express-rate-limit";
import dotenv from "dotenv";
import path from "path";
import optimizeRouter from "./routes/optimize.js";

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

app.use(helmet());
app.use(morgan(process.env.NODE_ENV === "development" ? "dev" : "combined"));
app.use(express.json({ limit: "1mb" }));
app.use(express.urlencoded({ extended: true }));
app.use(cors({
  origin: process.env.ALLOWED_ORIGIN?.split(",") ?? "*"
}));

app.use(rateLimit({
  windowMs: 60_000,
  max: 30
}));

// static UI
app.use(express.static(path.resolve("public")));

app.use("/api", optimizeRouter);

app.get("/healthz", (_, res) => res.json({ ok: true }));

app.listen(PORT, () => {
  console.log(`Resume Optimizer running on http://localhost:${PORT}`);
});
