/**
 * newsApi.ts
 *
 * Data-fetching layer for the HackLDN backend.
 *
 * All requests go through the Vite dev proxy (/api → http://127.0.0.1:8000),
 * so no CORS issues during development.
 *
 * Usage:
 *   import { getTopics, getTopic } from '@/api/newsApi';
 *
 *   const topics = await getTopics();          // TopicSummary[]
 *   const topic  = await getTopic(0);          // TopicSummary | null
 */

import type {
  TopicSummary,
  Source,
  Article,
  UserProfile,
  Comment,
  SummarySection,
  BiasAnalysis,
  CredibilityAssessment,
  BiasLean,
  Citation,
  SectionStats,
} from '@/types/news';
import { mockTopics, mockUsers, mockSourceProfiles } from '@/data/mockNews';

// ---------------------------------------------------------------------------
// Backend response shapes (mirrors Backend/models.py Pydantic models)
// ---------------------------------------------------------------------------

export interface BackendNewsProvider {
  name: string;
  bias_score: number;   // -1 (far-left) → 1 (far-right)
  trust_score: number;  // 0 (low) → 1 (high)
}

export interface BackendUser {
  username: string;
  email: string;
  reputation: number;  // 0–100
}

export interface BackendComment {
  text: string;
  like_count: number;
  dislike_count: number;
  parent: number | null;
  user: BackendUser | null;
}

export interface BackendCitation {
  source: string;
  article_id: string;
  quote: string;
  bias_level: string;  // 'left' | 'right' | 'neutral'
}

export interface BackendArticleMeta {
  id: string;
  title: string;
  url: string;
  source: string;
  published_at: string | null;
  excerpt: string;
}

export interface BackendSegment {
  heading: string;
  text: string;
  sources: BackendNewsProvider[];
  citations: BackendCitation[];
  avg_bias: number;
  avg_truth: number;
  article_count: number;
  notes: string | null;
  comments: BackendComment[];
}

export interface BackendStory {
  heading: string;
  slug: string;
  summary: string;
  political_bias: number;
  factual_accuracy: number;
  sources: BackendNewsProvider[];
  segments: BackendSegment[];
  articles: BackendArticleMeta[];
  category: string;
  updated_at: string;
}

export interface BackendStoryWrapper {
  story: BackendStory;
  comments: BackendComment[];
}

// ---------------------------------------------------------------------------
// Transformation helpers
// ---------------------------------------------------------------------------

/** Convert a -1…1 bias float to a named BiasLean. */
function biasFloatToLean(score: number): BiasLean {
  if (score < -0.6) return 'far-left';
  if (score < -0.3) return 'left';
  if (score < -0.1) return 'center-left';
  if (score <= 0.1) return 'center';
  if (score <= 0.3) return 'center-right';
  if (score <= 0.6) return 'right';
  return 'far-right';
}

/** Convert a 0…1 credibility float to a label. */
function credibilityLabel(score: number): CredibilityAssessment['label'] {
  if (score >= 0.8)  return 'High';
  if (score >= 0.6)  return 'Medium';
  if (score >= 0.4)  return 'Low';
  return 'Uncertain';
}

/** Turn any string into a URL-safe slug. */
function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

/**
 * Build a frontend Source from a BackendNewsProvider.
 * Many fields (id, url, country) are not available from the backend yet;
 * they get sensible defaults until the backend model is extended.
 */
function transformProvider(provider: BackendNewsProvider, index: number): Source {
  return {
    id:               slugify(provider.name) || `source-${index}`,
    name:             provider.name,
    url:              '#',
    credibilityScore: Math.round(provider.trust_score * 100),
    biasLean:         biasFloatToLean(provider.bias_score),
    country:          'Unknown',
  };
}

/**
 * Build a frontend SummarySection from a BackendSegment.
 * Uses real citations (with quotes) from the backend when available.
 */
function transformSegment(segment: BackendSegment, index: number): SummarySection {
  // Use real citations from the backend if available
  let citations: Citation[];
  if (segment.citations && segment.citations.length > 0) {
    citations = segment.citations.map((c) => ({
      articleId: c.article_id,
      text:      c.quote || `Reported by ${c.source}.`,
      biasLevel: (c.bias_level === 'left' || c.bias_level === 'right' || c.bias_level === 'neutral')
        ? c.bias_level
        : 'neutral',
    }));
  } else {
    // Fallback for legacy data without real citations
    const sources: Source[] = segment.sources.map(transformProvider);
    citations = sources.map((src, i) => ({
      articleId: `seg-${index}-src-${i}`,
      text:      `Reported by ${src.name}.`,
      biasLevel: segment.sources[i].bias_score < -0.3
        ? 'left' as const
        : segment.sources[i].bias_score > 0.3
          ? 'right' as const
          : 'neutral' as const,
    }));
  }

  const stats: SectionStats = {
    biasLean:         biasFloatToLean(segment.avg_bias),
    leanScore:        Math.round(segment.avg_bias * 100),
    credibilityScore: Math.round(segment.avg_truth * 100),
    sourceCount:      segment.sources.length,
    agreement:        Math.round(segment.avg_truth * 100),
  };

  return {
    heading:   segment.heading || segment.notes || `Section ${index + 1}`,
    content:   segment.text,
    citations,
    stats,
  };
}

