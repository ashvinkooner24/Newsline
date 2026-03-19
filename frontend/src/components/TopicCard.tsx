import { StorySummary } from '@/types/news';
import { StoryCard } from './StoryCard';

interface TopicCardProps {
  topic: StorySummary;
  index: number;
}

export const TopicCard = ({ topic, index }: TopicCardProps) => {
  return <StoryCard story={topic} index={index} />;
};
