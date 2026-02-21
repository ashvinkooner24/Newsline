import { TopicSummary, Source, Comment, CommunityNote, UserProfile, SourceProfile } from '@/types/news';

const sources: Record<string, Source> = {
  reuters: { id: 'reuters', name: 'Reuters', url: 'https://reuters.com', credibilityScore: 92, biasLean: 'center', country: 'UK' },
  apnews: { id: 'apnews', name: 'AP News', url: 'https://apnews.com', credibilityScore: 90, biasLean: 'center', country: 'US' },
  nytimes: { id: 'nytimes', name: 'New York Times', url: 'https://nytimes.com', credibilityScore: 85, biasLean: 'center-left', country: 'US' },
  wsj: { id: 'wsj', name: 'Wall Street Journal', url: 'https://wsj.com', credibilityScore: 87, biasLean: 'center-right', country: 'US' },
  bbc: { id: 'bbc', name: 'BBC News', url: 'https://bbc.com', credibilityScore: 88, biasLean: 'center', country: 'UK' },
  foxnews: { id: 'foxnews', name: 'Fox News', url: 'https://foxnews.com', credibilityScore: 62, biasLean: 'right', country: 'US' },
  msnbc: { id: 'msnbc', name: 'MSNBC', url: 'https://msnbc.com', credibilityScore: 60, biasLean: 'left', country: 'US' },
  guardian: { id: 'guardian', name: 'The Guardian', url: 'https://theguardian.com', credibilityScore: 82, biasLean: 'center-left', country: 'UK' },
  aljazeera: { id: 'aljazeera', name: 'Al Jazeera', url: 'https://aljazeera.com', credibilityScore: 75, biasLean: 'center-left', country: 'Qatar' },
  dw: { id: 'dw', name: 'Deutsche Welle', url: 'https://dw.com', credibilityScore: 84, biasLean: 'center', country: 'Germany' },
  scmp: { id: 'scmp', name: 'South China Morning Post', url: 'https://scmp.com', credibilityScore: 72, biasLean: 'center', country: 'China' },
  economist: { id: 'economist', name: 'The Economist', url: 'https://economist.com', credibilityScore: 89, biasLean: 'center-right', country: 'UK' },
  jacobin: { id: 'jacobin', name: 'Jacobin', url: 'https://jacobin.com', credibilityScore: 65, biasLean: 'left', country: 'US' },
  breitbart: { id: 'breitbart', name: 'Breitbart', url: 'https://breitbart.com', credibilityScore: 45, biasLean: 'far-right', country: 'US' },
  abc: { id: 'abc', name: 'ABC News', url: 'https://abcnews.go.com', credibilityScore: 82, biasLean: 'center', country: 'US' },
};

const mockComments: Comment[] = [
  { id: 'c1', userId: 'u1', userName: 'DataDrivenReader', userReputation: 87, text: 'The coverage from Reuters and AP seems most balanced here. Good aggregation.', createdAt: '2026-02-21T08:00:00Z', likes: 24, dislikes: 2 },
  { id: 'c2', userId: 'u2', userName: 'SkepticalObserver', userReputation: 72, text: 'I think the credibility score might be slightly high given the conflicting narratives between sources.', createdAt: '2026-02-21T09:30:00Z', likes: 15, dislikes: 5, replies: [
    { id: 'c3', userId: 'u3', userName: 'MediaAnalyst', userReputation: 91, text: 'Disagreement between sources doesn\'t necessarily reduce credibility — it can indicate a complex issue with multiple valid perspectives.', createdAt: '2026-02-21T10:00:00Z', likes: 32, dislikes: 1 },
  ] },
  { id: 'c4', userId: 'u4', userName: 'NewsJunkie42', userReputation: 65, text: 'Would love to see more international sources represented.', createdAt: '2026-02-20T22:00:00Z', likes: 8, dislikes: 0 },
];

const mockCommunityNotes: CommunityNote[] = [
  { id: 'cn1', userId: 'u3', userName: 'MediaAnalyst', text: 'This summary accurately represents the key positions from all sources. The bias meter correctly reflects the slight lean.', helpfulCount: 45, unhelpfulCount: 3, createdAt: '2026-02-21T07:00:00Z' },
  { id: 'cn2', userId: 'u5', userName: 'FactChecker101', text: 'Note: The Fox News article referenced is an opinion piece, not a news report. This should be factored into credibility scoring.', helpfulCount: 67, unhelpfulCount: 8, createdAt: '2026-02-20T18:00:00Z' },
];

