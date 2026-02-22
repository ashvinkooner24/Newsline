import { useParams, Link } from 'react-router-dom';
import { useState, useEffect, useMemo } from 'react';
import { getTopics, mockSourceProfiles } from '@/api/newsApi';
import { TopicSummary, SourceProfile } from '@/types/news';
import { BiasMeter } from '@/components/BiasMeter';
import { HeaderBar } from '@/components/HeaderBar';
import { ExternalLink, FileText } from 'lucide-react';

const SourceProfilePage = () => {
  const { sourceId } = useParams();
  const [topics, setTopics] = useState<TopicSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTopics()
      .then(data => setTopics(data))
      .catch(err => console.error('[SourceProfile] Failed to load topics:', err))
      .finally(() => setLoading(false));
  }, []);

  const profile = mockSourceProfiles.find(p => p.source.id === sourceId);

  const sourceArticles = useMemo(
    () => topics.flatMap(t => t.articles.filter(a => a.source.id === sourceId)),
    [topics, sourceId]
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <span className="font-mono text-muted-foreground">Loading...</span>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <h2 className="font-display text-2xl text-foreground">Source not found</h2>
          <Link to="/" className="text-primary font-mono text-sm hover:underline">← Back to The Newsline</Link>
        </div>
      </div>
    );
  }

  const biasLeanToScore: Record<string, number> = {
    'far-left': -80, 'left': -50, 'center-left': -25, 'center': 0,
    'center-right': 25, 'right': 50, 'far-right': 80,
  };

  return (
    <div className="min-h-screen bg-background">
      <HeaderBar backLink="/" backLabel="The Newsline" />

      <main className="container max-w-4xl mx-auto px-4 py-8">
        <div className="animate-fade-in opacity-0">
          <div className="border border-border bg-card p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="font-display text-3xl font-bold text-foreground">{profile.source.name}</h1>
                <div className="flex items-center gap-3 mt-2">
                  <span className="font-mono text-sm text-muted-foreground">{profile.source.country}</span>
                  <a href={profile.source.url} target="_blank" rel="noopener noreferrer" className="font-mono text-sm text-primary hover:underline flex items-center gap-1">
                    {profile.source.url} <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 border-t border-border pt-4">
              <div><span className="font-mono text-xs text-muted-foreground">Total Articles</span><div className="font-mono text-lg font-bold text-foreground">{profile.totalArticles}</div></div>
              <div><span className="font-mono text-xs text-muted-foreground">Avg Credibility</span><div className="font-mono text-lg font-bold text-foreground">{profile.avgCredibility}%</div></div>
              <div><span className="font-mono text-xs text-muted-foreground">Bias Lean</span><div className="font-mono text-lg font-bold text-foreground capitalize">{profile.source.biasLean}</div></div>
              <div><span className="font-mono text-xs text-muted-foreground">Top Topics</span><div className="font-mono text-sm text-foreground">{profile.topTopics.slice(0, 2).join(', ')}</div></div>
            </div>
          </div>

          <div className="border border-border bg-card p-6 mb-6">
            <h2 className="font-display text-xl font-semibold text-foreground mb-4">Bias Profile</h2>
            <BiasMeter leanScore={biasLeanToScore[profile.source.biasLean] || 0} overallLean={profile.source.biasLean} />
            <div className="mt-4 space-y-2">
              <h3 className="font-mono text-xs text-muted-foreground uppercase tracking-wider">Bias Trend</h3>
              {profile.biasHistory.map(h => (
                <div key={h.month} className="flex items-center gap-3 font-mono text-sm">
                  <span className="text-muted-foreground w-20">{h.month}</span>
                  <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${((h.leanScore + 100) / 200) * 100}%` }} />
                  </div>
                  <span className="text-foreground w-12 text-right">{h.leanScore > 0 ? '+' : ''}{h.leanScore}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="border border-border bg-card p-6 mb-6">
            <h2 className="font-display text-xl font-semibold text-foreground mb-4">Credibility Score</h2>
            <div className="flex items-center gap-3 mb-3">
              <span className="font-mono text-3xl font-bold text-primary">{profile.avgCredibility}</span>
              <span className="font-mono text-sm text-muted-foreground">/100</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div className={`h-full rounded-full ${profile.avgCredibility >= 80 ? 'bg-credibility-high' : profile.avgCredibility >= 60 ? 'bg-credibility-medium' : 'bg-credibility-low'}`} style={{ width: `${profile.avgCredibility}%` }} />
            </div>
          </div>

          <div className="border border-border bg-card p-6">
            <h2 className="font-display text-xl font-semibold text-foreground mb-4">
              <FileText className="w-5 h-5 inline mr-2" />Articles ({sourceArticles.length})
            </h2>
            <div className="divide-y divide-border">
              {sourceArticles.map(article => {
                const topic = topics.find(t => t.articles.some(a => a.id === article.id));
                return (
                  <div key={article.id} className="py-3">
                    {topic && (
                      <Link to={`/topic/${topic.slug}/article/${article.id}`} className="text-sm font-semibold text-foreground hover:text-primary transition-colors">
                        {article.title}
                      </Link>
                    )}
                    <div className="flex items-center gap-2 mt-1">
                      <span className="font-mono text-xs text-muted-foreground">{article.publishedAt}</span>
                      {article.tone && <span className="font-mono text-xs text-muted-foreground capitalize">· {article.tone}</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default SourceProfilePage;
