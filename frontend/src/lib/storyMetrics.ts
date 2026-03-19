import { Article, TopicSummary } from '@/types/news';

export function getUniqueSourceCount(articles: Article[]): number {
  const unique = new Set(
    articles
      .map(a => a.source?.id || a.source?.name || '')
      .filter(Boolean),
  );
  return unique.size;
}

export function getArticleCount(story: TopicSummary): number {
  return story.articles?.length || 0;
}

export function getSourceCount(story: TopicSummary): number {
  return getUniqueSourceCount(story.articles || []);
}