export const mockTopics: TopicSummary[] = [
  {
    id: '1', topic: 'AI Regulation', slug: 'ai-regulation',
    headline: 'Global Push for AI Safety Standards Intensifies as Nations Draft Competing Frameworks',
    summary: 'Multiple nations are racing to establish regulatory frameworks for artificial intelligence, with the EU, US, and China taking divergent approaches that could reshape the global tech landscape.',
    category: 'Technology', country: 'Global', subtopic: 'Artificial Intelligence',
    updatedAt: '2026-02-21T10:30:00Z', isFeatured: true, isBreaking: true,
    sections: [
      { heading: 'EU Leads with Comprehensive Framework', content: 'The European Union has finalized its AI Act enforcement mechanisms, establishing the world\'s most comprehensive regulatory framework for artificial intelligence. The legislation categorizes AI systems by risk level and imposes strict requirements on high-risk applications.', citations: [
        { articleId: 'a1', text: 'EU enforcement mechanisms were finalized in January 2026, according to official commission documents.', biasLevel: 'neutral' },
        { articleId: 'a2', text: 'The framework categorizes AI into four risk tiers, with "unacceptable risk" systems banned outright.', biasLevel: 'neutral' },
      ], stats: { biasLean: 'center', leanScore: -5, credibilityScore: 90, sourceCount: 2, agreement: 88 } },
      { heading: 'US Takes Industry-Friendly Approach', content: 'The United States has opted for a more industry-collaborative approach, with voluntary commitments from major tech companies supplemented by executive orders. Critics argue this creates insufficient guardrails, while proponents say it fosters innovation.', citations: [
        { articleId: 'a3', text: 'Major tech firms unanimously prefer the US voluntary framework, seeing it as innovation-friendly.', biasLevel: 'right' },
        { articleId: 'a4', text: 'The voluntary commitment approach has been widely criticized as toothless by consumer advocates.', biasLevel: 'left' },
      ], stats: { biasLean: 'center', leanScore: 2, credibilityScore: 84, sourceCount: 2, agreement: 62 } },
      { heading: 'China\'s State-Controlled Model', content: 'China has implemented strict content-focused AI regulations requiring all generative AI systems to align with socialist values, while simultaneously investing heavily in AI development for economic competitiveness.', citations: [
        { articleId: 'a5', text: 'China\'s dual approach balances strict ideological controls with aggressive industrial investment.', biasLevel: 'neutral' },
      ], stats: { biasLean: 'center', leanScore: 0, credibilityScore: 86, sourceCount: 1, agreement: 75 } },
    ],
    articles: [
      { id: 'a1', title: 'EU Finalizes AI Act Enforcement Mechanisms', url: '#', source: sources.reuters, publishedAt: '2026-02-20', excerpt: 'The European Commission announced final enforcement guidelines...', tone: 'analytical', toneScore: { emotional: 15, logical: 85 }, factCheck: { verdict: 'verified', details: 'Claims verified against EU official documents.', missingContext: ['Does not mention potential delays in member-state implementation.'] } },
      { id: 'a2', title: 'Understanding the EU\'s Four-Tier AI Risk Framework', url: '#', source: sources.guardian, publishedAt: '2026-02-19', excerpt: 'A deep dive into how the EU categorizes AI risk...', tone: 'analytical', toneScore: { emotional: 20, logical: 80 }, factCheck: { verdict: 'verified', details: 'Accurate representation of the framework tiers.', missingContext: [] } },
      { id: 'a3', title: 'Big Tech Backs Voluntary AI Safety Commitments', url: '#', source: sources.wsj, publishedAt: '2026-02-18', excerpt: 'Major technology companies reaffirm commitment to voluntary guidelines...', tone: 'analytical', toneScore: { emotional: 25, logical: 75 }, factCheck: { verdict: 'mostly-true', details: 'Accurate on corporate positions but omits dissenting voices within industry.', missingContext: ['Several mid-size AI companies opposed voluntary-only approach.'] } },
      { id: 'a4', title: 'Are Voluntary AI Rules Enough?', url: '#', source: sources.nytimes, publishedAt: '2026-02-17', excerpt: 'Editorial examining the limitations of industry self-regulation...', tone: 'emotional', toneScore: { emotional: 55, logical: 45 }, factCheck: { verdict: 'mostly-true', details: 'Opinion piece with factual basis but strong framing.', missingContext: ['Does not acknowledge areas where voluntary compliance has worked.'] } },
      { id: 'a5', title: 'China Balances AI Control and Innovation', url: '#', source: sources.apnews, publishedAt: '2026-02-16', excerpt: 'Beijing seeks to dominate AI while maintaining tight control...', tone: 'balanced', toneScore: { emotional: 30, logical: 70 }, factCheck: { verdict: 'verified', details: 'Factual reporting on Chinese AI policy.', missingContext: [] } },
      { id: 'a6', title: 'AI Safety: A Liberal Fantasy?', url: '#', source: sources.foxnews, publishedAt: '2026-02-15', excerpt: 'Commentary arguing regulations will hamper American competitiveness...', tone: 'emotional', toneScore: { emotional: 72, logical: 28 }, factCheck: { verdict: 'mixed', details: 'Contains valid economic concerns mixed with unsupported claims.', missingContext: ['Omits bipartisan support for basic AI safety measures.', 'Does not mention industry support for some regulation.'] } },
    ],
    biasAnalysis: { overallLean: 'center', leanScore: -8, leftSourceCount: 1, centerSourceCount: 3, rightSourceCount: 2 },
    credibility: { score: 82, articleCount: 6, avgSourceCredibility: 83, sourceAgreement: 72, label: 'High' },
    rating: { accuracy: 4.2, fairness: 3.8, completeness: 3.9, totalRatings: 156 },
    comments: mockComments, communityNotes: mockCommunityNotes,
  },
  {
    id: '2', topic: 'Climate Policy', slug: 'climate-policy',
    headline: 'Record-Breaking Temperatures Force Accelerated Climate Action Discussions',
    summary: 'As 2025 shattered global temperature records, world leaders face mounting pressure to accelerate emissions reduction targets ahead of COP31.',
    category: 'Environment', country: 'Global', subtopic: 'Climate Change',
    updatedAt: '2026-02-20T14:00:00Z', isFeatured: true,
    sections: [
      { heading: 'Temperature Records Broken', content: '2025 was confirmed as the hottest year on record, exceeding the 1.5°C Paris Agreement threshold for the first time on an annual basis.', citations: [
        { articleId: 'b1', text: '2025 exceeded 1.5°C threshold annually for the first time, per NASA and NOAA data.', biasLevel: 'neutral' },
        { articleId: 'b2', text: 'Independent confirmation from multiple agencies leaves no scientific ambiguity.', biasLevel: 'neutral' },
      ], stats: { biasLean: 'center', leanScore: -3, credibilityScore: 94, sourceCount: 2, agreement: 95 } },
      { heading: 'Political Divide Deepens', content: 'Climate policy remains deeply polarized, with progressive leaders calling for emergency measures while conservative voices emphasize economic costs and energy security.', citations: [
        { articleId: 'b3', text: 'The climate crisis demands emergency-level government intervention and a complete overhaul of our energy systems.', biasLevel: 'left' },
        { articleId: 'b4', text: 'Aggressive climate targets could devastate working families and destroy millions of jobs in the energy sector.', biasLevel: 'right' },
      ], stats: { biasLean: 'center', leanScore: -5, credibilityScore: 68, sourceCount: 2, agreement: 35 } },
    ],
    articles: [
      { id: 'b1', title: '2025 Confirmed Hottest Year on Record', url: '#', source: sources.bbc, publishedAt: '2026-02-19', excerpt: 'Global temperatures exceeded 1.5°C above pre-industrial levels...', tone: 'analytical', toneScore: { emotional: 20, logical: 80 }, factCheck: { verdict: 'verified', details: 'Confirmed by NASA, NOAA, and ESA.', missingContext: [] } },
      { id: 'b2', title: 'NASA, NOAA Confirm Record Temperatures', url: '#', source: sources.reuters, publishedAt: '2026-02-18', excerpt: 'US agencies released independent confirmations...', tone: 'analytical', toneScore: { emotional: 10, logical: 90 }, factCheck: { verdict: 'verified', details: 'Direct reporting of agency data.', missingContext: [] } },
      { id: 'b3', title: 'Progressive Caucus Pushes Emergency Climate Plan', url: '#', source: sources.msnbc, publishedAt: '2026-02-17', excerpt: 'Congressional progressives introduced sweeping legislation...', tone: 'emotional', toneScore: { emotional: 65, logical: 35 }, factCheck: { verdict: 'mostly-true', details: 'Accurate on proposals but overstates feasibility.', missingContext: ['Does not address cost estimates or transition timeline challenges.'] } },
      { id: 'b4', title: 'Climate Agenda Could Cost Millions of Jobs', url: '#', source: sources.foxnews, publishedAt: '2026-02-16', excerpt: 'Economic analysis warns of job losses from accelerated targets...', tone: 'emotional', toneScore: { emotional: 70, logical: 30 }, factCheck: { verdict: 'mixed', details: 'Job loss figures come from industry-funded study. Independent estimates are lower.', missingContext: ['Omits job creation in renewable sector.', 'Uses worst-case scenario exclusively.'] } },
      { id: 'b5', title: 'What COP31 Must Achieve', url: '#', source: sources.guardian, publishedAt: '2026-02-15', excerpt: 'Setting expectations for the next climate summit...', tone: 'balanced', toneScore: { emotional: 40, logical: 60 }, factCheck: { verdict: 'mostly-true', details: 'Thoughtful analysis with clear editorial perspective.', missingContext: [] } },
    ],
    biasAnalysis: { overallLean: 'center-left', leanScore: -22, leftSourceCount: 2, centerSourceCount: 2, rightSourceCount: 1 },
    credibility: { score: 76, articleCount: 5, avgSourceCredibility: 78, sourceAgreement: 58, label: 'Medium' },
    rating: { accuracy: 3.9, fairness: 3.3, completeness: 3.6, totalRatings: 203 },
    comments: mockComments, communityNotes: mockCommunityNotes,
  },
  {
    id: '3', topic: 'Housing Crisis', slug: 'housing-crisis',
    headline: 'Urban Housing Affordability Hits Historic Low as Policy Responses Diverge',
    summary: 'Housing costs in major cities have reached unprecedented levels, with governments pursuing vastly different strategies from rent controls to deregulation.',
    category: 'Economy', country: 'US', subtopic: 'Housing',
    updatedAt: '2026-02-19T09:00:00Z',
    sections: [
      { heading: 'Crisis by the Numbers', content: 'The median home price in major metropolitan areas now exceeds 8x median household income, up from 5x a decade ago. Over 50% of renters in top cities spend more than 30% of income on housing.', citations: [
        { articleId: 'c1', text: 'Census data shows the median price-to-income ratio has reached 8x in major metros.', biasLevel: 'neutral' },
        { articleId: 'c2', text: 'More than half of renters across 50 major cities are now considered cost-burdened.', biasLevel: 'neutral' },
      ], stats: { biasLean: 'center', leanScore: -3, credibilityScore: 91, sourceCount: 2, agreement: 90 } },
    ],
    articles: [
      { id: 'c1', title: 'Housing Affordability Reaches Crisis Point', url: '#', source: sources.nytimes, publishedAt: '2026-02-18', excerpt: 'New census data reveals staggering affordability gaps...', tone: 'analytical', toneScore: { emotional: 30, logical: 70 }, factCheck: { verdict: 'verified', details: 'Census data accurately cited.', missingContext: [] } },
      { id: 'c2', title: 'Rent Burden Grows Across Major Cities', url: '#', source: sources.apnews, publishedAt: '2026-02-17', excerpt: 'More than half of renters now housing-cost burdened...', tone: 'balanced', toneScore: { emotional: 20, logical: 80 }, factCheck: { verdict: 'verified', details: 'Based on HUD and census data.', missingContext: [] } },
      { id: 'c3', title: 'Free Market Solutions to Housing Shortage', url: '#', source: sources.wsj, publishedAt: '2026-02-16', excerpt: 'Deregulation could unlock millions of new housing units...', tone: 'analytical', toneScore: { emotional: 25, logical: 75 }, factCheck: { verdict: 'mostly-true', details: 'Deregulation arguments have research support but overstate potential impact.', missingContext: ['Does not address environmental impact of unregulated building.'] } },
    ],
    biasAnalysis: { overallLean: 'center', leanScore: -5, leftSourceCount: 1, centerSourceCount: 1, rightSourceCount: 1 },
    credibility: { score: 88, articleCount: 3, avgSourceCredibility: 87, sourceAgreement: 81, label: 'High' },
    rating: { accuracy: 4.4, fairness: 4.1, completeness: 3.5, totalRatings: 89 },
    comments: mockComments, communityNotes: mockCommunityNotes,
  },
  {
    id: '4', topic: 'Ukraine Conflict', slug: 'ukraine-conflict',
    headline: 'Diplomatic Efforts Intensify as Ceasefire Talks Enter Critical Phase',
    summary: 'International mediators push for a lasting ceasefire agreement as battlefield dynamics shift and humanitarian concerns mount.',
    category: 'Geopolitics', country: 'Ukraine', subtopic: 'War & Conflict',
    updatedAt: '2026-02-21T08:00:00Z', isBreaking: true,
    sections: [
      { heading: 'Ceasefire Negotiations', content: 'Diplomatic envoys from multiple nations have convened in Geneva for what officials describe as the most promising round of ceasefire negotiations since the conflict began. Key sticking points remain territorial sovereignty and security guarantees.', citations: [
        { articleId: 'd1', text: 'Geneva talks represent the most substantive diplomatic engagement since 2024, with both sides showing flexibility.', biasLevel: 'neutral' },
        { articleId: 'd2', text: 'Security guarantees remain the primary obstacle, with NATO involvement a red line for Moscow.', biasLevel: 'neutral' },
      ], stats: { biasLean: 'center', leanScore: -2, credibilityScore: 88, sourceCount: 2, agreement: 82 } },
      { heading: 'Humanitarian Impact', content: 'The UN estimates over 14 million people have been displaced, with critical infrastructure damage affecting access to heating, water, and medical care across eastern regions.', citations: [
        { articleId: 'd3', text: 'UN displacement figures now exceed 14 million, making it one of the largest displacement crises in modern European history.', biasLevel: 'neutral' },
      ], stats: { biasLean: 'center-left', leanScore: -10, credibilityScore: 85, sourceCount: 1, agreement: 78 } },
    ],
    articles: [
      { id: 'd1', title: 'Geneva Talks: A New Window for Peace?', url: '#', source: sources.reuters, publishedAt: '2026-02-21', excerpt: 'Mediators express cautious optimism as talks continue...', tone: 'balanced', toneScore: { emotional: 25, logical: 75 }, factCheck: { verdict: 'verified', details: 'Confirmed by diplomatic sources.', missingContext: [] } },
      { id: 'd2', title: 'NATO\'s Role in Ceasefire Complications', url: '#', source: sources.bbc, publishedAt: '2026-02-20', excerpt: 'Security guarantee demands create deadlock...', tone: 'analytical', toneScore: { emotional: 20, logical: 80 }, factCheck: { verdict: 'verified', details: 'Accurate analysis of negotiation positions.', missingContext: [] } },
      { id: 'd3', title: 'Ukraine\'s Humanitarian Crisis Deepens', url: '#', source: sources.aljazeera, publishedAt: '2026-02-19', excerpt: 'Millions face critical shortages as winter drags on...', tone: 'emotional', toneScore: { emotional: 60, logical: 40 }, factCheck: { verdict: 'verified', details: 'UN data accurately reported.', missingContext: ['Some aid corridors have improved since November.'] } },
      { id: 'd4', title: 'Russia Signals Openness to Talks', url: '#', source: sources.dw, publishedAt: '2026-02-18', excerpt: 'Moscow\'s diplomatic shift raises questions about motives...', tone: 'analytical', toneScore: { emotional: 30, logical: 70 }, factCheck: { verdict: 'mostly-true', details: 'Diplomatic signals are real but context of military situation is underplayed.', missingContext: [] } },
    ],
    biasAnalysis: { overallLean: 'center', leanScore: -6, leftSourceCount: 1, centerSourceCount: 3, rightSourceCount: 0 },
    credibility: { score: 85, articleCount: 4, avgSourceCredibility: 85, sourceAgreement: 78, label: 'High' },
    rating: { accuracy: 4.0, fairness: 3.7, completeness: 3.8, totalRatings: 312 },
    comments: mockComments, communityNotes: mockCommunityNotes,
  },
  {
    id: '5', topic: 'Cryptocurrency Regulation', slug: 'crypto-regulation',
    headline: 'SEC Unveils Landmark Crypto Framework as Bitcoin Surpasses $150K',
    summary: 'US securities regulators introduce comprehensive cryptocurrency oversight rules while market valuations reach all-time highs.',
    category: 'Finance', country: 'US', subtopic: 'Cryptocurrency',
    updatedAt: '2026-02-20T16:00:00Z',
    sections: [
      { heading: 'New Regulatory Framework', content: 'The SEC has released a comprehensive framework distinguishing between securities tokens and utility tokens, providing clarity that the industry has long demanded. Compliance deadlines begin in Q3 2026.', citations: [
        { articleId: 'e1', text: 'The SEC framework provides the first clear legal distinction between token types, resolving years of regulatory ambiguity.', biasLevel: 'neutral' },
        { articleId: 'e2', text: 'This represents a massive government overreach that threatens to stifle the most innovative financial technology in decades.', biasLevel: 'right' },
      ], stats: { biasLean: 'center-right', leanScore: 12, credibilityScore: 80, sourceCount: 2, agreement: 55 } },
    ],
    articles: [
      { id: 'e1', title: 'SEC Crypto Framework: What You Need to Know', url: '#', source: sources.reuters, publishedAt: '2026-02-20', excerpt: 'Comprehensive breakdown of new token classification rules...', tone: 'analytical', toneScore: { emotional: 10, logical: 90 }, factCheck: { verdict: 'verified', details: 'Direct reporting of SEC filings.', missingContext: [] } },
      { id: 'e2', title: 'Crypto Crackdown or Common Sense?', url: '#', source: sources.wsj, publishedAt: '2026-02-19', excerpt: 'Industry reactions split along predictable lines...', tone: 'balanced', toneScore: { emotional: 35, logical: 65 }, factCheck: { verdict: 'mostly-true', details: 'Good representation of both sides but industry quotes cherry-picked.', missingContext: [] } },
      { id: 'e3', title: 'Bitcoin Hits $150K Amid Regulatory Clarity', url: '#', source: sources.economist, publishedAt: '2026-02-18', excerpt: 'Markets rally on regulatory certainty...', tone: 'analytical', toneScore: { emotional: 15, logical: 85 }, factCheck: { verdict: 'verified', details: 'Price data and market analysis verified.', missingContext: [] } },
    ],
    biasAnalysis: { overallLean: 'center-right', leanScore: 15, leftSourceCount: 0, centerSourceCount: 2, rightSourceCount: 1 },
    credibility: { score: 84, articleCount: 3, avgSourceCredibility: 89, sourceAgreement: 70, label: 'High' },
    rating: { accuracy: 4.1, fairness: 3.6, completeness: 3.7, totalRatings: 178 },
    comments: mockComments, communityNotes: mockCommunityNotes,
  },
  {
    id: '6', topic: 'Healthcare Reform', slug: 'healthcare-reform',
    headline: 'Bipartisan Drug Pricing Bill Advances as Pharma Industry Pushes Back',
    summary: 'A rare bipartisan healthcare bill targeting prescription drug costs gains momentum while facing intense industry lobbying.',
    category: 'Health', country: 'US', subtopic: 'Drug Pricing',
    updatedAt: '2026-02-19T11:00:00Z',
    sections: [
      { heading: 'The Bill\'s Key Provisions', content: 'The proposed legislation would allow Medicare to negotiate prices on 50 additional drugs and cap out-of-pocket costs for seniors at $2,000 annually. Both parties have signaled support for the core framework.', citations: [
        { articleId: 'f1', text: 'The bill extends Medicare negotiation powers to 50 drugs beyond the original 10 from the Inflation Reduction Act.', biasLevel: 'neutral' },
        { articleId: 'f2', text: 'The $2,000 cap would provide immediate relief to millions of seniors facing crushing medication costs.', biasLevel: 'left' },
      ], stats: { biasLean: 'center-left', leanScore: -12, credibilityScore: 82, sourceCount: 2, agreement: 75 } },
    ],
    articles: [
      { id: 'f1', title: 'Drug Pricing Bill Clears Committee', url: '#', source: sources.apnews, publishedAt: '2026-02-19', excerpt: 'Bipartisan support overcomes initial industry objections...', tone: 'balanced', toneScore: { emotional: 20, logical: 80 }, factCheck: { verdict: 'verified', details: 'Committee vote and provisions accurately reported.', missingContext: [] } },
      { id: 'f2', title: 'Millions of Seniors Could See Relief', url: '#', source: sources.nytimes, publishedAt: '2026-02-18', excerpt: 'Analysis of how the cap would affect Medicare recipients...', tone: 'emotional', toneScore: { emotional: 50, logical: 50 }, factCheck: { verdict: 'mostly-true', details: 'Impact estimates are from non-partisan CBO.', missingContext: ['Implementation timeline could delay benefits by 18 months.'] } },
      { id: 'f3', title: 'Pharma Warns of Innovation Slowdown', url: '#', source: sources.wsj, publishedAt: '2026-02-17', excerpt: 'Industry argues price controls will reduce R&D investment...', tone: 'analytical', toneScore: { emotional: 30, logical: 70 }, factCheck: { verdict: 'mixed', details: 'R&D claims are disputed by health economists.', missingContext: ['Pharma R&D budgets have increased despite previous price negotiations.'] } },
      { id: 'f4', title: 'The Case for Universal Drug Coverage', url: '#', source: sources.jacobin, publishedAt: '2026-02-16', excerpt: 'Why this bill doesn\'t go far enough...', tone: 'emotional', toneScore: { emotional: 65, logical: 35 }, factCheck: { verdict: 'mixed', details: 'Policy arguments have merit but comparative claims to other nations oversimplified.', missingContext: ['Does not account for differences in healthcare systems.'] } },
    ],
    biasAnalysis: { overallLean: 'center-left', leanScore: -18, leftSourceCount: 2, centerSourceCount: 1, rightSourceCount: 1 },
    credibility: { score: 78, articleCount: 4, avgSourceCredibility: 79, sourceAgreement: 65, label: 'Medium' },
    rating: { accuracy: 3.8, fairness: 3.5, completeness: 3.4, totalRatings: 94 },
    comments: mockComments, communityNotes: mockCommunityNotes,
  },
  {
    id: '7', topic: 'Immigration Policy', slug: 'immigration-policy',
    headline: 'Border Policy Overhaul Proposed Amid Record Migration Numbers',
    summary: 'New legislative proposals aim to reform the immigration system as border encounters reach unprecedented levels and labor shortages persist.',
    category: 'Politics', country: 'US', subtopic: 'Immigration',
    updatedAt: '2026-02-18T13:00:00Z',
    sections: [
      { heading: 'Record Migration Figures', content: 'Border encounters exceeded 3 million in 2025, the highest on record. Asylum processing backlogs now stretch over 5 years, leaving millions in legal limbo.', citations: [
        { articleId: 'g1', text: 'CBP data confirms 3.1 million encounters in fiscal year 2025, a 15% increase over the previous record.', biasLevel: 'neutral' },
        { articleId: 'g2', text: 'The border crisis is a direct result of failed progressive open-border policies.', biasLevel: 'right' },
        { articleId: 'g3', text: 'These migrants are fleeing desperate conditions and deserve a humane pathway to safety.', biasLevel: 'left' },
      ], stats: { biasLean: 'center', leanScore: 5, credibilityScore: 72, sourceCount: 3, agreement: 40 } },
    ],
    articles: [
      { id: 'g1', title: '2025 Border Encounters Hit Record High', url: '#', source: sources.apnews, publishedAt: '2026-02-18', excerpt: 'Official CBP statistics reveal unprecedented numbers...', tone: 'analytical', toneScore: { emotional: 15, logical: 85 }, factCheck: { verdict: 'verified', details: 'CBP data accurately reported.', missingContext: [] } },
      { id: 'g2', title: 'Border Security Must Come First', url: '#', source: sources.foxnews, publishedAt: '2026-02-17', excerpt: 'Commentary on prioritizing enforcement over amnesty...', tone: 'emotional', toneScore: { emotional: 75, logical: 25 }, factCheck: { verdict: 'mixed', details: 'Valid security concerns mixed with unsupported policy claims.', missingContext: ['Does not mention labor market needs for immigrant workers.'] } },
      { id: 'g3', title: 'The Human Cost of Immigration Limbo', url: '#', source: sources.msnbc, publishedAt: '2026-02-16', excerpt: 'Families trapped in years-long asylum backlogs...', tone: 'emotional', toneScore: { emotional: 70, logical: 30 }, factCheck: { verdict: 'mostly-true', details: 'Human interest stories are real but presented without policy tradeoff context.', missingContext: ['Does not address security screening requirements.'] } },
      { id: 'g4', title: 'Immigration Reform: A Bipartisan Path?', url: '#', source: sources.abc, publishedAt: '2026-02-15', excerpt: 'Moderate lawmakers seek middle ground...', tone: 'balanced', toneScore: { emotional: 30, logical: 70 }, factCheck: { verdict: 'mostly-true', details: 'Good overview of bipartisan efforts.', missingContext: [] } },
    ],
    biasAnalysis: { overallLean: 'center', leanScore: 5, leftSourceCount: 1, centerSourceCount: 2, rightSourceCount: 1 },
    credibility: { score: 71, articleCount: 4, avgSourceCredibility: 74, sourceAgreement: 42, label: 'Medium' },
    rating: { accuracy: 3.5, fairness: 3.0, completeness: 3.3, totalRatings: 267 },
    comments: mockComments, communityNotes: mockCommunityNotes,
  },
  {
    id: '8', topic: 'Space Exploration', slug: 'space-exploration',
    headline: 'Artemis III Moon Landing Date Set as Commercial Space Race Accelerates',
    summary: 'NASA confirms a 2027 crewed lunar landing while SpaceX and Blue Origin compete for the next generation of space infrastructure contracts.',
    category: 'Science', country: 'US', subtopic: 'Space',
    updatedAt: '2026-02-17T10:00:00Z',
    sections: [
      { heading: 'Artemis III Timeline Confirmed', content: 'NASA has officially set September 2027 for the Artemis III crewed lunar landing, which will include the first woman and first person of color to walk on the Moon. The Starship lunar lander has completed all key testing milestones.', citations: [
        { articleId: 'h1', text: 'NASA Administrator confirmed the September 2027 date in a press conference at Johnson Space Center.', biasLevel: 'neutral' },
        { articleId: 'h2', text: 'SpaceX\'s Starship lunar lander passed final orbital refueling tests in January.', biasLevel: 'neutral' },
      ], stats: { biasLean: 'center', leanScore: 0, credibilityScore: 92, sourceCount: 2, agreement: 95 } },
    ],
    articles: [
      { id: 'h1', title: 'NASA Sets Artemis III for September 2027', url: '#', source: sources.reuters, publishedAt: '2026-02-17', excerpt: 'Official announcement confirms timeline for historic landing...', tone: 'analytical', toneScore: { emotional: 15, logical: 85 }, factCheck: { verdict: 'verified', details: 'Direct from NASA press conference.', missingContext: [] } },
      { id: 'h2', title: 'Starship Clears Final Hurdle for Moon Mission', url: '#', source: sources.bbc, publishedAt: '2026-02-16', excerpt: 'SpaceX completes critical orbital refueling demonstration...', tone: 'balanced', toneScore: { emotional: 25, logical: 75 }, factCheck: { verdict: 'verified', details: 'SpaceX test data confirmed by independent observers.', missingContext: [] } },
      { id: 'h3', title: 'The New Space Race: Who Will Build the Moon Base?', url: '#', source: sources.economist, publishedAt: '2026-02-15', excerpt: 'Commercial competition drives down costs and speeds up timelines...', tone: 'analytical', toneScore: { emotional: 20, logical: 80 }, factCheck: { verdict: 'mostly-true', details: 'Good analysis with some speculative cost projections.', missingContext: [] } },
    ],
    biasAnalysis: { overallLean: 'center', leanScore: 2, leftSourceCount: 0, centerSourceCount: 3, rightSourceCount: 0 },
    credibility: { score: 91, articleCount: 3, avgSourceCredibility: 90, sourceAgreement: 92, label: 'High' },
    rating: { accuracy: 4.6, fairness: 4.5, completeness: 4.2, totalRatings: 145 },
    comments: mockComments, communityNotes: mockCommunityNotes,
  },
  {
    id: '9', topic: 'Education Reform', slug: 'education-reform',
    headline: 'AI Tutoring Revolution Sparks Debate Over Future of Traditional Schooling',
    summary: 'Rapid adoption of AI-powered personalized tutoring is producing remarkable results while raising concerns about equity and the role of human teachers.',
    category: 'Education', country: 'US', subtopic: 'EdTech',
    updatedAt: '2026-02-16T09:00:00Z',
    sections: [
      { heading: 'AI Tutoring Results', content: 'A Stanford study found that students using AI tutoring systems for one semester showed learning gains equivalent to two years of traditional instruction in mathematics. The technology is now deployed in over 15,000 US schools.', citations: [
        { articleId: 'i1', text: 'Stanford\'s randomized controlled trial showed 2x learning acceleration in mathematics with AI tutoring.', biasLevel: 'neutral' },
        { articleId: 'i2', text: 'AI tutoring offers the potential to finally close achievement gaps that decades of policy have failed to address.', biasLevel: 'left' },
      ], stats: { biasLean: 'center', leanScore: -8, credibilityScore: 83, sourceCount: 2, agreement: 72 } },
    ],
    articles: [
      { id: 'i1', title: 'Stanford Study: AI Tutors Double Learning Speed', url: '#', source: sources.apnews, publishedAt: '2026-02-16', excerpt: 'Landmark study confirms AI tutoring effectiveness...', tone: 'analytical', toneScore: { emotional: 15, logical: 85 }, factCheck: { verdict: 'verified', details: 'Peer-reviewed study accurately reported.', missingContext: ['Study focused on math only; results may not generalize.'] } },
      { id: 'i2', title: 'Can AI Close the Education Gap?', url: '#', source: sources.nytimes, publishedAt: '2026-02-15', excerpt: 'Equity implications of AI-driven education...', tone: 'balanced', toneScore: { emotional: 35, logical: 65 }, factCheck: { verdict: 'mostly-true', details: 'Good analysis with appropriate caveats.', missingContext: [] } },
      { id: 'i3', title: 'Teachers Union: AI Threatens Profession', url: '#', source: sources.guardian, publishedAt: '2026-02-14', excerpt: 'Educators worry about replacement and devaluation...', tone: 'emotional', toneScore: { emotional: 55, logical: 45 }, factCheck: { verdict: 'mostly-true', details: 'Union concerns are real but presented without counterpoint from districts.', missingContext: ['Most implementations augment rather than replace teachers.'] } },
    ],
    biasAnalysis: { overallLean: 'center-left', leanScore: -12, leftSourceCount: 1, centerSourceCount: 1, rightSourceCount: 1 },
    credibility: { score: 80, articleCount: 3, avgSourceCredibility: 83, sourceAgreement: 68, label: 'High' },
    rating: { accuracy: 4.0, fairness: 3.7, completeness: 3.5, totalRatings: 76 },
    comments: mockComments, communityNotes: mockCommunityNotes,
  },
  {
    id: '10', topic: 'Global Trade Wars', slug: 'global-trade-wars',
    headline: 'New Tariff Escalation Threatens Global Supply Chains as Allies Retaliate',
    summary: 'Expanding trade barriers between major economies are disrupting supply chains and raising consumer prices, with no diplomatic resolution in sight.',
    category: 'Economy', country: 'Global', subtopic: 'Trade',
    updatedAt: '2026-02-21T06:00:00Z', isFeatured: true,
    sections: [
      { heading: 'Tariff Escalation', content: 'The latest round of tariffs affects $500 billion in goods, with retaliatory measures from the EU, China, and Canada. Economists warn of significant GDP impact across all affected economies.', citations: [
        { articleId: 'j1', text: 'The tariff package is the largest in modern history, affecting $500B in bilateral trade across multiple sectors.', biasLevel: 'neutral' },
        { articleId: 'j2', text: 'Tariffs are a necessary tool to protect domestic industries from unfair foreign competition.', biasLevel: 'right' },
        { articleId: 'j3', text: 'These tariffs amount to a tax on American consumers and will disproportionately harm low-income families.', biasLevel: 'left' },
      ], stats: { biasLean: 'center', leanScore: 3, credibilityScore: 78, sourceCount: 3, agreement: 50 } },
      { heading: 'Supply Chain Disruption', content: 'Major manufacturers are scrambling to restructure supply chains as tariffs make established trade routes economically unviable. Southeast Asian nations are emerging as alternative manufacturing hubs.', citations: [
        { articleId: 'j4', text: 'Vietnam and India have seen a 40% increase in manufacturing investment inquiries since the tariff announcement.', biasLevel: 'neutral' },
      ], stats: { biasLean: 'center', leanScore: 0, credibilityScore: 86, sourceCount: 1, agreement: 80 } },
    ],
    articles: [
      { id: 'j1', title: '$500B Tariff Package: Full Analysis', url: '#', source: sources.reuters, publishedAt: '2026-02-21', excerpt: 'Comprehensive breakdown of the new trade barriers...', tone: 'analytical', toneScore: { emotional: 10, logical: 90 }, factCheck: { verdict: 'verified', details: 'Trade data from official government sources.', missingContext: [] } },
      { id: 'j2', title: 'Why Tariffs Are Working', url: '#', source: sources.foxnews, publishedAt: '2026-02-20', excerpt: 'Defense of protectionist trade policy...', tone: 'emotional', toneScore: { emotional: 60, logical: 40 }, factCheck: { verdict: 'mixed', details: 'Cherry-picks successful cases while ignoring broader economic consensus.', missingContext: ['Most economists disagree that tariffs benefit overall economy.'] } },
      { id: 'j3', title: 'Trade War Hits Consumer Wallets', url: '#', source: sources.nytimes, publishedAt: '2026-02-19', excerpt: 'How tariffs translate to higher prices for everyday goods...', tone: 'balanced', toneScore: { emotional: 40, logical: 60 }, factCheck: { verdict: 'verified', details: 'Consumer price impact verified by BLS data.', missingContext: [] } },
      { id: 'j4', title: 'Supply Chain Shift: Asia\'s New Manufacturing Hubs', url: '#', source: sources.scmp, publishedAt: '2026-02-18', excerpt: 'Vietnam and India capitalize on trade disruption...', tone: 'analytical', toneScore: { emotional: 15, logical: 85 }, factCheck: { verdict: 'mostly-true', details: 'Investment figures from ASEAN data sources.', missingContext: ['Capacity constraints may limit how quickly production can shift.'] } },
      { id: 'j5', title: 'EU Retaliatory Tariffs Target US Tech', url: '#', source: sources.dw, publishedAt: '2026-02-17', excerpt: 'European response focuses on American tech sector...', tone: 'analytical', toneScore: { emotional: 20, logical: 80 }, factCheck: { verdict: 'verified', details: 'EU official statements accurately reported.', missingContext: [] } },
    ],
    biasAnalysis: { overallLean: 'center', leanScore: 5, leftSourceCount: 1, centerSourceCount: 3, rightSourceCount: 1 },
    credibility: { score: 81, articleCount: 5, avgSourceCredibility: 81, sourceAgreement: 62, label: 'High' },
    rating: { accuracy: 4.0, fairness: 3.6, completeness: 4.1, totalRatings: 198 },
    comments: mockComments, communityNotes: mockCommunityNotes,
  },
];

