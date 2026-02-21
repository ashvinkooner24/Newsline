export type BiasLean = 'far-left' | 'left' | 'center-left' | 'center' | 'center-right' | 'right' | 'far-right';

export type ToneType = 'emotional' | 'balanced' | 'analytical' | 'sensational';

export interface Source {
  id: string;
  name: string;
  url: string;
  credibilityScore: number;
  biasLean: BiasLean;
  country: string;
}

export interface Article {
  id: string;
  title: string;
  url: string;
  source: Source;
  publishedAt: string;
  excerpt: string;
  tone?: ToneType;
  toneScore?: { emotional: number; logical: number };
  factCheck?: FactCheck;
}

export interface Citation {
  articleId: string;
  text: string;
  biasLevel?: 'left' | 'right' | 'neutral';
}

export interface SectionStats {
  biasLean: BiasLean;
  leanScore: number;
  credibilityScore: number;
  sourceCount: number;
  agreement: number;
}

export interface SummarySection {
  heading: string;
  content: string;
  citations: Citation[];
  stats?: SectionStats;
}

export interface BiasAnalysis {
  overallLean: BiasLean;
  leanScore: number;
  leftSourceCount: number;
  centerSourceCount: number;
  rightSourceCount: number;
}

export interface CredibilityAssessment {
  score: number;
  articleCount: number;
  avgSourceCredibility: number;
  sourceAgreement: number;
  label: 'High' | 'Medium' | 'Low' | 'Uncertain';
}

export interface FactCheck {
  verdict: 'verified' | 'mostly-true' | 'mixed' | 'misleading' | 'unverified';
  details: string;
  missingContext: string[];
}

export interface Comment {
  id: string;
  userId: string;
  userName: string;
  userReputation: number;
  text: string;
  createdAt: string;
  likes: number;
  dislikes: number;
  replies?: Comment[];
}

export interface CommunityNote {
  id: string;
  userId: string;
  userName: string;
  text: string;
  helpfulCount: number;
  unhelpfulCount: number;
  createdAt: string;
}

export interface Rating {
  accuracy: number;
  fairness: number;
  completeness: number;
  totalRatings: number;
}

export interface UserProfile {
  id: string;
  name: string;
  joinedAt: string;
  articlesRead: number;
  commentsCount: number;
  biasLean: BiasLean;
  leanScore: number;
  reputation: number;
  isPublic: boolean;
}

export interface SourceProfile {
  source: Source;
  totalArticles: number;
  avgCredibility: number;
  biasHistory: { month: string; leanScore: number }[];
  topTopics: string[];
}

export interface TopicSummary {
  id: string;
  topic: string;
  slug: string;
  headline: string;
  summary: string;
  sections: SummarySection[];
  articles: Article[];
  biasAnalysis: BiasAnalysis;
  credibility: CredibilityAssessment;
  updatedAt: string;
  category: string;
  country: string;
  subtopic?: string;
  isFeatured?: boolean;
  isBreaking?: boolean;
  rating?: Rating;
  comments?: Comment[];
  communityNotes?: CommunityNote[];
}
