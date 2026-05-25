'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { UploadDropzone } from '@/components/upload-dropzone';
import { extractPdfText } from '@/lib/pdf-extract';

type Source = 'pdf' | 'paste' | 'scanned-pdf';

const SAMPLE_TEXT = `1. Term and Termination. This Agreement shall commence on the Effective Date and continue for an initial term of one (1) year, automatically renewing for successive one-year periods unless either party provides written notice of termination at least thirty (30) days prior to the end of the then-current term.

2. Liability. In no event shall either party be liable to the other for any indirect, incidental, special, consequential, or punitive damages, including without limitation loss of profits, data, or use, arising out of or in connection with this Agreement, even if such party has been advised of the possibility of such damages.

3. Indemnification. The Customer agrees to indemnify, defend, and hold harmless the Company from and against any and all claims, damages, liabilities, costs, and expenses (including reasonable attorneys' fees) arising out of or related to the Customer's use of the services in violation of this Agreement.

4. Confidentiality. Each party acknowledges that it may receive Confidential Information from the other party. The receiving party shall (a) maintain the confidentiality of the Confidential Information using at least the same degree of care it uses to protect its own confidential information of like nature, but in no event less than reasonable care, and (b) not disclose the Confidential Information to any third party without the prior written consent of the disclosing party.

5. Payment Terms. Customer shall pay all undisputed invoices within thirty (30) days of receipt. Late payments shall accrue interest at the lower of one and one-half percent (1.5%) per month or the maximum rate permitted by law.`;

export default function UploadPage() {
  const router = useRouter();
  const [text, setText] = useState('');
  const [filename, setFilename] = useState('Pasted text');
  const [pageCount, setPageCount] = useState(0);
  const [sizeBytes, setSizeBytes] = useState(0);
  const [source, setSource] = useState<Source>('paste');
  const [scannedFile, setScannedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [extracting, setExtracting] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  async function onPdfDropped(file: File) {
    setError(null);
    setExtracting(true);
    try {
      const { text: extracted, pageCount: pages, likelyScanned } = await extractPdfText(file);
      if (likelyScanned) {
        // Scanned PDF — defer text extraction to the ML service's OCR pipeline.
        setText('');
        setFilename(file.name);
        setPageCount(pages);
        setSizeBytes(file.size);
        setScannedFile(file);
        setSource('scanned-pdf');
        return;
      }
      setText(extracted);
      setFilename(file.name);
      setPageCount(pages);
      setSizeBytes(file.size);
      setScannedFile(null);
      setSource('pdf');
    } catch (err) {
      console.error('PDF extraction failed:', err);
      setError(err instanceof Error ? `Could not read PDF: ${err.message}` : 'Could not read PDF');
    } finally {
      setExtracting(false);
    }
  }

  async function onAnalyse() {
    if (source === 'scanned-pdf') {
      return onAnalyseScanned();
    }
    if (!text.trim()) {
      setError('Please paste some legal text or upload a document first.');
      return;
    }
    setError(null);
    setSubmitting(true);

    const isPdf = source === 'pdf';
    try {
      // 1. Save the document
      const docRes = await fetch('/api/documents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename,
          mimeType: isPdf ? 'application/pdf' : 'text/plain',
          sizeBytes: isPdf ? sizeBytes : new Blob([text]).size,
          pageCount: isPdf ? pageCount : 0,
          extractedText: text,
          ingestionMethod: isPdf ? 'pdfjs' : 'text-direct',
        }),
      });

      if (!docRes.ok) {
        const body = await docRes.json().catch(() => null);
        throw new Error(body?.error?.message ?? 'Failed to save document');
      }
      const { id: documentId } = await docRes.json();

      // 2. Kick off the analysis
      const aRes = await fetch('/api/analyses', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ documentId }),
      });

      if (!aRes.ok && aRes.status !== 502) {
        const body = await aRes.json().catch(() => null);
        throw new Error(body?.error?.message ?? 'Analysis failed');
      }

      const { id: analysisId } = await aRes.json();
      router.push(`/dashboard/${analysisId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
      setSubmitting(false);
    }
  }

  async function onAnalyseScanned() {
    if (!scannedFile) {
      setError('No scanned PDF selected.');
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const form = new FormData();
      form.append('file', scannedFile);

      const aRes = await fetch('/api/analyses/pdf', {
        method: 'POST',
        body: form,
      });

      if (!aRes.ok) {
        const body = await aRes.json().catch(() => null);
        throw new Error(body?.error?.message ?? 'OCR analysis failed');
      }

      const { id: analysisId } = await aRes.json();
      router.push(`/dashboard/${analysisId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
      setSubmitting(false);
    }
  }

  function loadSample() {
    setText(SAMPLE_TEXT);
    setFilename('Sample contract');
    setPageCount(0);
    setSizeBytes(0);
    setSource('paste');
    setError(null);
  }

  return (
    <>
      <main className="container flex-1 space-y-8 py-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Upload a document</h1>
          <p className="text-muted-foreground">
            Drop a PDF or paste legal text directly. We&rsquo;ll analyse it clause by clause.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>PDF upload</CardTitle>
            <CardDescription>
              Drag and drop a PDF. We&rsquo;ll extract the text in your browser before sending it
              for analysis. Scanned PDFs (no text layer) need OCR — coming later.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <UploadDropzone onFile={onPdfDropped} />
            {extracting && (
              <p className="mt-2 text-sm text-muted-foreground">Reading PDF…</p>
            )}
            {source === 'pdf' && !extracting && text && (
              <p className="mt-2 text-sm text-muted-foreground">
                Extracted {text.length.toLocaleString()} characters from {pageCount} page
                {pageCount === 1 ? '' : 's'}.
              </p>
            )}
            {source === 'scanned-pdf' && !extracting && (
              <p className="mt-2 text-sm text-muted-foreground">
                Scanned PDF detected ({pageCount} page{pageCount === 1 ? '' : 's'}). OCR will
                run server-side when you press analyse — this can take a minute.
              </p>
            )}
            {source === 'scanned-pdf' && (
              <div className="mt-4">
                <Button onClick={onAnalyseScanned} disabled={submitting}>
                  {submitting ? 'Running OCR + analysing…' : 'Run OCR and analyse'}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Paste text</CardTitle>
            <CardDescription>
              Copy from any contract or terms-of-service document and paste below.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="legal-text">Document text</Label>
              <textarea
                id="legal-text"
                value={text}
                onChange={(e) => {
                  setText(e.target.value);
                  if (source === 'pdf') {
                    // User edited extracted text — treat it as pasted from now on so we
                    // don't claim the bytes are still a faithful copy of the PDF.
                    setSource('paste');
                    setFilename('Pasted text');
                    setPageCount(0);
                    setSizeBytes(0);
                  }
                }}
                placeholder="Paste your legal document here…"
                rows={12}
                className="w-full rounded-md border border-input bg-background p-3 font-mono text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <div className="flex flex-wrap gap-3">
              <Button onClick={onAnalyse} disabled={submitting || !text.trim()}>
                {submitting ? 'Analysing…' : 'Analyse document'}
              </Button>
              <Button type="button" variant="outline" onClick={loadSample} disabled={submitting}>
                Load sample
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    </>
  );
}
