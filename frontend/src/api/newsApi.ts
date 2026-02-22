/**
 * newsApi.ts
 *
 * Data-fetching layer for The Newsline backend.
 *
 * All requests go through the Vite dev proxy (/api → http://127.0.0.1:8000),
 * so no CORS issues during development.
 *
 * The backend serves models defined in ``backend/models.py`` using
 * **snake_case** field names.  This file declares matching ``Backend*``
 * interfaces and provides ``transform*`` functions that map them into the
 * **camelCase** frontend types from ``@/types/news``.
 *
 * When the backend is unreachable the fetch helpers fall back to
 * ``@/data/mockNews`` so the frontend can be developed independently.
 */

import type {
  TopicSummary,
  Source,
  Article,
  UserProfile,
  Comment,
  CommunityNote,
  SummarySection,
  BiasAnalysis,
  CredibilityAssessment,
  BiasLean,
  Citation,
  SectionStats,
  ToneType,
  FactCheck,
  Rating,
} from '@/types/news';
import { mockTopics, mockUsers, mockSourceProfiles } from '@/data/mockNews';

// ─────────────────────────────────────────────────────────────────────────────
// Backend response shapes  (mirror backend/models.py — all snake_case)
// ─────────────────────────────────────────────────────────────────────────────

export interface BackendNewsSource {
  id: string;
  name: string;
  url: string;
  credibility_score: number;
  bias_lean: string;
  country: string;
}

export interface BackendToneScore {
  emotional: number;
  logical: number;
}

export interface BackendFactCheck {
  verdict: string;
  details: string;
  missing_context: string[];
}

export interface BackendArticle {
  id: string;
  title: string;
  url: string;
  source: BackendNewsSource;
  published_at: string;
  excerpt: string;
  tone: string | null;
  tone_score: BackendToneScore | null;
  fact_check: BackendFactCheck | null;
}

export interface BackendCitation {
  article_id: string;
  text: string;
  bias_level: string | null;
}

export interface BackendSectionStats {
  bias_lean: string;
  lean_score: number;
  credibility_score: number;
  source_count: number;
  agreement: number;
}

export interface BackendSummarySection {
  heading: string;
  content: string;
  citations: BackendCitation[];
  stats: BackendSectionStats | null;
}

export interface BackendBiasAnalysis {
  overall_lean: string;
  lean_score: number;
  left_source_count: number;
  center_source_count: number;
  right_source_count: number;
}

export interface BackendCredibilityAssessment {
  score: number;
  article_count: number;
  avg_source_credibility: number;
  source_agreement: number;
  label: string;
}

export interface BackendComment {
  id: string;
  user_id: string;
  user_name: string;
  user_reputation: number;
  text: string;
  created_at: string;
  likes: number;
  dislikes: number;
  replies: BackendComment[];
}

export interface BackendCommunityNote {
  id: string;
  user_id: string;
  user_name: string;
  text: string;
  helpful_count: number;
  unhelpful_count: number;
  created_at: string;
}

export interface BackendRating {
  accuracy: number;
  fairness: number;
  completeness: number;
  total_ratings: number;
}

export interface BackendTopicSummary {
  id: string;
  topic: string;
  slug: string;
  headline: string;
  summary: string;
  sections: BackendSummarySection[];
  articles: BackendArticle[];
  bias_analysis: BackendBiasAnalysis;
  credibility: BackendCredibilityAssessment;
  updated_at: string;
  category: string;
  country: string;
  subtopic: string | null;
  is_featured: boolean;
  is_breaking: boolean;
  rating: BackendRating | null;
  comments: BackendComment[];
  community_notes: BackendCommunityNote[];
}

export interface BackendUserProfile {
  id: string;
  name: string;
  joined_at: string;
  articles_read: number;
  comments_count: number;
  bias_lean: string;
  lean_score: number;
  reputation: number;
  is_public: boolean;
}

// ─────────────────────────────────────────────────────────────────────────────
// Transformation helpers  (snake_case backend → camelCase frontend)
// ─────────────────────────────────────────────────────────────────────────────

function transformSource(src: BackendNewsSource): Source {
  return {
    id: src.id,
    name: src.name,
    url: src.url,
    credibilityScore: src.credibility_score,
    biasLean: src.bias_lean as BiasLean,
    country: src.country,
  };
}

function transformArticle(a: BackendArticle): Article {
  return {
    id: a.id,
    title: a.title,
    url: a.url,
    source: transformSource(a.source),
    publishedAt: a.published_at,
    excerpt: a.excerpt,
    tone: (a.tone ?? undefined) as ToneType | undefined,
    toneScore: a.tone_score ?? undefined,
    factCheck: a.fact_check
      ? {
          verdict: a.fact_check.verdict as FactCheck['verdict'],
          details: a.fact_check.details,
          missingContext: a.fact_check.missing_context,
        }
      : undefined,
  };
}

function transformCitation(c: BackendCitation): Citation {
  return {
    articleId: c.article_id,
    text: c.text,
    biasLevel: (c.bias_level ?? undefined) as Citation['biasLevel'],
  };
}

function transformSectionStats(s: BackendSectionStats): SectionStats {
  return {
    biasLean: s.bias_lean as BiasLean,
    leanScore: s.lean_score,
    credibilityScore: s.credibility_score,
    sourceCount: s.source_count,
    agreement: s.agreement,
  };
}