export const mockUsers: UserProfile[] = [
  { id: 'u1', name: 'DataDrivenReader', joinedAt: '2025-06-15', articlesRead: 342, commentsCount: 28, biasLean: 'center', leanScore: -3, reputation: 87, isPublic: true },
  { id: 'u2', name: 'SkepticalObserver', joinedAt: '2025-09-01', articlesRead: 198, commentsCount: 45, biasLean: 'center-left', leanScore: -15, reputation: 72, isPublic: true },
  { id: 'u3', name: 'MediaAnalyst', joinedAt: '2025-03-20', articlesRead: 567, commentsCount: 89, biasLean: 'center', leanScore: 2, reputation: 91, isPublic: true },
  { id: 'u4', name: 'NewsJunkie42', joinedAt: '2025-11-10', articlesRead: 112, commentsCount: 12, biasLean: 'center-right', leanScore: 18, reputation: 65, isPublic: false },
  { id: 'u5', name: 'FactChecker101', joinedAt: '2025-01-05', articlesRead: 890, commentsCount: 156, biasLean: 'center', leanScore: -1, reputation: 95, isPublic: true },
];

export const mockSourceProfiles: SourceProfile[] = Object.values(sources).map(s => ({
  source: s,
  totalArticles: Math.floor(Math.random() * 500) + 100,
  avgCredibility: s.credibilityScore,
  biasHistory: [
    { month: '2025-09', leanScore: s.biasLean === 'left' ? -45 : s.biasLean === 'right' ? 42 : s.biasLean === 'center-left' ? -20 : s.biasLean === 'center-right' ? 22 : 0 },
    { month: '2025-12', leanScore: s.biasLean === 'left' ? -48 : s.biasLean === 'right' ? 45 : s.biasLean === 'center-left' ? -22 : s.biasLean === 'center-right' ? 20 : -2 },
    { month: '2026-02', leanScore: s.biasLean === 'left' ? -44 : s.biasLean === 'right' ? 40 : s.biasLean === 'center-left' ? -18 : s.biasLean === 'center-right' ? 24 : 1 },
  ],
  topTopics: ['AI Regulation', 'Climate Policy', 'Economy'],
}));

export const allCategories = [...new Set(mockTopics.map(t => t.category))];
export const allCountries = [...new Set(mockTopics.map(t => t.country))];
export const allSubtopics = [...new Set(mockTopics.filter(t => t.subtopic).map(t => t.subtopic!))];
