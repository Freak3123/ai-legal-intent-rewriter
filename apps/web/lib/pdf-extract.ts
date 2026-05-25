'use client';

import type { TextItem } from 'pdfjs-dist/types/src/display/api';

// Loaded via dynamic import so Next.js's static bundler doesn't trip on
// pdfjs-dist's module-init code.
let pdfjsPromise: Promise<typeof import('pdfjs-dist')> | null = null;

function loadPdfjs() {
  if (!pdfjsPromise) {
    pdfjsPromise = import('pdfjs-dist').then((mod) => {
      mod.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${mod.version}/build/pdf.worker.min.mjs`;
      return mod;
    });
  }
  return pdfjsPromise;
}

export interface PdfExtractionResult {
  text: string;
  pageCount: number;
  /** True if the PDF appears to be a scan with no embedded text layer. */
  likelyScanned: boolean;
}

/** Threshold below which a multi-page PDF is treated as a probable scan. */
const SCANNED_TEXT_DENSITY = 30; // characters per page

export async function extractPdfText(file: File): Promise<PdfExtractionResult> {
  const { getDocument } = await loadPdfjs();
  const buffer = await file.arrayBuffer();
  const pdf = await getDocument({ data: new Uint8Array(buffer) }).promise;

  const pages: string[] = [];
  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i);
    const content = await page.getTextContent();
    const lines = content.items
      .map((item) => ('str' in item ? (item as TextItem).str : ''))
      .filter(Boolean);
    pages.push(lines.join(' '));
  }

  const text = pages.join('\n\n').trim();
  const likelyScanned = pdf.numPages > 0 && text.length < SCANNED_TEXT_DENSITY * pdf.numPages;

  return { text, pageCount: pdf.numPages, likelyScanned };
}
