import Link from 'next/link';
import { auth } from '@/auth';
import { connectDb } from '@/lib/db/mongoose';
import { Analysis } from '@/lib/db/models/Analysis';
import { DocumentModel } from '@/lib/db/models/Document';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { formatDate } from '@/lib/utils';

export default async function DashboardPage() {
  const session = await auth();
  if (!session?.user?.id) return null; // middleware handles redirect

  await connectDb();

  const analyses = await Analysis.find({ userId: session.user.id })
    .sort({ startedAt: -1 })
    .limit(50)
    .lean();

  const docIds = analyses.map((a) => a.documentId);
  const docs = await DocumentModel.find({ _id: { $in: docIds } })
    .select('filename')
    .lean();
  const docFilenames = new Map(docs.map((d) => [d._id.toString(), d.filename]));

  return (
    <>
      <main className="container flex-1 py-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Your analyses</h1>
            <p className="text-muted-foreground">All the documents you&rsquo;ve analysed.</p>
          </div>
          <Button asChild>
            <Link href="/upload">Upload new</Link>
          </Button>
        </div>

        {analyses.length === 0 ? (
          <Card>
            <CardContent className="py-16 text-center">
              <p className="text-muted-foreground">
                Nothing here yet.{' '}
                <Link href="/upload" className="font-medium text-primary hover:underline">
                  Upload your first document
                </Link>{' '}
                to get started.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4">
            {analyses.map((a) => (
              <Link key={a._id.toString()} href={`/dashboard/${a._id}`} className="block">
                <Card className="transition-colors hover:border-primary/40">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between gap-4">
                      <CardTitle className="text-base">
                        {docFilenames.get(a.documentId.toString()) ?? 'Untitled document'}
                      </CardTitle>
                      <StatusPill status={a.status} />
                    </div>
                  </CardHeader>
                  <CardContent className="text-sm text-muted-foreground">
                    <div className="flex flex-wrap items-center gap-4">
                      <span>{a.metrics?.totalClauses ?? 0} clauses</span>
                      {(a.metrics?.highRiskCount ?? 0) > 0 && (
                        <span className="text-risk-high">
                          {a.metrics?.highRiskCount} high-risk
                        </span>
                      )}
                      {(a.metrics?.mediumRiskCount ?? 0) > 0 && (
                        <span className="text-risk-medium">
                          {a.metrics?.mediumRiskCount} medium-risk
                        </span>
                      )}
                      <span className="ml-auto">{formatDate(a.startedAt)}</span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </main>
    </>
  );
}

function StatusPill({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
    processing: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
    failed: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
    queued: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
  };
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${styles[status] ?? styles.queued}`}>
      {status}
    </span>
  );
}
