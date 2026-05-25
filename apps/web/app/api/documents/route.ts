import { NextResponse } from 'next/server';
import crypto from 'node:crypto';
import { auth } from '@/auth';
import { connectDb } from '@/lib/db/mongoose';
import { DocumentModel } from '@/lib/db/models/Document';
import { createDocumentSchema } from '@/lib/validations';

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
    const parsed = createDocumentSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: { code: 'INVALID_INPUT', message: 'Invalid document data', details: parsed.error.flatten() } },
        { status: 400 }
      );
    }

    await connectDb();

    const hash = crypto.createHash('sha256').update(parsed.data.extractedText).digest('hex');

    const doc = await DocumentModel.create({
      userId: session.user.id,
      hash,
      ...parsed.data,
    });

    return NextResponse.json({ id: doc._id.toString() }, { status: 201 });
  } catch (err) {
    console.error('[documents POST] error:', err);
    return NextResponse.json(
      { error: { code: 'INTERNAL_ERROR', message: 'Could not save document' } },
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

  const docs = await DocumentModel.find({ userId: session.user.id })
    .sort({ uploadedAt: -1 })
    .limit(50)
    .select('-extractedText') // skip the bulky field on list view
    .lean();

  return NextResponse.json({
    documents: docs.map((d) => ({
      id: d._id.toString(),
      filename: d.filename,
      pageCount: d.pageCount,
      uploadedAt: d.uploadedAt,
      ingestionMethod: d.ingestionMethod,
      sizeBytes: d.sizeBytes,
    })),
  });
}
