import { useParams, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { getUser } from '@/api/newsApi';
import { UserProfile as UserProfileType } from '@/types/news';
import { BiasMeter } from '@/components/BiasMeter';
import { HeaderBar } from '@/components/HeaderBar';
import { BookOpen, MessageSquare, Shield, Eye } from 'lucide-react';

const UserProfile = () => {
  const { userId } = useParams();
  const [user, setUser] = useState<UserProfileType | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId) { setLoading(false); return; }
    getUser(userId)
      .then(data => setUser(data))
      .catch(err => console.error('[UserProfile] Failed to load user:', err))
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <span className="font-mono text-muted-foreground">Loading...</span>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center space-y-4">
          <h2 className="font-display text-2xl text-foreground">User not found</h2>
          <Link to="/" className="text-primary font-mono text-sm hover:underline">← Back to The Newsline</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <HeaderBar backLink="/" backLabel="The Newsline" />
      
      <main className="container max-w-4xl mx-auto px-4 py-8">
        <div className="animate-fade-in opacity-0">
          {/* Profile header */}
          <div className="border border-border bg-card p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="font-display text-3xl font-bold text-foreground">{user.name}</h1>
                <p className="font-mono text-sm text-muted-foreground mt-1">
                  Member since {new Date(user.joinedAt).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {user.isPublic ? (
                  <span className="font-mono text-xs text-credibility-high flex items-center gap-1">
                    <Eye className="w-3 h-3" /> Public
                  </span>
                ) : (
                  <span className="font-mono text-xs text-muted-foreground">Private</span>
                )}
              </div>
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 border-t border-border pt-4">
              <StatBox icon={<BookOpen className="w-4 h-4" />} label="Articles Read" value={user.articlesRead.toString()} />
              <StatBox icon={<MessageSquare className="w-4 h-4" />} label="Comments" value={user.commentsCount.toString()} />
              <StatBox icon={<Shield className="w-4 h-4" />} label="Reputation" value={`${user.reputation}/100`} />
              <div>
                <span className="font-mono text-xs text-muted-foreground">Reading Bias</span>
                <BiasMeter leanScore={user.leanScore} overallLean={user.biasLean} compact />
              </div>
            </div>
          </div>

          {/* Reputation details */}
          <div className="border border-border bg-card p-6 mb-6">
            <h2 className="font-display text-xl font-semibold text-foreground mb-4">Reputation Score</h2>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="font-mono text-3xl font-bold text-primary">{user.reputation}</span>
                <span className="font-mono text-sm text-muted-foreground">/100</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${
                    user.reputation >= 80 ? 'bg-credibility-high' :
                    user.reputation >= 60 ? 'bg-credibility-medium' : 'bg-credibility-low'
                  }`}
                  style={{ width: `${user.reputation}%` }}
                />
              </div>
              <p className="text-sm text-muted-foreground">
                Based on comment quality, accuracy of claims, and community feedback.
              </p>
            </div>
          </div>

          {/* Reading bias */}
          <div className="border border-border bg-card p-6">
            <h2 className="font-display text-xl font-semibold text-foreground mb-4">Reading Bias Profile</h2>
            <BiasMeter leanScore={user.leanScore} overallLean={user.biasLean} />
            <p className="text-sm text-muted-foreground mt-4">
              This user's reading habits show a <span className="font-semibold text-foreground">{user.biasLean}</span> tendency,
              based on the sources and articles they engage with most frequently.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

const StatBox = ({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) => (
  <div className="space-y-1">
    <div className="flex items-center gap-1.5 text-muted-foreground">{icon}<span className="font-mono text-xs">{label}</span></div>
    <div className="font-mono text-lg font-bold text-foreground">{value}</div>
  </div>
);

export default UserProfile;
