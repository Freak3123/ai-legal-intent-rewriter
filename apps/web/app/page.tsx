import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { auth } from '@/auth';

export default async function HomePage() {
  const session = await auth();

  return (
    <main className="container flex flex-1 flex-col items-center justify-center gap-8 py-16 text-center">
      <div className="max-w-3xl space-y-6">
        <p className="text-sm font-medium uppercase tracking-wider text-muted-foreground">
          BTech CSE (AIML) Final Year Project
        </p>
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
          Understand any legal document in plain English
        </h1>
        <p className="text-lg text-muted-foreground sm:text-xl">
          Upload a contract, terms of service, or rental agreement. We&rsquo;ll break it down
          clause by clause, rewrite the dense legal language, and flag the bits you should
          actually pay attention to.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          {session?.user ? (
            <>
              <Button asChild size="lg">
                <Link href="/upload">Upload a document</Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="/dashboard">Go to dashboard</Link>
              </Button>
            </>
          ) : (
            <>
              <Button asChild size="lg">
                <Link href="/signup">Get started</Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="/login">Sign in</Link>
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="mt-12 grid w-full max-w-4xl gap-6 sm:grid-cols-3">
        <FeatureCard
          title="Clause classification"
          body="Each section is sorted into categories like Termination, Liability, or Payment."
        />
        <FeatureCard
          title="Plain-English rewrite"
          body="A simplified version of every clause, side-by-side with the original."
        />
        <FeatureCard
          title="Risk flags"
          body="Automatic and unilateral terms get highlighted so you don't miss them."
        />
      </div>
    </main>
  );
}

function FeatureCard({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border bg-card p-6 text-left shadow-sm">
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-muted-foreground">{body}</p>
    </div>
  );
}
