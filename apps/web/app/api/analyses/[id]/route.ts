import { NextResponse } from 'next/server';
import { auth } from '@/auth';
import { connectDb } from '@/lib/db/mongoose';
import { Analysis } from '@/lib/db/models/Analysis';
import { Clause } from '@/lib/db/models/Clause';
import { DocumentModel } from '@/lib/db/models/Document';

export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json(
      { error: { code: 'UNAUTHORIZED', message: 'Sign in required' } },
      { status: 401 }
    );
  }

  const { id } = await params;
  await connectDb();

  const analysis = await Analysis.findOne({ _id: id, userId: session.user.id }).lean();
  if (!analysis) {
    return NextResponse.json(
      { error: { code: 'NOT_FOUND', message: 'Analysis not found' } },
      { status: 404 }
    );
  }

  const [doc, clauses] = await Promise.all([
    DocumentModel.findById(analysis.documentId).select('filename pageCount uploadedAt').lean(),
    Clause.find({ analysisId: id }).sort({ ordinal: 1 }).lean(),
  ]);

  return NextResponse.json({
    id: analysis._id.toString(),
    documentId: analysis.documentId.toString(),
    document: doc
      ? { filename: doc.filename, pageCount: doc.pageCount, uploadedAt: doc.uploadedAt }
      : null,
    status: analysis.status,
    progress: analysis.progress,
    startedAt: analysis.startedAt,
    completedAt: analysis.completedAt,
    errorMessage: analysis.errorMessage,
    metrics: analysis.metrics,
    modelVersions: analysis.modelVersions,
    clauses: clauses.map((c) => ({
      id: c._id.toString(),
      ordinal: c.ordinal,
      originalText: c.originalText,
      classification: c.classification,
      entities: c.entities,
      rewrite: c.rewrite,
      risk: c.risk,
    })),
  });
}
