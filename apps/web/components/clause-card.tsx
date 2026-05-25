import { Card, CardContent } from '@/components/ui/card';
import { RiskBadge } from '@/components/risk-badge';
import type { ClassificationLabel, Entity, RiskLevel } from '@/types';
import { cn } from '@/lib/utils';

interface ClauseCardProps {
  ordinal: number;
  originalText: string;
  classification: {
    label: string;
    confidence: number;
    topK?: { label: string; score: number }[];
  };
  rewrite: {
    text: string;
    readabilityScore?: number;
    method: string;
  };
  risk: {
    level: RiskLevel;
    score: number;
    triggers: string[];
  };
  entities: Entity[];
}

const ENTITY_STYLES: Record<string, string> = {
  DATE: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  AMOUNT: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  PARTY: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
  RIGHT: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-300',
  OBLIGATION: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
  CONDITION: 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300',
};

export function ClauseCard({
  ordinal,
  originalText,
  classification,
  rewrite,
  risk,
  entities,
}: ClauseCardProps) {
  return (
    <Card className={cn(risk.level === 'high' && 'border-red-300 dark:border-red-900')}>
      <CardContent className="space-y-4 py-5">
        {/* Header: ordinal + classification + risk */}
        <div className="flex flex-wrap items-center gap-3">
          <span className="text-sm font-medium text-muted-foreground">
            Clause {ordinal + 1}
          </span>
          <span className="rounded-md bg-secondary px-2 py-0.5 text-xs font-medium uppercase tracking-wide text-secondary-foreground">
            {classification.label}
            <span className="ml-1 opacity-60">
              · {Math.round(classification.confidence * 100)}%
            </span>
          </span>
          <RiskBadge level={risk.level} score={risk.score} className="ml-auto" />
        </div>

        {/* Side-by-side: original vs rewrite */}
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Original
            </p>
            <p className="rounded-md bg-muted/50 p-3 text-sm leading-relaxed">{originalText}</p>
          </div>
          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Plain English
              {rewrite.method === 'template-fallback' && (
                <span className="ml-1 italic opacity-70">(template)</span>
              )}
            </p>
            <p className="rounded-md bg-primary/5 p-3 text-sm leading-relaxed">{rewrite.text}</p>
          </div>
        </div>

        {/* Risk triggers */}
        {risk.triggers.length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground">Why flagged:</span>
            {risk.triggers.map((t) => (
              <span
                key={t}
                className="rounded-md bg-red-50 px-2 py-0.5 text-xs text-red-800 dark:bg-red-900/20 dark:text-red-300"
              >
                {t}
              </span>
            ))}
          </div>
        )}

        {/* Entities */}
        {entities.length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-muted-foreground">Entities:</span>
            {entities.map((e, i) => (
              <span
                key={`${e.text}-${i}`}
                className={cn(
                  'rounded-md px-2 py-0.5 text-xs',
                  ENTITY_STYLES[e.type] ?? ENTITY_STYLES.CONDITION
                )}
                title={e.type}
              >
                {e.text}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
