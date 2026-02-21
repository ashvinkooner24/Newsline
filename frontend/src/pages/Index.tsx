import { useState, useMemo } from 'react';
import { mockTopics, allCategories, allCountries } from '@/data/mockNews';
import { TopicCard } from '@/components/TopicCard';
import { SearchFilter } from '@/components/SearchFilter';
import { HeaderBar } from '@/components/HeaderBar';
import { Link } from 'react-router-dom';
import { Clock, TrendingUp, Shield, AlertTriangle, CheckCircle, Bookmark, Globe, Landmark, Cpu, HeartPulse, GraduationCap, Banknote } from 'lucide-react';
import { BiasMeter } from '@/components/BiasMeter';
import { CredibilityGauge } from '@/components/CredibilityGauge';

const topicIcons: Record<string, React.ReactNode> = {
  Technology: <Cpu className="w-4 h-4" />,
  Environment: <Globe className="w-4 h-4" />,
  Economy: <Banknote className="w-4 h-4" />,
  Geopolitics: <Landmark className="w-4 h-4" />,
  Finance: <Banknote className="w-4 h-4" />,
  Health: <HeartPulse className="w-4 h-4" />,
  Politics: <Landmark className="w-4 h-4" />,
  Science: <Globe className="w-4 h-4" />,
  Education: <GraduationCap className="w-4 h-4" />,
};

