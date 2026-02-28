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
import { ExternalLink, AlertTriangle } from 'lucide-react';

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
            {/* Analysis Summary */}
            <section className="border border-border bg-card p-5">
              <h2 className="font-display text-lg font-semibold text-foreground mb-3">Source Analysis</h2>
              {(() => {
                const contradictionsForArticle = (topic.contradictions || []).filter(
                  c => c.wrongArticle === article.id
                );
                const missingClaims = topic.articleMissingContext?.[article.id] || [];
                const credScore = article.source.credibilityScore;

                // Describe the credibility formula accurately
                const credLabel = credScore >= 80 ? 'high' : credScore >= 60 ? 'moderate' : 'low';

                return (
                  <>
                    <p className="text-secondary-foreground leading-relaxed">
                      Our pipeline scored <span className="font-semibold">{article.source.name}</span>'s
                      coverage at <span className="font-semibold">{credScore}% credibility</span> ({credLabel}).
                      This score is derived from three factors:{' '}
                      <span className="font-semibold">source reputation</span> (based on known outlet reliability),{' '}
                      <span className="font-semibold">objectivity</span> (measured by running each sentence through
                      a subjectivity classifier and a sentiment-neutrality model), and{' '}
                      <span className="font-semibold">cross-source agreement</span> (determined by extracting factual
                      claims and comparing them across all {topic.articles.length} sources using natural language inference).
                    </p>
                    <p className="text-secondary-foreground leading-relaxed mt-3">
                      {contradictionsForArticle.length > 0
                        ? `Our NLI analysis detected ${contradictionsForArticle.length} claim${contradictionsForArticle.length > 1 ? 's' : ''} from this source that contradict${contradictionsForArticle.length === 1 ? 's' : ''} reporting by other outlets, which lowered the credibility score.`
                        : 'No contradictions were detected between this source and other outlets.'}
                      {' '}
                      {missingClaims.length > 0
                        ? `Additionally, ${missingClaims.length} key claim${missingClaims.length > 1 ? 's' : ''} covered by other sources ${missingClaims.length === 1 ? 'is' : 'are'} absent from this article, which also reduced the score.`
                        : 'This article covers all key claims present across other sources.'}
                    </p>
                    <p className="text-secondary-foreground leading-relaxed mt-3">
                      The source's editorial framing was classified as{' '}
                      <span className="font-semibold">{article.source.biasLean}</span> based on
                      our model's assessment of cited quotes. The overall topic draws
                      from {topic.articles.length} article{topic.articles.length > 1 ? 's' : ''} with
                      a {topic.credibility.sourceAgreement}% inter-source agreement rate.
                    </p>
                  </>
                );
              })()}
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

            {/* Cross-Source Contradictions */}
            {(() => {
              const articleContradictions = (topic.contradictions || []).filter(
                c => c.wrongArticle === article.id || c.correctArticle === article.id
              );
              if (articleContradictions.length === 0) return null;
              return (
                <section className="border border-amber-200 bg-amber-50/50 dark:bg-amber-950/20 dark:border-amber-800 p-5 space-y-4">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-600" />
                    <h3 className="font-display text-lg font-semibold text-foreground">
                      Cross-Source Contradictions ({articleContradictions.length})
                    </h3>
                  </div>
                  <div className="space-y-3">
                    {articleContradictions.map((c, i) => (
                      <div key={i} className="border-l-2 border-amber-400 pl-3 space-y-1">
                        <p className="text-sm text-muted-foreground">
                          <span className="font-semibold text-foreground">{c.wrongSource}</span>:{' '}
                          <span className="italic">&ldquo;{c.wrongClaim}&rdquo;</span>
                        </p>
                        <p className="text-xs text-amber-600 dark:text-amber-400 font-mono uppercase tracking-wider">contradicts</p>
                        <p className="text-sm text-muted-foreground">
                          <span className="font-semibold text-foreground">{c.correctSource}</span>:{' '}
                          <span className="italic">&ldquo;{c.correctClaim}&rdquo;</span>
                        </p>
                      </div>
                    ))}
                  </div>
                </section>
              );
            })()}
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
