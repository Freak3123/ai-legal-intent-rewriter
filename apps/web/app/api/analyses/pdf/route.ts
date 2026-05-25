import { NextResponse } from 'next/server';
import crypto from 'node:crypto';
import { auth } from '@/auth';
import { connectDb } from '@/lib/db/mongoose';
import { DocumentModel } from '@/lib/db/models/Document';
import { Analysis } from '@/lib/db/models/Analysis';
import { Clause } from '@/lib/db/models/Clause';
import { analyzePdf, MlServiceError } from '@/lib/ml-client';
import type { Clause as ClauseDTO } from '@/types';

export const runtime = 'nodejs';
export const maxDuration = 60;

/**
 * Accept a PDF upload (scanned or digital) and run it through the ML service's
 * /v1/analyze/pdf endpoint. The ML side handles OCR via Tesseract when the
 * text layer is empty; we just persist the result.
 */
export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json(
      { error: { code: 'UNAUTHORIZED', message: 'Sign in required' } },
      { status: 401 }
    );
  }

  const form = await req.formData().catch(() => null);
  if (!form) {
    return NextResponse.json(
      { error: { code: 'INVALID_INPUT', message: 'multipart/form-data body required' } },
      { status: 400 }
    );
  }
  const file = form.get('file');
  if (!(file instanceof File) || !file.name.toLowerCase().endsWith('.pdf')) {
    return NextResponse.json(
      { error: { code: 'INVALID_INPUT', message: 'A .pdf file is required in the `file` field' } },
      { status: 400 }
    );
  }
  if (file.size > 10 * 1024 * 1024) {
    return NextResponse.json(
      { error: { code: 'FILE_TOO_LARGE', message: 'PDF exceeds 10 MB limit' } },
      { status: 413 }
    );
  }

  await connectDb();

  let analysisId: string | null = null;

  try {
    // 1. Forward to ML service for ingestion + analysis
    const result = await analyzePdf(file);

    // 2. Persist Document with the OCR/text-layer output. Hash on extracted text.
    const hash = crypto.createHash('sha256').update(result.clauses.map((c) => c.original_text).join('\n')).digest('hex');
    const doc = await DocumentModel.create({
      userId: session.user.id,
      hash,
      filename: file.name,
      mimeType: 'application/pdf',
      sizeBytes: file.size,
      pageCount: result.page_count,
      extractedText: result.clauses.map((c) => c.original_text).join('\n\n'),
      ingestionMethod: result.ingestion_method,
    });

    // 3. Persist Analysis + Clauses
    const analysis = await Analysis.create({
      documentId: doc._id,
      userId: session.user.id,
      status: 'completed',
      startedAt: new Date(),
      completedAt: new Date(),
      progress: 100,
      metrics: {
        totalClauses: result.metrics.total_clauses,
        highRiskCount: result.metrics.high_risk_count,
        mediumRiskCount: result.metrics.medium_risk_count,
        avgConfidence: result.metrics.avg_confidence,
      },
      modelVersions: {
        classifier: result.model_versions.classifier,
        rewriter: result.model_versions.rewriter,
        nerVersion: result.model_versions.ner_version,
      },
    });
    analysisId = analysis._id.toString();

    if (result.clauses.length > 0) {
      await Clause.insertMany(
        result.clauses.map((c: ClauseDTO) => ({
          analysisId: analysis._id,
          documentId: doc._id,
          ordinal: c.ordinal,
          originalText: c.original_text,
          charSpan: c.char_span,
          classification: {
            label: c.classification.label,
            confidence: c.classification.confidence,
            topK: c.classification.top_k,
          },
          entities: c.entities,
          rewrite: {
            text: c.rewrite.text,
            readabilityScore: c.rewrite.readability_score,
            method: c.rewrite.method,
          },
          risk: c.risk,
        }))
      );
    }

    return NextResponse.json({ id: analysisId }, { status: 201 });
  } catch (err) {
    console.error('[analyses/pdf POST] error:', err);
    if (err instanceof MlServiceError) {
      return NextResponse.json(
        { error: { code: err.code, message: err.message } },
        { status: 502 }
      );
    }
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Could not analyse PDF' } },
      { status: 500 }
    );
  }
}