const Index = () => {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedCountry, setSelectedCountry] = useState('');
  const [selectedBias, setSelectedBias] = useState('');
  const [selectedCredibility, setSelectedCredibility] = useState('');
  const [followedTopics, setFollowedTopics] = useState<string[]>(['Technology', 'Geopolitics', 'Economy']);

  const filtered = useMemo(() => {
    return mockTopics.filter(t => {
      if (search && !t.headline.toLowerCase().includes(search.toLowerCase()) && !t.topic.toLowerCase().includes(search.toLowerCase())) return false;
      if (selectedCategory && t.category !== selectedCategory) return false;
      if (selectedCountry && t.country !== selectedCountry) return false;
      if (selectedBias) {
        const biasMap: Record<string, string[]> = {
          'left': ['far-left', 'left', 'center-left'],
          'center': ['center'],
          'right': ['center-right', 'right', 'far-right'],
        };
        if (!biasMap[selectedBias]?.includes(t.biasAnalysis.overallLean)) return false;
      }
      if (selectedCredibility && t.credibility.label !== selectedCredibility) return false;
      return true;
    });
  }, [search, selectedCategory, selectedCountry, selectedBias, selectedCredibility]);

  const heroTopic = filtered.find(t => t.isBreaking) || filtered.find(t => t.isFeatured) || filtered[0];
  const secondaryFeatured = filtered.filter(t => t.isFeatured && t.id !== heroTopic?.id).slice(0, 2);
  const restTopics = filtered.filter(t => t.id !== heroTopic?.id && !secondaryFeatured.find(f => f.id === t.id));

  // Credibility tiers
  const sortedByCredibility = [...mockTopics].sort((a, b) => a.credibility.score - b.credibility.score);
  const lowCredibility = sortedByCredibility.filter(t => t.credibility.label === 'Low' || t.credibility.score < 65).slice(0, 3);
  const midCredibility = sortedByCredibility.filter(t => t.credibility.label === 'Medium').slice(0, 3);
  const highCredibility = [...sortedByCredibility].reverse().filter(t => t.credibility.label === 'High').slice(0, 3);

  // User's followed topics
  const myTopics = filtered.filter(t => followedTopics.includes(t.category));

  const toggleFollow = (cat: string) => {
    setFollowedTopics(prev => prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]);
  };

  return (
    <div className="min-h-screen bg-background">
      <HeaderBar />

      {/* Masthead */}
      <div className="border-b border-border">
        <div className="container max-w-6xl mx-auto px-4">
          <div className="text-center py-4">
            <h1 className="font-display text-5xl md:text-6xl font-bold text-foreground tracking-tight">
              The Newsline
            </h1>
            <p className="font-mono text-xs text-muted-foreground mt-1 tracking-widest uppercase">
              Aggregated Intelligence · Bias Analysis · Source Verification
            </p>
          </div>
          <div className="newspaper-divider mb-0" />
        </div>
      </div>

      {/* Stats bar */}
      <div className="border-b border-border">
        <div className="container max-w-6xl mx-auto px-4 py-2 flex items-center gap-6 text-xs font-mono text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-primary" />
            <span>{mockTopics.length} active topics</span>
          </div>
          <div>{mockTopics.reduce((sum, t) => sum + t.articles.length, 0)} sources analyzed</div>
          <div className="ml-auto">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}
          </div>
        </div>
      </div>

      {/* Search & Filters */}
      <SearchFilter
        search={search} onSearchChange={setSearch}
        selectedCategory={selectedCategory} onCategoryChange={setSelectedCategory}
        selectedCountry={selectedCountry} onCountryChange={setSelectedCountry}
        selectedBias={selectedBias} onBiasChange={setSelectedBias}
        selectedCredibility={selectedCredibility} onCredibilityChange={setSelectedCredibility}
        categories={allCategories} countries={allCountries}
      />

      <main className="container max-w-6xl mx-auto px-4 py-6">
        {/* Hero + Secondary Featured */}
        {heroTopic && (
          <section className="mb-8">
            <div className="flex items-center gap-2 mb-3">
              <span className="font-display text-sm font-bold text-foreground uppercase tracking-wider">Top Stories</span>
              <div className="flex-1 border-t border-foreground" />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
              <Link to={`/topic/${heroTopic.slug}`} className="lg:col-span-3 group">
                <article className="space-y-3">
                  {heroTopic.isBreaking && (
                    <span className="inline-block font-mono text-xs font-bold text-destructive uppercase tracking-widest">● Breaking</span>
                  )}
                  <h2 className="font-display text-3xl md:text-4xl font-bold text-foreground leading-tight group-hover:text-primary transition-colors">
                    {heroTopic.headline}
                  </h2>
                  <p className="text-muted-foreground leading-relaxed text-lg">{heroTopic.summary}</p>
                  <div className="flex items-center gap-4 pt-2">
                    <span className="font-mono text-xs text-primary uppercase tracking-wider">{heroTopic.category}</span>
                    <span className="font-mono text-xs text-muted-foreground">{heroTopic.articles.length} sources</span>
                    <CredibilityGauge credibility={heroTopic.credibility} compact />
                  </div>
                  <div className="max-w-xs pt-1">
                    <BiasMeter leanScore={heroTopic.biasAnalysis.leanScore} overallLean={heroTopic.biasAnalysis.overallLean} compact />
                  </div>
                </article>
              </Link>
              <div className="lg:col-span-2 space-y-4 lg:border-l lg:border-border lg:pl-6">
                {secondaryFeatured.map(topic => (
                  <Link key={topic.id} to={`/topic/${topic.slug}`} className="block group">
                    <article className="space-y-2 pb-4 border-b border-border last:border-0">
                      <span className="font-mono text-xs text-primary uppercase tracking-wider">{topic.category}</span>
                      <h3 className="font-display text-lg font-semibold text-foreground leading-snug group-hover:text-primary transition-colors">
                        {topic.headline}
                      </h3>
                      <p className="text-sm text-muted-foreground leading-relaxed line-clamp-2">{topic.summary}</p>
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-xs text-muted-foreground">{topic.articles.length} sources</span>
                        <CredibilityGauge credibility={topic.credibility} compact />
                      </div>
                    </article>
                  </Link>
                ))}
              </div>
            </div>
          </section>
        )}

        <div className="newspaper-divider mb-6" />

        {/* Your Topics */}
        <section className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Bookmark className="w-4 h-4 text-primary" />
            <span className="font-display text-sm font-bold text-foreground uppercase tracking-wider">Your Topics</span>
            <div className="flex-1 border-t border-rule" />
          </div>
          {/* Topic pills */}
          <div className="flex flex-wrap gap-2 mb-4">
            {allCategories.map(cat => (
              <button
                key={cat}
                onClick={() => toggleFollow(cat)}
                className={`flex items-center gap-1.5 px-3 py-1.5 font-mono text-xs border transition-colors ${
                  followedTopics.includes(cat)
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-card text-muted-foreground border-border hover:border-primary hover:text-foreground'
                }`}
              >
                {topicIcons[cat] || <Globe className="w-3.5 h-3.5" />}
                {cat}
              </button>
            ))}
          </div>
          {myTopics.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {myTopics.slice(0, 6).map((topic, i) => (
                <TopicCard key={topic.id} topic={topic} index={i} />
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-6 font-mono text-sm">Select topics above to see personalized stories.</p>
          )}
        </section>

        <div className="newspaper-divider mb-6" />

        {/* Credibility Tiers */}
        <section className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-4 h-4 text-primary" />
            <span className="font-display text-sm font-bold text-foreground uppercase tracking-wider">By Credibility</span>
            <div className="flex-1 border-t border-rule" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* High */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-border">
                <CheckCircle className="w-4 h-4 text-credibility-high" />
                <span className="font-mono text-xs font-bold text-credibility-high uppercase tracking-wider">High Credibility</span>
              </div>
              {highCredibility.map(t => (
                <Link key={t.id} to={`/topic/${t.slug}`} className="block group">
                  <div className="border-l-2 border-credibility-high pl-3 py-1">
                    <h4 className="font-display text-sm font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-2">{t.headline}</h4>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="font-mono text-xs text-credibility-high font-bold">{t.credibility.score}%</span>
                      <span className="font-mono text-xs text-muted-foreground">{t.articles.length} sources</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
            {/* Medium */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-border">
                <AlertTriangle className="w-4 h-4 text-credibility-medium" />
                <span className="font-mono text-xs font-bold text-credibility-medium uppercase tracking-wider">Medium Credibility</span>
              </div>
              {midCredibility.map(t => (
                <Link key={t.id} to={`/topic/${t.slug}`} className="block group">
                  <div className="border-l-2 border-credibility-medium pl-3 py-1">
                    <h4 className="font-display text-sm font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-2">{t.headline}</h4>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="font-mono text-xs text-credibility-medium font-bold">{t.credibility.score}%</span>
                      <span className="font-mono text-xs text-muted-foreground">{t.articles.length} sources</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
            {/* Low */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-border">
                <AlertTriangle className="w-4 h-4 text-credibility-low" />
                <span className="font-mono text-xs font-bold text-credibility-low uppercase tracking-wider">Low Credibility</span>
              </div>
              {lowCredibility.length > 0 ? lowCredibility.map(t => (
                <Link key={t.id} to={`/topic/${t.slug}`} className="block group">
                  <div className="border-l-2 border-credibility-low pl-3 py-1">
                    <h4 className="font-display text-sm font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-2">{t.headline}</h4>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="font-mono text-xs text-credibility-low font-bold">{t.credibility.score}%</span>
                      <span className="font-mono text-xs text-muted-foreground">{t.articles.length} sources</span>
                    </div>
                  </div>
                </Link>
              )) : (
                <p className="font-mono text-xs text-muted-foreground py-4">No low credibility topics currently.</p>
              )}
            </div>
          </div>
        </section>

        <div className="newspaper-divider mb-6" />

        {/* Most Discussed */}
        <section className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-primary" />
            <span className="font-display text-sm font-bold text-foreground uppercase tracking-wider">Most Discussed</span>
            <div className="flex-1 border-t border-rule" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[...mockTopics].sort((a, b) => (b.rating?.totalRatings || 0) - (a.rating?.totalRatings || 0)).slice(0, 4).map(t => (
              <Link key={t.id} to={`/topic/${t.slug}`} className="group flex gap-4 border border-border bg-card p-4 hover:bg-accent/30 transition-colors">
                <div className="flex-1">
                  <h4 className="font-display text-sm font-semibold text-foreground group-hover:text-primary transition-colors">{t.headline}</h4>
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{t.summary}</p>
                </div>
                <div className="flex flex-col items-end justify-center shrink-0">
                  <span className="font-mono text-lg font-bold text-primary">{t.rating?.totalRatings || 0}</span>
                  <span className="font-mono text-xs text-muted-foreground">ratings</span>
                </div>
              </Link>
            ))}
          </div>
        </section>

        <div className="newspaper-divider mb-6" />

        {/* All Coverage */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <span className="font-display text-sm font-bold text-foreground uppercase tracking-wider">All Coverage</span>
            <div className="flex-1 border-t border-rule" />
            <span className="font-mono text-xs text-muted-foreground">{restTopics.length} topics</span>
          </div>
          {restTopics.length === 0 && (
            <p className="text-center text-muted-foreground py-12 font-mono text-sm">No topics match your filters.</p>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {restTopics.map((topic, i) => (
              <TopicCard key={topic.id} topic={topic} index={i} />
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t-2 border-foreground mt-12">
        <div className="container max-w-6xl mx-auto px-4 py-6 text-center text-xs text-muted-foreground font-mono">
          The Newsline — Automated news aggregation with bias and credibility analysis
        </div>
      </footer>
    </div>
  );
};

export default Index;
