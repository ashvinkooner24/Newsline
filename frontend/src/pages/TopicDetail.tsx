import { useParams, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { getTopic } from '@/api/newsApi';
import { TopicSummary } from '@/types/news';
import { BiasMeter } from '@/components/BiasMeter';
import { CredibilityGauge } from '@/components/CredibilityGauge';
import { CitedContent } from '@/components/CitedContent';
import { SourceList } from '@/components/SourceList';
import { CommentSection } from '@/components/CommentSection';
import { CommunityNotes } from '@/components/CommunityNotes';
import { RatingDisplay } from '@/components/RatingDisplay';
import { HeaderBar } from '@/components/HeaderBar';
import { Clock, BarChart3, Star } from 'lucide-react';

const TopicDetail = () => {
  const { slug } = useParams();
  const [topic, setTopic] = useState<TopicSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) { setLoading(false); return; }
    getTopic(slug)
      .then(data => setTopic(data))
      .catch(err => console.error('[TopicDetail] Failed to load topic:', err))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <span className="font-mono text-muted-foreground">Loading...</span>
      </div>
    );
  }

  if (!topic) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <h2 className="font-display text-2xl text-foreground">Topic not found</h2>
          <Link to="/" className="text-primary font-mono text-sm hover:underline">← Back to The Newsline</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <HeaderBar backLink="/" backLabel="The Newsline" />

      <main className="container max-w-5xl mx-auto px-4 py-8">
        {/* Title section */}
        <div className="mb-8 animate-fade-in opacity-0">
          <div className="flex items-center gap-3 mb-3">
            <span className="font-mono text-xs text-primary tracking-widest uppercase">{topic.category}</span>
            {topic.country && <span className="font-mono text-xs text-muted-foreground">· {topic.country}</span>}
            <span className="flex items-center gap-1 text-xs text-muted-foreground font-mono">
              <Clock className="w-3 h-3" />
              {new Date(topic.updatedAt).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
            </span>
          </div>
          <h1 className="font-display text-3xl md:text-4xl font-bold text-foreground leading-tight mb-4">
            {topic.headline}
          </h1>
          <p className="text-lg text-muted-foreground leading-relaxed border-b border-border pb-6">
            {topic.summary}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main content */}
          <div className="lg:col-span-2 space-y-8 animate-fade-in opacity-0" style={{ animationDelay: '100ms' }}>
            <CitedContent
              sections={topic.sections}
              articles={topic.articles}
              topicSlug={topic.slug}
              communityNotes={topic.communityNotes}
            />
          </div>

          {/* Sidebar */}
          <aside className="space-y-6 animate-fade-in opacity-0" style={{ animationDelay: '200ms' }}>
            <div className="border border-border p-5 space-y-4 bg-card">
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-primary" />
                <h3 className="font-mono text-sm font-semibold text-foreground">Overall Bias</h3>
              </div>
              <BiasMeter leanScore={topic.biasAnalysis.leanScore} overallLean={topic.biasAnalysis.overallLean} />
              <div className="grid grid-cols-3 gap-2 text-xs font-mono text-center">
                <div>
                  <div className="text-bias-left font-bold">{topic.biasAnalysis.leftSourceCount}</div>
                  <div className="text-muted-foreground">Left</div>
                </div>
                <div>
                  <div className="text-bias-center font-bold">{topic.biasAnalysis.centerSourceCount}</div>
                  <div className="text-muted-foreground">Center</div>
                </div>
                <div>
                  <div className="text-bias-right font-bold">{topic.biasAnalysis.rightSourceCount}</div>
                  <div className="text-muted-foreground">Right</div>
                </div>
              </div>
            </div>

            <div className="border border-border p-5 bg-card">
              <CredibilityGauge credibility={topic.credibility} />
            </div>

            {topic.rating && (
              <div className="border border-border p-5 bg-card">
                <RatingDisplay rating={topic.rating} />
              </div>
            )}
          </aside>
        </div>

        {/* Community Notes (before sources) */}
        <div className="mt-12 animate-fade-in opacity-0" style={{ animationDelay: '300ms' }}>
          <div className="newspaper-divider mb-4" />
          {topic.communityNotes && topic.communityNotes.length > 0 && (
            <CommunityNotes notes={topic.communityNotes} />
          )}
        </div>

        {/* Sources */}
        <div className="mt-8 animate-fade-in opacity-0" style={{ animationDelay: '350ms' }}>
          <div className="newspaper-divider mb-4" />
          <h2 className="font-display text-xl font-semibold text-foreground mb-4">
            Sources ({topic.articles.length})
          </h2>
          <SourceList articles={topic.articles} topicSlug={topic.slug} />
        </div>

        {/* Comments */}
        <div className="mt-12 space-y-8 animate-fade-in opacity-0" style={{ animationDelay: '400ms' }}>
          <div className="newspaper-divider mb-4" />
          {topic.comments && (
            <CommentSection comments={topic.comments} />
          )}
        </div>
      </main>
    </div>
  );
};

export default TopicDetail;
