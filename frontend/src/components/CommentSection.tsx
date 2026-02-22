import { useState } from 'react';
import { Comment } from '@/types/news';
import { ThumbsUp, ThumbsDown, MessageSquare, ChevronDown, ChevronUp } from 'lucide-react';
import { Link } from 'react-router-dom';

interface CommentSectionProps {
  comments: Comment[];
}

export const CommentSection = ({ comments }: CommentSectionProps) => {
  const [sortBy, setSortBy] = useState<'top' | 'newest'>('top');
  const [showReplyInput, setShowReplyInput] = useState<string | null>(null);

  const sorted = [...comments].sort((a, b) =>
    sortBy === 'top' ? (b.likes - b.dislikes) - (a.likes - a.dislikes) : new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-primary" />
          <h3 className="font-display text-lg font-semibold text-foreground">Discussion ({comments.length})</h3>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setSortBy('top')}
            className={`font-mono text-xs px-2 py-1 ${sortBy === 'top' ? 'text-primary border-b-2 border-primary' : 'text-muted-foreground'}`}
          >Top</button>
          <button
            onClick={() => setSortBy('newest')}
            className={`font-mono text-xs px-2 py-1 ${sortBy === 'newest' ? 'text-primary border-b-2 border-primary' : 'text-muted-foreground'}`}
          >Newest</button>
        </div>
      </div>

      {/* Add comment */}
      <div className="border border-border p-4 bg-card">
        <textarea
          placeholder="Share your thoughts..."
          className="w-full bg-background border border-border rounded-sm p-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary resize-none font-body"
          rows={3}
        />
        <div className="flex justify-end mt-2">
          <button className="font-mono text-xs bg-primary text-primary-foreground px-4 py-2 hover:bg-primary/90 transition-colors">
            Comment
          </button>
        </div>
      </div>

      {/* Comments */}
      <div className="space-y-0 divide-y divide-border">
        {sorted.map(comment => (
          <CommentItem key={comment.id} comment={comment} />
        ))}
      </div>
    </div>
  );
};

const CommentItem = ({ comment, isReply = false }: { comment: Comment; isReply?: boolean }) => {
  const [showReplies, setShowReplies] = useState(false);

  return (
    <div className={`py-4 ${isReply ? 'pl-6 border-l-2 border-border' : ''}`}>
      <div className="flex items-center gap-2 mb-2">
        <Link to={`/user/${comment.userId}`} className="font-mono text-sm font-semibold text-foreground hover:text-primary">
          {comment.userName}
        </Link>
        <span className="font-mono text-xs text-muted-foreground">
          rep: {comment.userReputation}
        </span>
        <span className="font-mono text-xs text-muted-foreground">·</span>
        <span className="font-mono text-xs text-muted-foreground">
          {getTimeAgo(comment.createdAt)}
        </span>
      </div>
      <p className="text-sm text-secondary-foreground leading-relaxed mb-2">{comment.text}</p>
      <div className="flex items-center gap-4">
        <button className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors">
          <ThumbsUp className="w-3.5 h-3.5" />
          <span className="font-mono text-xs">{comment.likes}</span>
        </button>
        <button className="flex items-center gap-1 text-muted-foreground hover:text-foreground transition-colors">
          <ThumbsDown className="w-3.5 h-3.5" />
          <span className="font-mono text-xs">{comment.dislikes}</span>
        </button>
        <button className="font-mono text-xs text-muted-foreground hover:text-foreground">Reply</button>
        {comment.replies && comment.replies.length > 0 && (
          <button
            onClick={() => setShowReplies(!showReplies)}
            className="flex items-center gap-1 font-mono text-xs text-primary"
          >
            {showReplies ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            {comment.replies.length} {comment.replies.length === 1 ? 'reply' : 'replies'}
          </button>
        )}
      </div>
      {showReplies && comment.replies?.map(reply => (
        <CommentItem key={reply.id} comment={reply} isReply />
      ))}
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
