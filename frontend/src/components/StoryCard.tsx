import { StorySummary } from '@/types/news';
import { BiasMeter } from './BiasMeter';
import { CredibilityGauge } from './CredibilityGauge';
import { Link } from 'react-router-dom';
import { Clock, FileText } from 'lucide-react';
import { getArticleCount, getSourceCount } from '@/lib/storyMetrics';

interface StoryCardProps {
  story: StorySummary;
  index: number;
}

export const StoryCard = ({ story, index }: StoryCardProps) => {
  const timeAgo = getTimeAgo(story.updatedAt);
  const articleCount = getArticleCount(story);
  const sourceCount = getSourceCount(story);

  return (
    <Link
      to={`/topic/${story.slug}`}
      className="block card-hover"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      <article className="animate-fade-in opacity-0 border border-border bg-card p-5 h-full flex flex-col">
        <div className="flex items-center gap-3 mb-2">
          <span className="font-mono text-xs text-primary tracking-widest uppercase">
            {story.category}
          </span>
          {story.isBreaking && (
            <span className="font-mono text-xs font-bold text-destructive">● Breaking</span>
          )}
          <span className="flex items-center gap-1 text-xs text-muted-foreground font-mono ml-auto">
            <Clock className="w-3 h-3" />
            {timeAgo}
          </span>
        </div>

        <h3 className="font-display text-lg font-semibold text-foreground leading-snug mb-2">
          {story.headline}
        </h3>

        <p className="text-sm text-muted-foreground leading-relaxed mb-4 flex-1 line-clamp-3">
          {story.summary}
        </p>

        <div className="space-y-3 pt-3 border-t border-border">
          <BiasMeter leanScore={story.biasAnalysis.leanScore} overallLean={story.biasAnalysis.overallLean} compact />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1 text-xs text-muted-foreground font-mono">
              <FileText className="w-3 h-3" />
              {articleCount} articles · {sourceCount} sources
            </div>
            <CredibilityGauge credibility={story.credibility} compact />
          </div>
        </div>
      </article>
    </Link>
  );
};

function getTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return 'Just now';
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}
