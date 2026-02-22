import { useParams, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { getTopic } from '@/api/newsApi';
import { TopicSummary } from '@/types/news';
import { BiasMeter } from '@/components/BiasMeter';
import { ToneAnalysis } from '@/components/ToneAnalysis';
import { FactCheckDisplay } from '@/components/FactCheckDisplay';
import { CommentSection } from '@/components/CommentSection';
import { CommunityNotes } from '@/components/CommunityNotes';
import { HeaderBar } from '@/components/HeaderBar';
import { ExternalLink } from 'lucide-react';

const ArticleDetail = () => {
  const { slug, articleId } = useParams();
  const [topic, setTopic] = useState<TopicSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    getTopic(slug).then(data => {
      setTopic(data);
      setLoading(false);
    });
  }, [slug]);

  const article = topic?.articles.find(a => a.id === articleId);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <span className="font-mono text-muted-foreground">Loading...</span>
      </div>
    );
  }

  if (!topic || !article) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <h2 className="font-display text-2xl text-foreground">Article not found</h2>
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
      <HeaderBar backLink={`/topic/${topic.slug}`} backLabel={`Back to ${topic.topic}`} />

      <main className="container max-w-4xl mx-auto px-4 py-8">
        {/* Article header */}
        <div className="mb-8 animate-fade-in opacity-0">
          <div className="flex items-center gap-3 mb-3 flex-wrap">
            <Link to={`/source/${article.source.id}`} className="font-mono text-sm text-primary hover:underline font-semibold">
              {article.source.name}
            </Link>
            <span className="font-mono text-xs text-muted-foreground">·</span>
            <span className="font-mono text-xs text-muted-foreground">{article.publishedAt}</span>
            <span className="font-mono text-xs text-muted-foreground">·</span>
            <span className="font-mono text-xs text-muted-foreground">{article.source.country}</span>
          </div>
          <h1 className="font-display text-3xl font-bold text-foreground leading-tight mb-4">
            {article.title}
          </h1>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Summary */}
            <section className="border border-border bg-card p-5">
              <h2 className="font-display text-lg font-semibold text-foreground mb-3">Article Summary</h2>
              <p className="text-secondary-foreground leading-relaxed">
                This article from {article.source.name} provides coverage of the {topic.topic} topic with a{' '}
                <span className="font-semibold">{article.source.biasLean}</span> editorial perspective.
                The reporting style is primarily <span className="font-semibold">{article.tone || 'balanced'}</span>,
                with {article.toneScore ? `${article.toneScore.logical}% analytical` : 'balanced'} content.
              </p>
              <p className="text-secondary-foreground leading-relaxed mt-3">
                The source has an overall credibility score of {article.source.credibilityScore}%, based on historical accuracy,
                editorial standards, and transparency practices. This article contributes to the broader coverage of {topic.topic},
                which includes {topic.articles.length} sources from {new Set(topic.articles.map(a => a.source.country)).size} countries.
              </p>
            </section>

            {/* Tone Analysis */}
            {article.toneScore && (
              <section className="border border-border bg-card p-5">
                <ToneAnalysis tone={article.tone || 'balanced'} toneScore={article.toneScore} sourceName={article.source.name} />
              </section>
            )}

            {/* Fact Check */}
            {article.factCheck && (
              <section className="border border-border bg-card p-5">
                <FactCheckDisplay factCheck={article.factCheck} />
              </section>
            )}
          </div>

          {/* Sidebar */}
          <aside className="space-y-6">
            {/* Article link */}
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between border border-border p-4 bg-card hover:bg-accent/30 transition-colors"
            >
              <span className="font-mono text-sm text-foreground">Read Original Article</span>
              <ExternalLink className="w-4 h-4 text-primary" />
            </a>

            {/* Source profile link */}
            <Link
              to={`/source/${article.source.id}`}
              className="block border border-border p-4 bg-card hover:bg-accent/30 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm text-foreground">View {article.source.name} profile</span>
                <ExternalLink className="w-4 h-4 text-muted-foreground" />
              </div>
            </Link>

            {/* Bias */}
            <div className="border border-border p-5 bg-card">
              <h3 className="font-mono text-sm font-semibold text-foreground mb-3">Source Bias</h3>
              <BiasMeter
                leanScore={biasLeanToScore[article.source.biasLean] || 0}
                overallLean={article.source.biasLean}
              />
            </div>

            {/* Credibility */}
            <div className="border border-border p-5 bg-card">
              <h3 className="font-mono text-sm font-semibold text-foreground mb-3">Source Credibility</h3>
              <div className="space-y-2">
                <div className="flex justify-between font-mono text-sm">
                  <span className="text-muted-foreground">Score</span>
                  <span className="text-foreground font-bold">{article.source.credibilityScore}%</span>
                </div>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${
                      article.source.credibilityScore >= 80 ? 'bg-credibility-high' :
                      article.source.credibilityScore >= 60 ? 'bg-credibility-medium' : 'bg-credibility-low'
                    }`}
                    style={{ width: `${article.source.credibilityScore}%` }}
                  />
                </div>
              </div>
            </div>
          </aside>
        </div>

        {/* Community */}
        <div className="mt-12 space-y-8">
          <div className="newspaper-divider mb-4" />
          <CommentSection comments={topic.comments || []} />
        </div>
      </main>
    </div>
  );
};

export default ArticleDetail;
