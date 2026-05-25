import { notFound } from 'next/navigation';
import Link from 'next/link';
import { auth } from '@/auth';
import { connectDb } from '@/lib/db/mongoose';
import { Analysis } from '@/lib/db/models/Analysis';
import { Clause } from '@/lib/db/models/Clause';
import { DocumentModel } from '@/lib/db/models/Document';
import { ClauseCard } from '@/components/clause-card';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { formatDate } from '@/lib/utils';
import type { ClassificationLabel, Entity, EntityType, RiskLevel } from '@/types';

// Mongoose's lean() returns nullable variants of every non-required schema
// field. Map those into the strict shapes ClauseCard expects, with safe
// defaults so a partial document never crashes the render.
type LeanClause = {
  _id: { toString: () => string };
  ordinal?: number | null;
  originalText?: string | null;
  classification?: {
    label?: string | null;
    confidence?: number | null;
    topK?: { label?: string | null; score?: number | null }[] | null;
  } | null;
  entities?:
    | {
        text?: string | null;
        type?: EntityType | null;
        start?: number | null;
        end?: number | null;
      }[]
    | null;
  rewrite?: {
    text?: string | null;
    readabilityScore?: number | null;
    method?: 'model' | 'template-fallback' | null;
  } | null;
  risk?: {
    level?: RiskLevel | null;
    score?: number | null;
    triggers?: string[] | null;
  } | null;
};

function toClauseDTO(c: LeanClause) {
  return {
    id: c._id.toString(),
    ordinal: c.ordinal ?? 0,
    originalText: c.originalText ?? '',
    classification: {
      label: (c.classification?.label ?? 'OTHER') as ClassificationLabel,
      confidence: c.classification?.confidence ?? 0,
      topK: (c.classification?.topK ?? []).map((t) => ({
        label: (t.label ?? 'OTHER') as ClassificationLabel,
        score: t.score ?? 0,
      })),
    },
    entities: (c.entities ?? []).map<Entity>((e) => ({
      text: e.text ?? '',
      type: (e.type ?? 'CONDITION') as EntityType,
      start: e.start ?? 0,
      end: e.end ?? 0,
    })),
    rewrite: {
      text: c.rewrite?.text ?? '',
      readabilityScore: c.rewrite?.readabilityScore ?? undefined,
      method: c.rewrite?.method ?? 'template-fallback',
    },
    risk: {
      level: (c.risk?.level ?? 'low') as RiskLevel,
      score: c.risk?.score ?? 0,
      triggers: c.risk?.triggers ?? [],
    },
  };
}

export default async function AnalysisDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await auth();
  if (!session?.user?.id) return null;

  const { id } = await params;
  await connectDb();

  const analysis = await Analysis.findOne({ _id: id, userId: session.user.id }).lean();
  if (!analysis) notFound();

  const [doc, clauses] = await Promise.all([
    DocumentModel.findById(analysis.documentId).select('filename pageCount uploadedAt').lean(),
    Clause.find({ analysisId: id }).sort({ ordinal: 1 }).lean(),
  ]);

  return (
    <>
      <main className="container flex-1 space-y-8 py-8">
        <div>
          <Link href="/dashboard" className="text-sm text-muted-foreground hover:underline">
            ← Back to dashboard
          </Link>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            {doc?.filename ?? 'Analysis'}
          </h1>
          <p className="text-muted-foreground">
            {doc?.pageCount ?? 0} pages · analysed {formatDate(analysis.startedAt)}
          </p>
        </div>

        {analysis.status === 'failed' && (
          <Card className="border-destructive">
            <CardContent className="py-4 text-sm">
              <p className="font-medium text-destructive">Analysis failed</p>
              <p className="mt-1 text-muted-foreground">
                {analysis.errorMessage ?? 'Unknown error'}
              </p>
            </CardContent>
          </Card>
        )}

        {analysis.status === 'completed' && (
          <>
            <div className="grid gap-4 sm:grid-cols-4">
              <SummaryStat label="Clauses" value={analysis.metrics?.totalClauses ?? 0} />
              <SummaryStat
                label="High risk"
                value={analysis.metrics?.highRiskCount ?? 0}
                tone="high"
              />
              <SummaryStat
                label="Medium risk"
                value={analysis.metrics?.mediumRiskCount ?? 0}
                tone="medium"
              />
              <SummaryStat
                label="Avg confidence"
                value={`${Math.round((analysis.metrics?.avgConfidence ?? 0) * 100)}%`}
              />
            </div>

            <div className="space-y-4">
              {clauses.map((raw) => {
                const c = toClauseDTO(raw as LeanClause);
                return (
                  <ClauseCard
                    key={c.id}
                    ordinal={c.ordinal}
                    originalText={c.originalText}
                    classification={c.classification}
                    rewrite={c.rewrite}
                    risk={c.risk}
                    entities={c.entities}
                  />
                );
              })}
            </div>
          </>
        )}

        {analysis.status === 'processing' && (
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-lg">Analysing your document…</p>
              <p className="mt-2 text-sm text-muted-foreground">
                This usually takes 5&ndash;30 seconds. Refresh the page in a moment.
              </p>
              <Button asChild variant="outline" className="mt-4">
                <Link href={`/dashboard/${id}`}>Refresh</Link>
              </Button>
            </CardContent>
          </Card>
        )}
      </main>
    </>
  );
}

function SummaryStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string | number;
  tone?: 'high' | 'medium';
}) {
  const toneClass =
    tone === 'high' ? 'text-risk-high' : tone === 'medium' ? 'text-risk-medium' : '';
  return (
    <Card>
      <CardContent className="py-4">
        <p className="text-xs uppercase tracking-wider text-muted-foreground">{label}</p>
        <p className={`mt-1 text-2xl font-bold ${toneClass}`}>{value}</p>
      </CardContent>
    </Card>
  );
}
