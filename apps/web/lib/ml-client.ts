import type { AnalyzeResponse, HealthResponse } from '@/types';

const ML_BASE = process.env.ML_SERVICE_URL ?? 'http://localhost:8000';
const ML_TOKEN = process.env.ML_SERVICE_TOKEN;

function authHeaders(): Record<string, string> {
  return ML_TOKEN ? { Authorization: `Bearer ${ML_TOKEN}` } : {};
}

export class MlServiceError extends Error {
  constructor(public status: number, public code: string, message: string) {
    super(message);
    this.name = 'MlServiceError';
  }
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${ML_BASE}/v1/health`, {
    headers: authHeaders(),
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new MlServiceError(res.status, 'HEALTH_FAILED', `Health check failed: ${res.status}`);
  }
  return res.json();
}

export async function analyzeText(text: string): Promise<AnalyzeResponse> {
  const res = await fetch(`${ML_BASE}/v1/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
    },
    body: JSON.stringify({
      input_type: 'text',
      text,
      options: { max_clauses: 200, include_top_k: 3 },
    }),
    // ML pipeline can take 5-30s for a long contract
    signal: AbortSignal.timeout(60_000),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: { code: 'PARSE_ERROR', message: res.statusText } }));
    throw new MlServiceError(
      res.status,
      body.error?.code ?? 'UNKNOWN',
      body.error?.message ?? `ML service returned ${res.status}`
    );
  }

  return res.json();
}

/**
 * Upload a PDF file for OCR + analysis. Use this path for scanned PDFs where
 * the client-side pdf.js extraction returned ~no text (likelyScanned).
 */
export async function analyzePdf(file: File | Blob): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.append('file', file, 'document.pdf');
  form.append(
    'options',
    JSON.stringify({ max_clauses: 200, include_top_k: 3 })
  );

  const res = await fetch(`${ML_BASE}/v1/analyze/pdf`, {
    method: 'POST',
    headers: authHeaders(),
    body: form,
    // OCR adds a chunk of time on top of inference; allow longer.
    signal: AbortSignal.timeout(180_000),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({
      error: { code: 'PARSE_ERROR', message: res.statusText },
    }));
    throw new MlServiceError(
      res.status,
      body.error?.code ?? 'UNKNOWN',
      body.error?.message ?? `ML service returned ${res.status}`
    );
  }

  return res.json();
}
