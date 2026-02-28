import { useState } from 'react';
import { SummarySection, Article, CommunityNote } from '@/types/news';
import { BiasMeter } from './BiasMeter';
import { ChevronDown, ChevronUp, BarChart3, Users, ThumbsUp, ThumbsDown, Plus } from 'lucide-react';
import { Link } from 'react-router-dom';

interface CitedContentProps {
  sections: SummarySection[];
  articles?: Article[];
  topicSlug?: string;
  communityNotes?: CommunityNote[];
}

export const CitedContent = ({ sections, articles = [], topicSlug, communityNotes = [] }: CitedContentProps) => {
  const [expandedSection, setExpandedSection] = useState<number | null>(null);
  const [addingNoteSection, setAddingNoteSection] = useState<number | null>(null);

  const getArticle = (articleId: string) => articles.find(a => a.id === articleId);

  // Distribute community notes to sections (mock: round-robin)
  const getSectionNotes = (sectionIdx: number): CommunityNote[] => {
    if (communityNotes.length === 0) return [];
    return communityNotes.filter((_, i) => i % sections.length === sectionIdx);
  };

  return (
    <div className="space-y-6">
      {sections.map((section, i) => {
        const isExpanded = expandedSection === i;
        const sectionNotes = getSectionNotes(i);
        const topNote = sectionNotes.sort((a, b) => b.helpfulCount - a.helpfulCount)[0];

        return (
          <div key={i} className="border border-border bg-card">
            {/* Section header - clickable to reveal citations & stats */}
            <button
              onClick={() => setExpandedSection(isExpanded ? null : i)}
              className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-accent/50 transition-colors"
            >
              <h3 className="font-display text-xl font-semibold text-foreground">
                {section.heading}
              </h3>
              <div className="flex items-center gap-2">
                {section.stats && (
                  <span className="font-mono text-xs text-muted-foreground">
                    {section.stats.credibilityScore}% credible
                  </span>
                )}
                {sectionNotes.length > 0 && (
                  <span className="font-mono text-xs text-muted-foreground flex items-center gap-1">
                    <Users className="w-3 h-3" /> {sectionNotes.length}
                  </span>
                )}
                {isExpanded ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
              </div>
            </button>

            {/* Summary content (always visible) */}
            <div className="px-5 pb-4">
              <p className="text-secondary-foreground leading-relaxed">
                {section.content}
              </p>
            </div>

            {/* Expanded: Citations, Stats, Community Notes */}
            {isExpanded && (
              <div className="border-t border-border">
                {/* Citations */}
                {section.citations.length > 0 && (
                  <div className="px-5 py-4 space-y-2">
                    <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider">Sources & Citations</span>
                    {section.citations.map((citation, j) => {
                      const article = getArticle(citation.articleId);
                      const biasClass = citation.biasLevel === 'left' ? 'bias-bg-left' :
                        citation.biasLevel === 'right' ? 'bias-bg-right' : '';

                      // Determine the source name: from matched article, or extract from citation text
                      const sourceName = article?.source?.name;

                      return (
                        <div key={j} className={`py-2 px-3 text-sm leading-relaxed ${biasClass}`}>
                          <span className="text-foreground italic">&ldquo;{citation.text}&rdquo;</span>
                          {article && topicSlug ? (
                            <Link
                              to={`/topic/${topicSlug}/article/${article.id}`}
                              className="ml-2 font-mono text-xs text-primary hover:underline"
                            >
                              — {article.source.name}
                            </Link>
                          ) : sourceName ? (
                            <span className="ml-2 font-mono text-xs text-muted-foreground">
                              — {sourceName}
                            </span>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Stats panel */}
                {section.stats && (
                  <div className="border-t border-border px-5 py-4 bg-accent/30 space-y-4">
                    <div className="flex items-center gap-2 mb-2">
                      <BarChart3 className="w-4 h-4 text-primary" />
                      <span className="font-mono text-xs font-semibold text-foreground uppercase tracking-wider">Section Analysis</span>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="font-mono text-xs text-muted-foreground">Bias</span>
                        <BiasMeter leanScore={section.stats.leanScore} overallLean={section.stats.biasLean} compact />
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between font-mono text-xs">
                          <span className="text-muted-foreground">Credibility</span>
                          <span className="text-foreground font-bold">{section.stats.credibilityScore}%</span>
                        </div>
                        <div className="flex justify-between font-mono text-xs">
                          <span className="text-muted-foreground">Sources</span>
                          <span className="text-foreground">{section.stats.sourceCount}</span>
                        </div>
                        <div className="flex justify-between font-mono text-xs">
                          <span className="text-muted-foreground">Agreement</span>
                          <span className="text-foreground">{section.stats.agreement}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Community note for this section */}
                <div className="border-t border-border px-5 py-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                      <Users className="w-3.5 h-3.5" /> Community Notes
                    </span>
                    <button
                      onClick={(e) => { e.stopPropagation(); setAddingNoteSection(addingNoteSection === i ? null : i); }}
                      className="font-mono text-xs text-primary hover:text-primary/80 flex items-center gap-1"
                    >
                      <Plus className="w-3 h-3" /> Add Note
                    </button>
                  </div>

                  {topNote && (
                    <div className="bg-accent/30 border border-border p-3">
                      <p className="text-sm text-secondary-foreground leading-relaxed">{topNote.text}</p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="font-mono text-xs text-muted-foreground">
                          by <span className="text-foreground">{topNote.userName}</span>
                        </span>
                        <div className="flex items-center gap-3">
                          <button className="flex items-center gap-1 text-muted-foreground hover:text-credibility-high transition-colors">
                            <ThumbsUp className="w-3 h-3" />
                            <span className="font-mono text-xs">{topNote.helpfulCount}</span>
                          </button>
                          <button className="flex items-center gap-1 text-muted-foreground hover:text-destructive transition-colors">
                            <ThumbsDown className="w-3 h-3" />
                            <span className="font-mono text-xs">{topNote.unhelpfulCount}</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {!topNote && (
                    <p className="font-mono text-xs text-muted-foreground">No community notes for this section yet.</p>
                  )}

                  {addingNoteSection === i && (
                    <div className="space-y-2">
                      <textarea
                        className="w-full bg-background border border-border rounded-sm px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                        rows={3}
                        placeholder="Add context, corrections, or additional information..."
                      />
                      <div className="flex justify-end gap-2">
                        <button onClick={() => setAddingNoteSection(null)} className="font-mono text-xs text-muted-foreground hover:text-foreground px-3 py-1.5">Cancel</button>
                        <button className="font-mono text-xs bg-primary text-primary-foreground px-3 py-1.5 hover:bg-primary/90">Submit</button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