/** Build frontend Comment objects from backend comments. */
function transformComments(
  backendComments: BackendComment[],
  storyIndex: number
): Comment[] {
  return backendComments.map((c, i) => ({
    id:             `story-${storyIndex}-comment-${i}`,
    userId:         slugify(c.user?.username ?? 'anonymous'),
    userName:       c.user?.username ?? 'Anonymous',
    userReputation: 50,
    text:           c.text,
    createdAt:      new Date().toISOString(),
    likes:          c.like_count,
    dislikes:       c.dislike_count,
  }));
}

/**
 * Build a BiasAnalysis from the story's source list.
 * Left = bias_score < -0.1, Right = bias_score > 0.1, else center.
 */
function buildBiasAnalysis(story: BackendStory): BiasAnalysis {
  let left = 0, center = 0, right = 0;
  for (const s of story.sources) {
    if (s.bias_score < -0.3)      left++;
    else if (s.bias_score > 0.3)  right++;
    else                           center++;
  }
  return {
    overallLean:       biasFloatToLean(story.political_bias),
    leanScore:         Math.round(story.political_bias * 100),
    leftSourceCount:   left,
    centerSourceCount: center,
    rightSourceCount:  right,
  };
}

/**
 * Build a CredibilityAssessment from the story's metrics.
 * `sourceAgreement` is approximated from the spread of segment bias scores.
 */
function buildCredibility(story: BackendStory): CredibilityAssessment {
  const score = Math.round(story.factual_accuracy * 100);
  const avgSrcCredibility = story.sources.length
    ? Math.round(
        (story.sources.reduce((sum, s) => sum + s.trust_score, 0) / story.sources.length) * 100
      )
    : 0;

  const articleCount = story.segments.reduce((sum, seg) => sum + seg.article_count, 0);

  // Approximate agreement: invert the std-dev of bias scores (higher spread = lower agreement)
  const biasScores = story.segments.map((s) => s.avg_bias);
  const mean = biasScores.reduce((a, b) => a + b, 0) / (biasScores.length || 1);
  const variance = biasScores.reduce((a, b) => a + (b - mean) ** 2, 0) / (biasScores.length || 1);
  const sourceAgreement = Math.max(0, Math.round((1 - Math.sqrt(variance)) * 100));

  return {
    score,
    articleCount,
    avgSourceCredibility: avgSrcCredibility,
    sourceAgreement,
    label: credibilityLabel(story.factual_accuracy),
  };
}

/**
 * Main transformer: BackendStoryWrapper → TopicSummary.
 * Uses real article metadata and citations from the backend.
 */
export function transformStory(wrapper: BackendStoryWrapper, index: number): TopicSummary {
  const { story, comments } = wrapper;

  // Use the backend summary (standfirst) or fall back to first segment text
  const summary = story.summary || story.segments[0]?.text || story.heading;

  // Use real article metadata from the backend if available
  let articles: Article[];
  if (story.articles && story.articles.length > 0) {
    // Build a provider lookup for credibility/bias info
    const providerMap: Record<string, BackendNewsProvider> = {};
    for (const p of story.sources) {
      providerMap[p.name] = p;
    }

    articles = story.articles.map((meta, i) => {
      const provider = providerMap[meta.source];
      return {
        id:          meta.id,
        title:       meta.title,
        url:         meta.url || '#',
        source: {
          id:               slugify(meta.source) || `source-${i}`,
          name:             meta.source,
          url:              meta.url || '#',
          credibilityScore: provider ? Math.round(provider.trust_score * 100) : 70,
          biasLean:         provider ? biasFloatToLean(provider.bias_score) : 'center' as const,
          country:          'Unknown',
        },
        publishedAt: meta.published_at || new Date().toISOString().split('T')[0],
        excerpt:     meta.excerpt || '',
      };
    });
  } else {
    // Fallback: derive stub Article entries from segment sources
    articles = story.segments.flatMap((seg, sIdx) =>
      seg.sources.map((provider, pIdx) => ({
        id:          `story-${index}-seg-${sIdx}-src-${pIdx}`,
        title:       `${provider.name}: ${story.heading}`,
        url:         '#',
        source:      transformProvider(provider, pIdx),
        publishedAt: new Date().toISOString().split('T')[0],
        excerpt:     seg.text,
      }))
    );
  }

  // Deduplicate articles by ID (keep first occurrence)
  const seenIds = new Set<string>();
  const uniqueArticles = articles.filter(a => {
    if (seenIds.has(a.id)) return false;
    seenIds.add(a.id);
    return true;
  });

  return {
    id:            String(index),
    topic:         story.heading,
    slug:          story.slug || slugify(story.heading),
    headline:      story.heading,
    summary,
    sections:      story.segments.map(transformSegment),
    articles:      uniqueArticles,
    biasAnalysis:  buildBiasAnalysis(story),
    credibility:   buildCredibility(story),
    updatedAt:     story.updated_at || new Date().toISOString(),
    category:      story.category || 'General',
    country:       'Global',
    comments:      transformComments(comments, index),
    communityNotes: [],
  };
}

