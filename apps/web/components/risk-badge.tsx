import { cn } from '@/lib/utils';
import type { RiskLevel } from '@/types';

interface RiskBadgeProps {
  level: RiskLevel;
  score?: number;
  className?: string;
}

const STYLES: Record<RiskLevel, string> = {
  low: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300',
  medium: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300',
  high: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
};

const LABELS: Record<RiskLevel, string> = {
  low: 'Low risk',
  medium: 'Medium risk',
  high: 'High risk',
};

export function RiskBadge({ level, score, className }: RiskBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
        STYLES[level],
        className
      )}
    >
      <span
        className={cn('h-1.5 w-1.5 rounded-full', {
          'bg-emerald-500': level === 'low',
          'bg-amber-500': level === 'medium',
          'bg-red-500': level === 'high',
        })}
      />
      {LABELS[level]}
      {typeof score === 'number' && (
        <span className="opacity-70">· {Math.round(score * 100)}%</span>
      )}
    </span>
  );
}
