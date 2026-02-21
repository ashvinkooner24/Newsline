import { Rating } from '@/types/news';
import { Star } from 'lucide-react';

interface RatingDisplayProps {
  rating: Rating;
}

export const RatingDisplay = ({ rating }: RatingDisplayProps) => {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Star className="w-4 h-4 text-primary" />
        <h3 className="font-mono text-sm font-semibold text-foreground">Community Rating</h3>
      </div>
      <div className="space-y-2">
        <RatingBar label="Accuracy" value={rating.accuracy} />
        <RatingBar label="Fairness" value={rating.fairness} />
        <RatingBar label="Completeness" value={rating.completeness} />
      </div>
      <p className="font-mono text-xs text-muted-foreground text-center">
        {rating.totalRatings} ratings
      </p>
    </div>
  );
};

const RatingBar = ({ label, value }: { label: string; value: number }) => (
  <div className="flex items-center gap-2">
    <span className="font-mono text-xs text-muted-foreground w-24">{label}</span>
    <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
      <div className="h-full bg-primary rounded-full transition-all duration-700" style={{ width: `${(value / 5) * 100}%` }} />
    </div>
    <span className="font-mono text-xs text-foreground w-8 text-right">{value.toFixed(1)}</span>
  </div>
);
