import { Article } from '@/types/news';
import { Link } from 'react-router-dom';

interface SourceListProps {
  articles: Article[];
  topicSlug?: string;
}

const biasColors: Record<string, string> = {
  'far-left': 'text-bias-left', 'left': 'text-bias-left', 'center-left': 'text-bias-left',
  'center': 'text-bias-center',
  'center-right': 'text-bias-right', 'right': 'text-bias-right', 'far-right': 'text-bias-right',
};

export const SourceList = ({ articles, topicSlug }: SourceListProps) => {
  return (
    <div className="space-y-0 divide-y divide-border border border-border">
      {articles.map((article) => (
        <div key={article.id} className="p-4 bg-card hover:bg-accent/30 transition-colors">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <Link to={`/source/${article.source.id}`} className="font-mono text-xs font-semibold text-primary hover:underline">
                  {article.source.name}
                </Link>
                <span className={`font-mono text-xs ${biasColors[article.source.biasLean] || 'text-muted-foreground'}`}>
                  {article.source.biasLean}
                </span>
                <span className="font-mono text-xs text-muted-foreground">· {article.source.credibilityScore}%</span>
                {article.tone && <span className="font-mono text-xs text-muted-foreground">· {article.tone}</span>}
              </div>
              {topicSlug ? (
                <Link to={`/topic/${topicSlug}/article/${article.id}`} className="text-sm font-semibold text-foreground hover:text-primary transition-colors leading-snug block">
                  {article.title}
                </Link>
              ) : (
                <h4 className="text-sm font-semibold text-foreground leading-snug">{article.title}</h4>
              )}
              <p className="text-xs text-muted-foreground mt-1">{article.excerpt}</p>
            </div>
            <span className="font-mono text-xs text-muted-foreground whitespace-nowrap">{article.publishedAt}</span>
          </div>
        </div>
      ))}
    </div>
  );
};