/**
 * Transform a BackendUser into a frontend UserProfile.
 * Fields not available from the backend (articlesRead, commentsCount,
 * biasLean, leanScore, isPublic) get sensible defaults until the backend
 * model is extended.
 */
export function transformUser(user: BackendUser): UserProfile {
  return {
    id:            slugify(user.username),
    name:          user.username,
    joinedAt:      new Date().toISOString().split('T')[0],
    articlesRead:  0,
    commentsCount: 0,
    biasLean:      'center',
    leanScore:     0,
    reputation:    user.reputation,
    isPublic:      true,
  };
}

// ---------------------------------------------------------------------------
// Fetch functions
// ---------------------------------------------------------------------------

const API_BASE = '/api';

/**
 * Fetch all stories from the backend and return them as TopicSummary[].
 * Falls back to mockTopics if the backend is unreachable (e.g. during
 * front-end-only development).
 */
export async function getTopics(): Promise<TopicSummary[]> {
  try {
    const res = await fetch(`${API_BASE}/stories`);
    if (!res.ok) throw new Error(`GET /stories → HTTP ${res.status}`);
    const data: BackendStoryWrapper[] = await res.json();
    return data.map((wrapper, index) => transformStory(wrapper, index));  } catch (err) {
    console.warn('[newsApi] Backend unavailable, falling back to mock data.', err);
    return mockTopics;
  }
}



export async function getTopic(slug: string): Promise<TopicSummary | null> {
  try {
    const res = await fetch(`${API_BASE}/stories/${slug}`);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`GET /stories/${slug} → HTTP ${res.status}`);
    const data: BackendStoryWrapper = await res.json();
    return transformStory(data, 0);
  } catch (err) {
    console.warn(`[newsApi] Backend unavailable for story ${slug}, falling back to mock data.`, err);
    return mockTopics.find(t => t.slug === slug) ?? null;
  }
}


export async function getUsers(): Promise<UserProfile[]> {
  try {
    const res = await fetch(`${API_BASE}/users`);
    if (!res.ok) throw new Error(`GET /users → HTTP ${res.status}`);
    const data: BackendUser[] = await res.json();
    return data.map((user, index) => transformUser(user));  } catch (err) {
    console.warn('[newsApi] Backend unavailable, falling back to mock data.', err);
    return mockUsers;
  }
}

export async function getUser(username: string): Promise<UserProfile | null> {
  try {
    const res = await fetch(`${API_BASE}/user/${username}`);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`GET /user/${username} → HTTP ${res.status}`);
    const data: BackendUser = await res.json();
    return transformUser(data);
  } catch (err) {
    console.warn(`[newsApi] Backend unavailable for user ${username}, falling back to mock data.`, err);
    return mockUsers[0] ?? null;
  }
}

// Re-export the mock helpers so callers can access users / source profiles
// (the backend doesn't have endpoints for these yet).
export { mockUsers };

/**
 * Fetch source profiles from the backend.
 * Falls back to mockSourceProfiles if the backend is unreachable.
 */
export async function getSourceProfiles(): Promise<import('@/types/news').SourceProfile[]> {
  try {
    const res = await fetch(`${API_BASE}/sources`);
    if (!res.ok) throw new Error(`GET /sources → HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('[newsApi] Backend unavailable for sources, falling back to mock data.', err);
    return mockSourceProfiles;
  }
}

/**
 * Fetch a single source profile by ID.
 */
export async function getSourceProfile(sourceId: string): Promise<import('@/types/news').SourceProfile | null> {
  const profiles = await getSourceProfiles();
  return profiles.find(p => p.source.id === sourceId) ?? null;
}