function transformSection(sec: BackendSummarySection): SummarySection {
  return {
    heading: sec.heading,
    content: sec.content,
    citations: sec.citations.map(transformCitation),
    stats: sec.stats ? transformSectionStats(sec.stats) : undefined,
  };
}

function transformBiasAnalysis(ba: BackendBiasAnalysis): BiasAnalysis {
  return {
    overallLean: ba.overall_lean as BiasLean,
    leanScore: ba.lean_score,
    leftSourceCount: ba.left_source_count,
    centerSourceCount: ba.center_source_count,
    rightSourceCount: ba.right_source_count,
  };
}

function transformCredibility(c: BackendCredibilityAssessment): CredibilityAssessment {
  return {
    score: c.score,
    articleCount: c.article_count,
    avgSourceCredibility: c.avg_source_credibility,
    sourceAgreement: c.source_agreement,
    label: c.label as CredibilityAssessment['label'],
  };
}

function transformComment(c: BackendComment): Comment {
  return {
    id: c.id,
    userId: c.user_id,
    userName: c.user_name,
    userReputation: c.user_reputation,
    text: c.text,
    createdAt: c.created_at,
    likes: c.likes,
    dislikes: c.dislikes,
    replies: c.replies?.map(transformComment),
  };
}

function transformCommunityNote(n: BackendCommunityNote): CommunityNote {
  return {
    id: n.id,
    userId: n.user_id,
    userName: n.user_name,
    text: n.text,
    helpfulCount: n.helpful_count,
    unhelpfulCount: n.unhelpful_count,
    createdAt: n.created_at,
  };
}

function transformRating(r: BackendRating): Rating {
  return {
    accuracy: r.accuracy,
    fairness: r.fairness,
    completeness: r.completeness,
    totalRatings: r.total_ratings,
  };
}

/**
 * Main transformer: BackendTopicSummary → frontend TopicSummary.
 */
export function transformTopicSummary(t: BackendTopicSummary): TopicSummary {
  return {
    id: t.id,
    topic: t.topic,
    slug: t.slug,
    headline: t.headline,
    summary: t.summary,
    sections: t.sections.map(transformSection),
    articles: t.articles.map(transformArticle),
    biasAnalysis: transformBiasAnalysis(t.bias_analysis),
    credibility: transformCredibility(t.credibility),
    updatedAt: t.updated_at,
    category: t.category,
    country: t.country,
    subtopic: t.subtopic ?? undefined,
    isFeatured: t.is_featured,
    isBreaking: t.is_breaking,
    rating: t.rating ? transformRating(t.rating) : undefined,
    comments: t.comments.map(transformComment),
    communityNotes: t.community_notes.map(transformCommunityNote),
  };
}

/**
 * Transform a BackendUserProfile → frontend UserProfile.
 */
export function transformUser(u: BackendUserProfile): UserProfile {
  return {
    id: u.id,
    name: u.name,
    joinedAt: u.joined_at,
    articlesRead: u.articles_read,
    commentsCount: u.comments_count,
    biasLean: u.bias_lean as BiasLean,
    leanScore: u.lean_score,
    reputation: u.reputation,
    isPublic: u.is_public,
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Fetch functions
// ─────────────────────────────────────────────────────────────────────────────

const API_BASE = '/api';

/**
 * Fetch all stories from the backend and return them as TopicSummary[].
 * Falls back to mockTopics if the backend is unreachable.
 */
export async function getTopics(): Promise<TopicSummary[]> {
  try {
    const res = await fetch(`${API_BASE}/stories`);
    if (!res.ok) throw new Error(`GET /stories → HTTP ${res.status}`);
    const data: BackendTopicSummary[] = await res.json();
    return data.map(transformTopicSummary);
  } catch (err) {
    console.warn('[newsApi] Backend unavailable, falling back to mock data.', err);
    return mockTopics;
  }
}

/**
 * Fetch a single story by slug.
 */
export async function getTopic(slug: string): Promise<TopicSummary | null> {
  try {
    const res = await fetch(`${API_BASE}/stories/${slug}`);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`GET /stories/${slug} → HTTP ${res.status}`);
    const data: BackendTopicSummary = await res.json();
    return transformTopicSummary(data);
  } catch (err) {
    console.warn(`[newsApi] Backend unavailable for story ${slug}, falling back to mock data.`, err);
    return mockTopics.find(t => t.slug === slug) ?? null;
  }
}

/**
 * Fetch all users.
 */
export async function getUsers(): Promise<UserProfile[]> {
  try {
    const res = await fetch(`${API_BASE}/users`);
    if (!res.ok) throw new Error(`GET /users → HTTP ${res.status}`);
    const data: BackendUserProfile[] = await res.json();
    return data.map(transformUser);
  } catch (err) {
    console.warn('[newsApi] Backend unavailable, falling back to mock data.', err);
    return mockUsers;
  }
}

/**
 * Fetch a single user by id or name.
 */
export async function getUser(userId: string): Promise<UserProfile | null> {
  try {
    const res = await fetch(`${API_BASE}/user/${userId}`);
    if (res.status === 404) return null;
    if (!res.ok) throw new Error(`GET /user/${userId} → HTTP ${res.status}`);
    const data: BackendUserProfile = await res.json();
    return transformUser(data);
  } catch (err) {
    console.warn(`[newsApi] Backend unavailable for user ${userId}, falling back to mock data.`, err);
    return mockUsers.find(u => u.id === userId) ?? null;
  }
}

// Re-export mock helpers for callers that need them directly
export { mockUsers, mockSourceProfiles };
