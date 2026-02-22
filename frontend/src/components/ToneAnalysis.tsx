import { ToneType } from '@/types/news';
import { Brain, Heart } from 'lucide-react';

interface ToneAnalysisProps {
  tone: ToneType | string;
  toneScore: { emotional: number; logical: number };
  sourceName: string;
}

export const ToneAnalysis = ({ tone, toneScore, sourceName }: ToneAnalysisProps) => {
  return (
    <div className="space-y-4">
      <h3 className="font-display text-lg font-semibold text-foreground">Tone & Sentiment</h3>
      <p className="text-sm text-muted-foreground">
        Analysis of the rhetorical approach used by {sourceName} in this article.
      </p>

      <div className="space-y-3">
        {/* Spectrum bar */}
        <div className="flex items-center gap-3">
          <Heart className="w-4 h-4 text-destructive flex-shrink-0" />
          <div className="flex-1 h-3 bg-muted rounded-full overflow-hidden flex">
            <div
              className="h-full bg-destructive/70 transition-all duration-700"
              style={{ width: `${toneScore.emotional}%` }}
            />
            <div
              className="h-full bg-primary/70 transition-all duration-700"
              style={{ width: `${toneScore.logical}%` }}
            />
          </div>
          <Brain className="w-4 h-4 text-primary flex-shrink-0" />
        </div>

        <div className="flex justify-between font-mono text-xs text-muted-foreground">
          <span>Emotional {toneScore.emotional}%</span>
          <span>Analytical {toneScore.logical}%</span>
        </div>

        <div className="bg-accent/50 p-3 text-sm">
          <span className="font-mono text-xs text-primary uppercase tracking-wider">Tone: </span>
          <span className="text-foreground capitalize font-semibold">{tone}</span>
          <p className="text-muted-foreground text-xs mt-1">
            {toneScore.emotional > 60
              ? 'This article relies heavily on emotional language and appeals. Read with awareness of rhetorical persuasion.'
              : toneScore.logical > 70
              ? 'This article uses primarily data-driven, analytical language with minimal emotional appeals.'
              : 'This article balances emotional and analytical elements in its presentation.'}
          </p>
        </div>
      </div>
    </div>
  );
};
