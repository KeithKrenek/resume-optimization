// src/routes/optimize.js
import fs from "fs";
import path from "path";
import { Router } from "express";
import multer from "multer";
import { nanoid } from "nanoid";
import Ajv from "ajv";
import { openai } from "../openaiClient.js";
import { resumeSchema } from "../schema/resumeSchema.js";

const router = Router();

// ---- Upload config ----
const UPLOAD_DIR = path.resolve("tmp/uploads");
fs.mkdirSync(UPLOAD_DIR, { recursive: true });

const allowedExt = new Set([".md", ".markdown", ".txt", ".json", ".pdf"]);
const maxSize = (Number(process.env.MAX_UPLOAD_MB || 10)) * 1024 * 1024;

const storage = multer.diskStorage({
  destination: (_, __, cb) => cb(null, UPLOAD_DIR),
  filename: (_, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    cb(null, `${Date.now()}-${nanoid(6)}${ext}`);
  }
});
const upload = multer({
  storage,
  limits: { fileSize: maxSize },
  fileFilter: (_, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    if (!allowedExt.has(ext)) return cb(new Error("Unsupported file type."));
    cb(null, true);
  }
});

// ---- Helpers ----
const cleanupFile = (p) => fs.existsSync(p) && fs.unlink(p, () => {});

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
async function withRetries(fn, { tries = 3, base = 400 } = {}) {
  let err;
  for (let i = 0; i < tries; i++) {
    try { return await fn(); } catch (e) {
      err = e;
      // Retry on 429/5xx and transient vector store states
      const status = e?.status || e?.response?.status;
      if (!(status === 429 || (status >= 500 && status <= 599))) break;
      await sleep(base * Math.pow(2, i)); // backoff
    }
  }
  throw err;
}

const instructionBlock = ({
  jobDescription,
  companyUrl
}) => `You are an expert resume tailor for STEM roles.
- Use the user's uploaded resume as primary source of truth via File Search.
- Research the company from: ${companyUrl}. Prefer official pages (careers, product pages, engineering blog); if unclear, use reputable sources. Use the Web Search tool for up-to-date details.
- Optimize resume content for the provided job description. Emphasize measurable impact, relevant tech, and align titles/keywords to the JD.
- Where specific metrics are missing, include tasteful placeholders like "<add metric: e.g., 25%>" so downstream editors can fill in later.
- Output must be STRICTLY valid JSON matching the provided JSON Schema. Do not include commentary outside JSON.

JOB DESCRIPTION (verbatim):
---
${jobDescription}
---`;

// ---- Route ----
router.post("/optimize", upload.single("resumeFile"), async (req, res) => {
  const start = Date.now();
  const { jobDescription, companyUrl } = req.body || {};
  const filePath = req.file?.path;

  if (!jobDescription || !companyUrl || !filePath) {
    if (filePath) cleanupFile(filePath);
    return res.status(400).json({ error: "Missing jobDescription, companyUrl, or resumeFile." });
  }

  try {
    // 1) Create vector store
    const vs = await withRetries(() =>
      openai.vectorStores.create({ name: `resume_${nanoid(6)}` })
    );
    const vsId = vs.id;

    // 2) Upload file
    const file = await withRetries(() =>
      openai.files.create({
        file: fs.createReadStream(filePath),
        purpose: "assistants"
      })
    );

    // 3) Attach via a batch and wait until indexed
    const batch = await withRetries(() =>
      openai.vectorStores.fileBatches.create(vsId, { file_ids: [file.id] })
    );

    // Poll indexing status
    const started = Date.now();
    while (true) {
      const status = await openai.vectorStores.fileBatches.retrieve(vsId, batch.id);
      if (status.status === "completed") break;
      if (status.status === "failed") {
        throw new Error(`Vector store indexing failed: ${JSON.stringify(status, null, 2)}`);
      }
      if (Date.now() - started > 60_000) { // 60s safety timeout
        throw new Error("Indexing timed out after 60s.");
      }
      await sleep(800);
    }

    // 4) Call Responses with proper tool wiring
    const toolName = process.env.WEB_SEARCH_TOOL || "web_search";
    const response = await withRetries(() =>
      openai.responses.create({
        model: process.env.OPENAI_MODEL || "gpt-4o-2024-08-06",
        parallel_tool_calls: false,                 // safer w/ structured outputs
        tools: [{ type: "file_search" }, { type: toolName }],
        tool_resources: { file_search: { vector_store_ids: [vsId] } }, // <-- correct place
        input: instructionBlock({ jobDescription, companyUrl }),
        response_format: {
          type: "json_schema",
          json_schema: resumeSchema
        }
      })
    );

    // 5) Validate strict JSON
    const raw = response.output_text;
    let parsed;
    try { parsed = JSON.parse(raw); }
    catch { return res.status(502).json({ error: "Model did not return valid JSON.", raw }); }

    const ajv = new Ajv({ allErrors: true, strict: false });
    const validate = ajv.compile(resumeSchema.schema);
    if (!validate(parsed)) {
      return res.status(502).json({ error: "JSON failed schema validation.", issues: validate.errors, raw: parsed });
    }

    return res.json({
      ok: true,
      elapsed_ms: Date.now() - start,
      resume: parsed,
      model: response.model,
      request_id: response.id
    });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: "Failed to optimize resume.", detail: err?.message });
  } finally {
    if (filePath) cleanupFile(filePath);
  }
});

export default router;
