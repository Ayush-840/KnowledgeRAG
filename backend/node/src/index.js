import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import { Readable } from "node:stream";

dotenv.config();

const app = express();
app.use(cors({ origin: "*" })); // dev only

const PYTHON_URL = process.env.PYTHON_URL || "http://localhost:8001";

app.get("/health", (req, res) => {
  res.json({ status: "gateway ok", uptime: process.uptime() });
});

// Generic passthrough proxy for the Python retrieval service.
// Streams the request body as-is so both JSON (/search, /chat) and
// multipart uploads (/ingest) work without reformatting.
app.use(["/ingest", "/search", "/chat", "/documents", "/title", "/space", "/graph", "/entities"], async (req, res) => {
  const target = `${PYTHON_URL}${req.originalUrl}`;
  try {
    const headers = { ...req.headers, host: new URL(target).host };
    const body = ["GET", "HEAD"].includes(req.method) ? undefined : req;
    const upstream = await fetch(target, {
      method: req.method,
      headers,
      body,
      duplex: "half",
    });
    res.status(upstream.status);
    for (const [key, value] of upstream.headers) {
      res.setHeader(key, value);
    }
    if (upstream.body) {
      // fetch() bodies are WHATWG web streams; pipe() needs a Node Readable.
      // Readable.fromWeb keeps backpressure correct and streams SSE/JSON bodies
      // (including the ?stream=1 ingest stage events) untouched.
      Readable.fromWeb(upstream.body).pipe(res);
    } else {
      res.end();
    }
  } catch (err) {
    console.error("Proxy error:", err);
    if (!res.headersSent) {
      res.status(502).json({ error: "Failed to reach Python service" });
    } else {
      res.destroy();
    }
  }
});

const PORT = process.env.PORT || 8000;
app.listen(PORT, () => {
  console.log(`🚀 Node gateway listening on http://localhost:${PORT}`);
});
