import { CredibilityAssessment } from '@/types/news';

interface CredibilityGaugeProps {
  credibility: CredibilityAssessment;
  compact?: boolean;
}

export const CredibilityGauge = ({ credibility, compact = false }: CredibilityGaugeProps) => {
  const colorClass =
    credibility.label === 'High' ? 'text-credibility-high' :
    credibility.label === 'Medium' ? 'text-credibility-medium' :
    'text-credibility-low';

  const bgClass =
    credibility.label === 'High' ? 'bg-credibility-high' :
    credibility.label === 'Medium' ? 'bg-credibility-medium' :
    'bg-credibility-low';

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${bgClass}`} />
        <span className={`text-xs font-mono ${colorClass}`}>
          {credibility.score}%
        </span>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground font-mono">Credibility</span>
        <span className={`text-lg font-bold font-mono ${colorClass}`}>
          {credibility.score}%
        </span>
      </div>
      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${bgClass} transition-all duration-700`}
          style={{ width: `${credibility.score}%` }}
        />
      </div>
      <div className="grid grid-cols-3 gap-2 text-xs font-mono text-muted-foreground">
        <div>
          <div className="text-foreground">{credibility.articleCount}</div>
          <div>Sources</div>
        </div>
        <div>
          <div className="text-foreground">{credibility.avgSourceCredibility}%</div>
          <div>Avg Quality</div>
        </div>
        <div>
          <div className="text-foreground">{credibility.sourceAgreement}%</div>
          <div>Agreement</div>
        </div>
      </div>
    </div>
  );
};
