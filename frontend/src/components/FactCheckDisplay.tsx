import { FactCheck } from '@/types/news';
import { CheckCircle, AlertTriangle, XCircle, HelpCircle, AlertCircle } from 'lucide-react';

interface FactCheckDisplayProps {
  factCheck: FactCheck;
}

const verdictConfig = {
  'verified': { icon: CheckCircle, label: 'Verified', color: 'text-credibility-high', bg: 'bg-credibility-high/10' },
  'mostly-true': { icon: CheckCircle, label: 'Mostly True', color: 'text-credibility-high', bg: 'bg-credibility-high/10' },
  'mixed': { icon: AlertTriangle, label: 'Mixed', color: 'text-credibility-medium', bg: 'bg-credibility-medium/10' },
  'misleading': { icon: XCircle, label: 'Misleading', color: 'text-credibility-low', bg: 'bg-credibility-low/10' },
  'unverified': { icon: HelpCircle, label: 'Unverified', color: 'text-muted-foreground', bg: 'bg-muted' },
};

export const FactCheckDisplay = ({ factCheck }: FactCheckDisplayProps) => {
  const config = verdictConfig[factCheck.verdict];
  const Icon = config.icon;

  return (
    <div className="space-y-4">
      <h3 className="font-display text-lg font-semibold text-foreground">Fact Check</h3>

      <div className={`flex items-center gap-3 p-3 ${config.bg}`}>
        <Icon className={`w-5 h-5 ${config.color}`} />
        <div>
          <span className={`font-mono text-sm font-bold ${config.color}`}>{config.label}</span>
          <p className="text-sm text-secondary-foreground mt-1">{factCheck.details}</p>
        </div>
      </div>

      {factCheck.missingContext.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-credibility-medium" />
            <span className="font-mono text-xs font-semibold text-foreground uppercase tracking-wider">Missing Context</span>
          </div>
          <ul className="space-y-1.5 pl-6">
            {factCheck.missingContext.map((ctx, i) => (
              <li key={i} className="text-sm text-muted-foreground list-disc">{ctx}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};
