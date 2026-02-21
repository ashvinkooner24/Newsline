import { BiasLean } from '@/types/news';

interface BiasMeterProps {
  leanScore: number; // -100 to +100
  overallLean: BiasLean;
  compact?: boolean;
}

const leanLabels: Record<BiasLean, string> = {
  'far-left': 'Far Left',
  'left': 'Left',
  'center-left': 'Center-Left',
  'center': 'Center',
  'center-right': 'Center-Right',
  'right': 'Right',
  'far-right': 'Far Right',
};

export const BiasMeter = ({ leanScore, overallLean, compact = false }: BiasMeterProps) => {
  const position = ((leanScore + 100) / 200) * 100;

  return (
    <div className={compact ? 'space-y-1' : 'space-y-2'}>
      {!compact && (
        <div className="flex justify-between text-xs font-mono text-muted-foreground">
          <span>Left</span>
          <span>Center</span>
          <span>Right</span>
        </div>
      )}
      <div className="relative h-2 rounded-full bias-gradient opacity-80">
        <div
          className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-foreground border-2 border-background shadow-lg transition-all duration-500"
          style={{ left: `${Math.max(2, Math.min(98, position))}%`, transform: 'translate(-50%, -50%)' }}
        />
      </div>
      <div className={`text-center font-mono ${compact ? 'text-xs' : 'text-sm'} text-muted-foreground`}>
        {leanLabels[overallLean]}
      </div>
    </div>
  );
};
