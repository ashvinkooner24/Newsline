import { CommunityNote } from '@/types/news';
import { Users, ThumbsUp, ThumbsDown } from 'lucide-react';

interface CommunityNotesProps {
  notes: CommunityNote[];
}

export const CommunityNotes = ({ notes }: CommunityNotesProps) => {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Users className="w-4 h-4 text-primary" />
        <h3 className="font-display text-lg font-semibold text-foreground">Community Notes</h3>
      </div>
      <div className="space-y-3">
        {notes.map(note => (
          <div key={note.id} className="border border-border bg-accent/30 p-4">
            <p className="text-sm text-secondary-foreground leading-relaxed mb-3">{note.text}</p>
            <div className="flex items-center justify-between">
              <span className="font-mono text-xs text-muted-foreground">
                by <span className="text-foreground">{note.userName}</span> · {getTimeAgo(note.createdAt)}
              </span>
              <div className="flex items-center gap-3">
                <button className="flex items-center gap-1 text-muted-foreground hover:text-credibility-high transition-colors">
                  <ThumbsUp className="w-3.5 h-3.5" />
                  <span className="font-mono text-xs">{note.helpfulCount}</span>
                </button>
                <button className="flex items-center gap-1 text-muted-foreground hover:text-destructive transition-colors">
                  <ThumbsDown className="w-3.5 h-3.5" />
                  <span className="font-mono text-xs">{note.unhelpfulCount}</span>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
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
