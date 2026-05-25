import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import { connectDb } from '@/lib/db/mongoose';
import { DocumentModel } from '@/lib/db/models/Document';
import { Analysis } from '@/lib/db/models/Analysis';
import { Clause } from '@/lib/db/models/Clause';
import { analyzeText, MlServiceError } from '@/lib/ml-client';
import { createAnalysisSchema } from '@/lib/validations';
import type { Clause as ClauseDTO } from '@/types';

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json(
      { error: { code: 'UNAUTHORIZED', message: 'Sign in required' } },
      { status: 401 }
    );
  }

  try {
    const body = await req.json();
    const parsed = createAnalysisSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: { code: 'INVALID_INPUT', message: 'documentId is required' } },
        { status: 400 }
      );
    }

    await connectDb();

    const doc = await DocumentModel.findOne({
      _id: parsed.data.documentId,
      userId: session.user.id,
    }).lean();

    if (!doc) {
      return NextResponse.json(
        { error: { code: 'NOT_FOUND', message: 'Document not found' } },
        { status: 404 }
      );
    }

    // Create the analysis record up-front so the client can poll it.
    const analysis = await Analysis.create({
      documentId: doc._id,
      userId: session.user.id,
      status: 'processing',
      startedAt: new Date(),
    });

    // For the scaffold we run synchronously. Once contracts get longer than
    // the Vercel 10s timeout, switch to a job queue or call the ML service
    // directly from the browser using a short-lived JWT.
    try {
      const result = await analyzeText(doc.extractedText);

      // Persist clauses
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

      analysis.status = 'completed';
      analysis.completedAt = new Date();
      analysis.metrics = {
        totalClauses: result.metrics.total_clauses,
        highRiskCount: result.metrics.high_risk_count,
        mediumRiskCount: result.metrics.medium_risk_count,
        avgConfidence: result.metrics.avg_confidence,
      };
      analysis.modelVersions = {
        classifier: result.model_versions.classifier,
        rewriter: result.model_versions.rewriter,
        nerVersion: result.model_versions.ner_version,
      };
      analysis.progress = 100;
      await analysis.save();

      return NextResponse.json({ id: analysis._id.toString() }, { status: 201 });
    } catch (mlErr) {
      analysis.status = 'failed';
      analysis.errorMessage =
        mlErr instanceof MlServiceError ? `${mlErr.code}: ${mlErr.message}` : 'Unknown ML error';
      await analysis.save();

      return NextResponse.json(
        {
          id: analysis._id.toString(),
          error: { code: 'ML_FAILED', message: analysis.errorMessage },
        },
        { status: 502 }
      );
    }
  } catch (err) {
    console.error('[analyses POST] error:', err);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Could not start analysis' } },
      { status: 500 }
    );
  }
}

export async function GET() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json(
      { error: { code: 'UNAUTHORIZED', message: 'Sign in required' } },
      { status: 401 }
    );
  }

  await connectDb();

  const analyses = await Analysis.find({ userId: session.user.id })
    .sort({ startedAt: -1 })
    .limit(50)
    .lean();

  return NextResponse.json({
    analyses: analyses.map((a) => ({
      id: a._id.toString(),
      documentId: a.documentId.toString(),
      status: a.status,
      progress: a.progress,
      startedAt: a.startedAt,
      completedAt: a.completedAt,
      metrics: a.metrics,
    })),
  });
}
