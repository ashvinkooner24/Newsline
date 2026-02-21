"""
Mock data: three fully populated aggregated articles for development & testing.

Topics:
  1. Federal Reserve interest-rate hike (economics)
  2. COP32 climate summit agreement (environment)
  3. US Senate AI Governance Act (technology / politics)
"""

from __future__ import annotations

from models.article import Article, Segment, SourceReference, PoliticalBiasLabel, bias_score_to_label
from models.topic import Topic, CitationMapping

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _src(name, bias, cred, url=None, published_at=None):
    return SourceReference.create(
        name=name,
        political_bias_score=bias,
        credibility_score=cred,
        url=url,
        published_at=published_at,
    )


def _avg_bias(sources: list[SourceReference]) -> float:
    return round(sum(s.political_bias_score for s in sources) / len(sources), 3)


# ===========================================================================
# ARTICLE 1 — Federal Reserve Interest Rate Hike
# ===========================================================================

_fed_reuters = _src(
    "Reuters", 0.02, 0.92,
    url="https://www.reuters.com/business/finance/fed-raises-rates-55-percent-2026-02-19",
    published_at="2026-02-19T18:00:00Z",
)
_fed_bloomberg = _src(
    "Bloomberg", 0.18, 0.91,
    url="https://www.bloomberg.com/news/articles/2026-02-19/fed-rate-hike-55",
    published_at="2026-02-19T18:05:00Z",
)
_fed_wsj = _src(
    "The Wall Street Journal", 0.22, 0.89,
    url="https://www.wsj.com/articles/fed-raises-interest-rates-highest-in-decade-2026",
    published_at="2026-02-19T18:10:00Z",
)
_fed_guardian = _src(
    "The Guardian", -0.22, 0.86,
    url="https://www.theguardian.com/business/2026/feb/19/federal-reserve-rate-hike-workers",
    published_at="2026-02-19T19:30:00Z",
)
_fed_foxbiz = _src(
    "Fox Business", 0.48, 0.77,
    url="https://www.foxbusiness.com/economy/fed-hikes-rates-again-inflation-fight",
    published_at="2026-02-19T19:00:00Z",
)

_fed_all_sources = [_fed_reuters, _fed_bloomberg, _fed_wsj, _fed_guardian, _fed_foxbiz]

_fed_seg1_sources = [_fed_reuters, _fed_bloomberg, _fed_wsj, _fed_guardian, _fed_foxbiz]
_fed_seg2_sources = [_fed_reuters, _fed_bloomberg, _fed_wsj]
_fed_seg3_sources = [_fed_bloomberg, _fed_wsj, _fed_foxbiz]
_fed_seg4_sources = [_fed_reuters, _fed_guardian]
_fed_seg5_sources = [_fed_guardian, _fed_foxbiz]
_fed_seg6_sources = [_fed_reuters, _fed_bloomberg]

FED_SEGMENTS = [
    Segment(
        segment_id="fed-seg-1",
        text=(
            "The Federal Reserve raised its benchmark interest rate by 25 basis points on Wednesday, "
            "lifting the federal funds rate to a target range of 5.25–5.50 percent — the highest level "
            "since June 2001. The unanimous decision by the Federal Open Market Committee (FOMC) was "
            "widely anticipated by markets and marks the eleventh rate increase in the current tightening "
            "cycle that began in March 2022. The Fed's statement cited 'continued elevated inflation and "
            "a resilient labor market' as the primary justifications for sustained policy action."
        ),
        sources=_fed_seg1_sources,
        num_articles=5,
        avg_political_bias_score=_avg_bias(_fed_seg1_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_fed_seg1_sources)),
        truth_value=0.97,
        additional_notes=(
            "Unanimously reported across all five sources with consistent factual detail. "
            "Rate range and FOMC vote count are confirmed by the official Fed press release."
        ),
    ),
    Segment(
        segment_id="fed-seg-2",
        text=(
            "Fed Chair Jerome Powell, speaking at a post-meeting press conference, acknowledged that "
            "progress on inflation has been 'significant but uneven.' He stressed that the Fed is "
            "'prepared to raise rates further if appropriate' while also signalling that the pace of "
            "hikes has slowed compared with 2022. Powell pushed back against market expectations of "
            "rate cuts before year-end, stating: 'It would not be appropriate to dial back our policy "
            "restraint when inflation remains meaningfully above our two-percent goal.' He pointed to "
            "the core PCE index — the Fed's preferred measure — running at 3.7 percent year-over-year "
            "as evidence that the job is not yet finished."
        ),
        sources=_fed_seg2_sources,
        num_articles=3,
        avg_political_bias_score=_avg_bias(_fed_seg2_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_fed_seg2_sources)),
        truth_value=0.95,
        additional_notes=(
            "Powell quotes are consistent across Reuters, Bloomberg, and WSJ transcripts. "
            "Core PCE figure of 3.7% is sourced from the January 2026 BEA release."
        ),
    ),
    Segment(
        segment_id="fed-seg-3",
        text=(
            "Financial markets responded with modest volatility. The S&P 500 initially fell 0.8 percent "
            "before recovering to close down 0.3 percent on the day, as traders processed Powell's hawkish "
            "guidance. The two-year Treasury yield — most sensitive to near-term rate expectations — edged "
            "up 6 basis points to 4.91 percent, while the ten-year yield was broadly unchanged at 4.42 percent. "
            "The dollar index (DXY) strengthened 0.4 percent. Bloomberg's rate probability model shifted "
            "to price in a 58 percent chance of a further 25-bps hike at the May FOMC meeting, up from "
            "41 percent before the press conference."
        ),
        sources=_fed_seg3_sources,
        num_articles=3,
        avg_political_bias_score=_avg_bias(_fed_seg3_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_fed_seg3_sources)),
        truth_value=0.91,
        additional_notes=(
            "Market figures are intraday snapshots and may differ slightly across sources depending on "
            "data provider and timestamp. Fox Business reported a slightly larger S&P decline of 0.5% "
            "at close due to a different index pricing source."
        ),
    ),
    Segment(
        segment_id="fed-seg-4",
        text=(
            "The rate increase has reignited debate about its disproportionate burden on lower-income "
            "households. Mortgage rates tied to the 30-year fixed benchmark have climbed above 7.8 percent, "
            "a level not seen since 2000, effectively pricing millions of first-time buyers out of the "
            "housing market. Reuters reported that existing home sales fell to a 12-year low in January, "
            "while The Guardian highlighted data from the National Low Income Housing Coalition showing "
            "that rental eviction filings surged 18 percent year-over-year in cities where housing costs "
            "are highest. Economists at Pantheon Macroeconomics warn that continued tightening risks "
            "triggering a labour-market slowdown disproportionately affecting service-sector workers."
        ),
        sources=_fed_seg4_sources,
        num_articles=2,
        avg_political_bias_score=_avg_bias(_fed_seg4_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_fed_seg4_sources)),
        truth_value=0.85,
        additional_notes=(
            "The 18% eviction figure originates from a housing advocacy organisation and should be "
            "considered alongside government-tracked eviction data, which shows a more moderate 11% rise. "
            "Mortgage rate figure is the Freddie Mac weekly average as of February 13, 2026."
        ),
    ),
    Segment(
        segment_id="fed-seg-5",
        text=(
            "The decision drew a sharp partisan split in Washington. Senate Democrats, led by Senator "
            "Elizabeth Warren, renewed calls for the Fed to 'stop inflicting pain on working families' "
            "and urged Powell to pause the hiking cycle. 'Millions of Americans are losing their homes "
            "and their jobs while Wall Street speculators profit,' Warren said in a statement. In "
            "contrast, several Republican lawmakers and conservative economists praised the decision as "
            "a necessary corrective to what they characterised as fiscal recklessness by the Biden and "
            "early Harris administrations. Fox Business quoted former Treasury official Lawrence Kudlow: "
            "'The Fed is doing the right thing. Inflation was a policy choice, and this is the cure.'"
        ),
        sources=_fed_seg5_sources,
        num_articles=2,
        avg_political_bias_score=_avg_bias(_fed_seg5_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_fed_seg5_sources)),
        truth_value=0.78,
        additional_notes=(
            "This segment synthesises partisan reaction and should be read as opinion rather than "
            "factual reporting. The Guardian and Fox Business selected quotes that reflected their "
            "respective political leanings; the broader congressional reaction was more nuanced. "
            "Attribution of inflation causation is contested among economists."
        ),
    ),
    Segment(
        segment_id="fed-seg-6",
        text=(
            "Looking ahead, Fed officials' median projections ('dot plot') suggest one further 25-bps "
            "increase in 2026, followed by three cuts totalling 75 bps in 2027, contingent on inflation "
            "returning sustainably to 2 percent. Goldman Sachs and JPMorgan economists both revised "
            "their terminal rate forecasts upward to 5.75 percent following the press conference. "
            "Bloomberg Economics noted that if core PCE remains above 3 percent through Q2 2026, the "
            "probability of a sixth consecutive hold — rather than a pause — rises substantially. "
            "The next FOMC meeting is scheduled for March 18–19, 2026."
        ),
        sources=_fed_seg6_sources,
        num_articles=2,
        avg_political_bias_score=_avg_bias(_fed_seg6_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_fed_seg6_sources)),
        truth_value=0.93,
        additional_notes=(
            "Dot plot projections are median estimates and are subject to revision. "
            "Bank forecasts are forward-looking and carry inherent uncertainty."
        ),
    ),
]

_fed_article_bias = _avg_bias(_fed_all_sources)

ARTICLE_FED = Article(
    article_id="art-001-fed-rate-hike",
    heading="Federal Reserve Raises Interest Rates to 5.5% — Highest Level Since 2001",
    topic_id="topic-001-us-monetary-policy",
    political_bias_score=_fed_article_bias,
    political_bias_label=bias_score_to_label(_fed_article_bias),
    factual_accuracy=0.90,
    sources=_fed_all_sources,
    segments=FED_SEGMENTS,
    created_at="2026-02-19T22:00:00Z",
    tags=["federal reserve", "interest rates", "inflation", "monetary policy", "US economy"],
)


# ===========================================================================
# ARTICLE 2 — COP32 Climate Summit Agreement
# ===========================================================================

_cop_ap = _src(
    "Associated Press", 0.01, 0.93,
    url="https://apnews.com/article/cop32-climate-agreement-carbon-neutrality-2045",
    published_at="2026-02-15T14:00:00Z",
)
_cop_bbc = _src(
    "BBC News", -0.09, 0.90,
    url="https://www.bbc.com/news/science-environment-cop32-agreement",
    published_at="2026-02-15T14:20:00Z",
)
_cop_guardian = _src(
    "The Guardian", -0.28, 0.87,
    url="https://www.theguardian.com/environment/2026/feb/15/cop32-carbon-neutrality-deal",
    published_at="2026-02-15T15:00:00Z",
)
_cop_fox = _src(
    "Fox News", 0.58, 0.71,
    url="https://www.foxnews.com/politics/cop32-climate-deal-economic-costs",
    published_at="2026-02-15T16:30:00Z",
)
_cop_ft = _src(
    "Financial Times", 0.21, 0.88,
    url="https://www.ft.com/content/cop32-climate-accord-carbon-markets",
    published_at="2026-02-15T15:45:00Z",
)

_cop_all_sources = [_cop_ap, _cop_bbc, _cop_guardian, _cop_fox, _cop_ft]

_cop_seg1_sources = [_cop_ap, _cop_bbc, _cop_guardian, _cop_ft]
_cop_seg2_sources = [_cop_ap, _cop_bbc, _cop_ft]
_cop_seg3_sources = [_cop_guardian, _cop_bbc, _cop_ap]
_cop_seg4_sources = [_cop_fox, _cop_ft]
_cop_seg5_sources = [_cop_ap, _cop_ft, _cop_bbc]
_cop_seg6_sources = [_cop_guardian, _cop_bbc]

COP_SEGMENTS = [
    Segment(
        segment_id="cop-seg-1",
        text=(
            "One hundred and fifty-three nations signed the Dubai Carbon Accord at the close of the "
            "COP32 United Nations Climate Conference on Sunday, committing to achieving carbon neutrality "
            "by 2045 — five years ahead of the 2050 target enshrined in the 2015 Paris Agreement. The "
            "accord, brokered over 14 days of negotiations in Dubai, includes binding emissions reduction "
            "pledges, a landmark agreement on carbon credit markets, and a $500 billion climate finance "
            "fund directed at developing nations. UN Secretary-General António Guterres called it 'the "
            "most consequential climate agreement since Paris,' while the UNFCCC executive secretary "
            "described it as 'a turning point for multilateral climate action.'"
        ),
        sources=_cop_seg1_sources,
        num_articles=4,
        avg_political_bias_score=_avg_bias(_cop_seg1_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_cop_seg1_sources)),
        truth_value=0.96,
        additional_notes=(
            "Signatory count of 153 is as reported at closing ceremony; several nations signalled "
            "intent to sign in subsequent days pending domestic ratification procedures. "
            "Finance fund figure of $500B confirmed by UNFCCC press release."
        ),
    ),
    Segment(
        segment_id="cop-seg-2",
        text=(
            "The accord's central mechanism is a phased emissions reduction schedule: signatory nations "
            "are required to cut greenhouse gas emissions by 43 percent versus 2019 levels by 2030, and "
            "by 75 percent by 2040, before reaching net zero by 2045. For the first time, a COP agreement "
            "includes a binding phase-out timeline for unabated coal power — set to end by 2035 for "
            "developed economies and by 2040 for developing ones. A new Internationally Transferred "
            "Mitigation Outcomes (ITMO) framework establishes standardised rules for cross-border carbon "
            "credit trading under Article 6 of the Paris rulebook, resolving a long-standing impasse that "
            "had stalled a functioning global carbon market for over a decade."
        ),
        sources=_cop_seg2_sources,
        num_articles=3,
        avg_political_bias_score=_avg_bias(_cop_seg2_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_cop_seg2_sources)),
        truth_value=0.94,
        additional_notes=(
            "Emissions reduction percentages are headline figures; the exact baselines and "
            "accounting methodologies vary by national submission. The coal phase-out dates are "
            "indicative targets and enforcement relies on national legislation rather than "
            "international sanctions."
        ),
    ),
    Segment(
        segment_id="cop-seg-3",
        text=(
            "The agreement's path to final signature was far from smooth. A bloc of 47 developing "
            "nations — led by India, Nigeria, and Bangladesh — pushed back against draft language that "
            "they argued placed an unfair burden on economies that have contributed least to historical "
            "emissions. India's chief negotiator, Sandeep Kaur, told reporters that the original finance "
            "proposals were 'wholly inadequate given the scale of adaptation needs.' The final compromise "
            "increased the climate finance pledge from an initial $200 billion proposal to $500 billion "
            "and created a dedicated Loss and Damage Facility with an inaugural allocation of $75 billion "
            "for nations already experiencing severe climate impacts. The Guardian noted that several "
            "African delegations remained dissatisfied, arguing the fund falls short of the $1 trillion-"
            "plus estimated to be needed annually by 2030."
        ),
        sources=_cop_seg3_sources,
        num_articles=3,
        avg_political_bias_score=_avg_bias(_cop_seg3_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_cop_seg3_sources)),
        truth_value=0.88,
        additional_notes=(
            "The $1 trillion annual estimate is from a 2024 UNEP Adaptation Gap Report; different "
            "methodologies yield estimates ranging from $400B to $1.8T. Sandeep Kaur quote is "
            "AP-verified; The Guardian's characterisation of African delegation sentiment may "
            "reflect a subset of delegations rather than a unified bloc position."
        ),
    ),
    Segment(
        segment_id="cop-seg-4",
        text=(
            "Critics in the United States were swift to challenge both the scientific framing and the "
            "economic implications of the accord. Fox News cited a Heritage Foundation analysis estimating "
            "that full compliance with the accord would cost the US economy between $3.1 trillion and "
            "$4.8 trillion over the next two decades, primarily through energy price increases and "
            "industrial restructuring. Republican senators issued a joint statement asserting that the "
            "agreement 'bypasses Congress' and warning that ratification would face 'insurmountable "
            "opposition' in the Senate. The Financial Times offered a more moderate assessment, "
            "acknowledging that transition costs are real but noting that most independent economic "
            "models project net positive GDP impacts over a 30-year horizon when avoided climate "
            "damages are factored in."
        ),
        sources=_cop_seg4_sources,
        num_articles=2,
        avg_political_bias_score=_avg_bias(_cop_seg4_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_cop_seg4_sources)),
        truth_value=0.74,
        additional_notes=(
            "The Heritage Foundation cost estimates are from a politically aligned think tank and "
            "use higher discount rates and narrower accounting than mainstream economic models. "
            "The $3.1–4.8T range is not peer-reviewed. The FT's characterisation of economic model "
            "consensus is broadly accurate but is itself an editorial summary, not a primary source."
        ),
    ),
    Segment(
        segment_id="cop-seg-5",
        text=(
            "The accord introduces a novel 'ratchet and review' enforcement mechanism that goes further "
            "than previous COP agreements. Nations must submit updated Nationally Determined Contributions "
            "(NDCs) every three years — reduced from the previous five-year cycle — and face a public "
            "'transparency registry' where reported emissions are cross-checked against satellite data "
            "provided by the newly established Climate Observation Alliance, a consortium of space "
            "agencies from the EU, NASA, JAXA, and ISRO. Nations failing to meet interim targets will "
            "face automatic suspension from ITMO carbon market access, creating a financial deterrent "
            "without requiring a formal sanctions regime. The Financial Times described this as 'the "
            "strongest compliance architecture in the history of the UNFCCC process.'"
        ),
        sources=_cop_seg5_sources,
        num_articles=3,
        avg_political_bias_score=_avg_bias(_cop_seg5_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_cop_seg5_sources)),
        truth_value=0.92,
        additional_notes=(
            "The Climate Observation Alliance is a newly announced body; its operational capacity "
            "and satellite coverage timelines are yet to be independently verified. The ITMO "
            "suspension mechanism is considered legally novel and may face challenges from WTO "
            "trade rules — a risk flagged in AP's deeper analysis published the following day."
        ),
    ),
    Segment(
        segment_id="cop-seg-6",
        text=(
            "Climate scientists reacted with cautious optimism tempered by urgency. Dr. Friederike Otto, "
            "a climate attribution scientist at Imperial College London, told the BBC that the accord "
            "'gives us a fighting chance' of limiting average global warming to 1.6°C above pre-industrial "
            "levels, though she stressed implementation must begin 'in months, not years.' The Guardian "
            "published an analysis citing multiple IPCC working group leads who noted that even a 1.5°C "
            "overshoot carries 'irreversible tipping point risks' for the Amazon basin, West Antarctic "
            "ice sheet, and Arctic permafrost. Greenpeace International called the agreement 'a "
            "historic step that is still not enough,' urging a faster coal phase-out and higher "
            "loss-and-damage commitments."
        ),
        sources=_cop_seg6_sources,
        num_articles=2,
        avg_political_bias_score=_avg_bias(_cop_seg6_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_cop_seg6_sources)),
        truth_value=0.89,
        additional_notes=(
            "The 1.6°C projection is a conditional estimate based on full accord implementation; "
            "current policy trajectories (pre-COP32) pointed to ~2.4°C. Tipping point language "
            "reflects mainstream IPCC AR6 findings and is well-supported scientifically."
        ),
    ),
]

_cop_article_bias = _avg_bias(_cop_all_sources)

ARTICLE_COP = Article(
    article_id="art-002-cop32-climate",
    heading="COP32: 153 Nations Sign Landmark Carbon Neutrality Agreement, Pledging Net Zero by 2045",
    topic_id="topic-002-climate-cop32",
    political_bias_score=_cop_article_bias,
    political_bias_label=bias_score_to_label(_cop_article_bias),
    factual_accuracy=0.89,
    sources=_cop_all_sources,
    segments=COP_SEGMENTS,
    created_at="2026-02-15T21:00:00Z",
    tags=["climate", "COP32", "carbon neutrality", "UN", "environment", "net zero"],
)


# ===========================================================================
# ARTICLE 3 — US Senate AI Governance Act
# ===========================================================================

_ai_reuters = _src(
    "Reuters", 0.03, 0.91,
    url="https://www.reuters.com/technology/us-senate-passes-ai-governance-act-2026-02-12",
    published_at="2026-02-12T20:00:00Z",
)
_ai_nyt = _src(
    "The New York Times", -0.31, 0.85,
    url="https://www.nytimes.com/2026/02/12/technology/senate-ai-governance-act-vote.html",
    published_at="2026-02-12T20:30:00Z",
)
_ai_techcrunch = _src(
    "TechCrunch", -0.16, 0.82,
    url="https://techcrunch.com/2026/02/12/senate-ai-act-passes-what-it-means",
    published_at="2026-02-12T21:00:00Z",
)
_ai_wired = _src(
    "Wired", -0.19, 0.83,
    url="https://www.wired.com/story/us-senate-ai-governance-act-passed-2026",
    published_at="2026-02-12T21:30:00Z",
)
_ai_fox = _src(
    "Fox News", 0.54, 0.73,
    url="https://www.foxnews.com/politics/senate-ai-bill-big-tech-government-overreach",
    published_at="2026-02-12T22:00:00Z",
)

_ai_all_sources = [_ai_reuters, _ai_nyt, _ai_techcrunch, _ai_wired, _ai_fox]

_ai_seg1_sources = [_ai_reuters, _ai_nyt, _ai_techcrunch, _ai_wired, _ai_fox]
_ai_seg2_sources = [_ai_reuters, _ai_nyt, _ai_techcrunch]
_ai_seg3_sources = [_ai_techcrunch, _ai_wired, _ai_reuters]
_ai_seg4_sources = [_ai_fox, _ai_reuters]
_ai_seg5_sources = [_ai_reuters, _ai_nyt]
_ai_seg6_sources = [_ai_techcrunch, _ai_wired, _ai_reuters]

AI_SEGMENTS = [
    Segment(
        segment_id="ai-seg-1",
        text=(
            "The United States Senate passed the AI Governance and Accountability Act (AGAA) on "
            "Thursday by a 67-to-33 margin, marking the most significant piece of American artificial "
            "intelligence legislation to date and the first federal AI law to pass both chambers of "
            "Congress. The bill, co-sponsored by Senators Maria Cantwell (D-WA) and John Cornyn (R-TX), "
            "now heads to President Reyes's desk, where the White House has confirmed she will sign it "
            "into law next week. The bipartisan vote — with 34 Republicans joining all 33 Democrats — "
            "reflected months of behind-the-scenes compromise between technology industry representatives, "
            "civil liberties groups, and national security officials."
        ),
        sources=_ai_seg1_sources,
        num_articles=5,
        avg_political_bias_score=_avg_bias(_ai_seg1_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_ai_seg1_sources)),
        truth_value=0.97,
        additional_notes=(
            "Vote count and sponsor names confirmed across all five sources. White House "
            "signing confirmation sourced from an official press statement cited by Reuters."
        ),
    ),
    Segment(
        segment_id="ai-seg-2",
        text=(
            "The AGAA establishes a tiered regulatory framework for AI systems based on risk level. "
            "Systems classified as 'critical-risk' — including autonomous weapons, AI used in criminal "
            "sentencing, health diagnostics affecting life-and-death decisions, and deepfake election "
            "content — are subject to mandatory pre-deployment audits by a newly created Office of AI "
            "Safety (OAIS) within the Department of Commerce. 'High-risk' systems, including hiring "
            "algorithms, credit scoring models, and AI-generated news content, must carry mandatory "
            "disclosure labels and undergo annual third-party audits. 'General-purpose' AI models with "
            "more than one billion parameters are required to submit model cards and training data "
            "summaries to OAIS and to report significant capability jumps within 90 days of detection."
        ),
        sources=_ai_seg2_sources,
        num_articles=3,
        avg_political_bias_score=_avg_bias(_ai_seg2_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_ai_seg2_sources)),
        truth_value=0.93,
        additional_notes=(
            "Risk tier definitions and parameter thresholds are drawn from the final bill text "
            "as published by the Senate Judiciary Committee. The 1-billion-parameter threshold "
            "is a significant simplification; the bill's actual wording uses a compute-equivalent "
            "measure, not parameter count, which TechCrunch's detailed breakdown notes may affect "
            "edge cases like sparse models."
        ),
    ),
    Segment(
        segment_id="ai-seg-3",
        text=(
            "Reactions from the technology industry were mixed. Alphabet, Microsoft, and Amazon issued "
            "statements welcoming the 'regulatory clarity' while voicing concern that audit timelines — "
            "as short as 60 days for critical-risk pre-deployment reviews — are 'operationally "
            "challenging.' OpenAI CEO Sam Altman called the law 'a reasonable first step' in a post on "
            "X, adding that the company had engaged with both Democratic and Republican staffers during "
            "drafting. Smaller AI start-ups, represented by the Coalition for AI Innovation, were more "
            "critical: its executive director warned that compliance costs could create a 'regulatory "
            "moat' that entrenches incumbents. Wired noted that companies have 18 months to come into "
            "compliance, a timeline that several legal experts described as 'tight but workable.'"
        ),
        sources=_ai_seg3_sources,
        num_articles=3,
        avg_political_bias_score=_avg_bias(_ai_seg3_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_ai_seg3_sources)),
        truth_value=0.88,
        additional_notes=(
            "Corporate statements are paraphrased from press releases; direct quotes from Altman "
            "are attributed to an X post. The Coalition for AI Innovation is a lobbying body; "
            "its 'regulatory moat' argument, while commonly cited, is contested by consumer "
            "protection advocates who argue that compliance costs also deter harmful AI deployment."
        ),
    ),
    Segment(
        segment_id="ai-seg-4",
        text=(
            "The bill's passage was not without ideological friction. Twenty-three Republican senators "
            "who voted against the legislation argued it represented government overreach that would "
            "stifle American AI competitiveness against China. Senator Rand Paul issued a lengthy floor "
            "statement calling the OAIS 'a censorship bureau in waiting,' specifically targeting "
            "provisions requiring disclosure labels on AI-generated political content. Fox News framed "
            "the story primarily around these concerns, interviewing several Heritage Foundation fellows "
            "who argued that algorithmic regulation of political speech posed a First Amendment risk. "
            "Reuters, however, noted that the bill's political content provisions were narrowly tailored "
            "to apply only to synthetic media in paid electoral advertising — a scope significantly "
            "narrower than early drafts."
        ),
        sources=_ai_seg4_sources,
        num_articles=2,
        avg_political_bias_score=_avg_bias(_ai_seg4_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_ai_seg4_sources)),
        truth_value=0.81,
        additional_notes=(
            "First Amendment analysis here represents legal opinion, not settled law. The OAIS "
            "'censorship' characterisation is Senator Paul's framing and is disputed by the bill's "
            "sponsors. Fox News's coverage in this segment was notably narrower in sourcing than "
            "other outlets, relying primarily on opponents of the legislation."
        ),
    ),
    Segment(
        segment_id="ai-seg-5",
        text=(
            "International observers have been watching the US legislative process closely given the "
            "global influence of American tech regulation. The EU's AI Act, which entered full force "
            "in August 2025, shares several structural similarities with the AGAA — including risk-based "
            "tiering and third-party audits — raising hopes among Brussels officials of future "
            "transatlantic regulatory alignment. However, the AGAA's lighter-touch approach to "
            "general-purpose models differs from the EU's broader provisions. The New York Times quoted "
            "a European Commission spokesperson saying Brussels would 'study the US framework with "
            "interest' and hoped for coordination mechanisms to avoid a fragmented global AI governance "
            "landscape. A joint US-EU AI governance working group is expected to convene by Q3 2026."
        ),
        sources=_ai_seg5_sources,
        num_articles=2,
        avg_political_bias_score=_avg_bias(_ai_seg5_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_ai_seg5_sources)),
        truth_value=0.90,
        additional_notes=(
            "EU AI Act entry-into-force date of August 2025 is accurate per EU Official Journal. "
            "The working group announcement is attributed to an unnamed State Department official "
            "by Reuters; it has not been confirmed by a formal joint statement."
        ),
    ),
    Segment(
        segment_id="ai-seg-6",
        text=(
            "Implementation will now shift to the rulemaking phase. The OAIS has a statutory 12-month "
            "window to publish implementing regulations, including detailed definitions of risk "
            "categories, audit protocols, and penalties — which can reach up to $50 million or four "
            "percent of global annual revenue, whichever is higher, for critical-risk violations. "
            "TechCrunch highlighted that the bill allocates $2.1 billion over five years for OAIS "
            "staffing and technology infrastructure, but several AI policy researchers told Wired they "
            "were 'sceptical' that budget was sufficient to audit the largest frontier model developers. "
            "The effective enforcement date for critical-risk systems is set for February 2028, giving "
            "industry roughly 24 months to prepare after the final rules are published."
        ),
        sources=_ai_seg6_sources,
        num_articles=3,
        avg_political_bias_score=_avg_bias(_ai_seg6_sources),
        avg_political_bias_label=bias_score_to_label(_avg_bias(_ai_seg6_sources)),
        truth_value=0.92,
        additional_notes=(
            "Penalty figures and budget allocations are sourced directly from the bill text as "
            "cited by Reuters and TechCrunch. OAIS resourcing adequacy is a matter of ongoing "
            "policy debate; the $2.1B figure should be contextualised against the scale of the "
            "AI industry (global revenues exceeding $500B in 2025)."
        ),
    ),
]

_ai_article_bias = _avg_bias(_ai_all_sources)

ARTICLE_AI = Article(
    article_id="art-003-senate-ai-act",
    heading="US Senate Passes AI Governance Act 67–33: What the Law Means for Tech, Politics, and Global AI Regulation",
    topic_id="topic-003-ai-regulation",
    political_bias_score=_ai_article_bias,
    political_bias_label=bias_score_to_label(_ai_article_bias),
    factual_accuracy=0.88,
    sources=_ai_all_sources,
    segments=AI_SEGMENTS,
    created_at="2026-02-12T23:30:00Z",
    tags=["AI regulation", "US Senate", "AGAA", "technology policy", "bipartisan"],
)


# ===========================================================================
# TOPICS (wrapping each article in a Topic object)
# ===========================================================================

TOPIC_FED = Topic(
    topic_id="topic-001-us-monetary-policy",
    name="US Federal Reserve Rate Hike — February 2026",
    description="The FOMC raises the federal funds rate to 5.25–5.50%, the highest since 2001, amid persistent inflation.",
    rag_summary=(
        "The Federal Reserve raised interest rates by 25 basis points to a target range of "
        "5.25–5.50% [1], the highest level since June 2001. Fed Chair Jerome Powell indicated "
        "the committee remains open to further hikes should inflation persist, with core PCE "
        "still running at 3.7% year-on-year [2]. Markets reacted with moderate volatility; "
        "the S&P 500 closed down 0.3% and two-year Treasury yields ticked up 6 basis points [3]. "
        "Rising mortgage rates above 7.8% have contributed to a 12-year low in existing home "
        "sales [4]. The decision prompted sharp partisan debate, with progressive lawmakers "
        "criticising the human cost of tightening [5] while conservative commentators praised it "
        "as a necessary inflation cure [5]. The Fed's dot plot projects one additional hike "
        "and three cuts by end-2027 [6]."
    ),
    citation_mapping=[
        CitationMapping(
            citation_id="[1]", article_id="art-001-fed-rate-hike", segment_id="fed-seg-1",
            source_name="Reuters",
            excerpt="The Federal Reserve raised its benchmark interest rate by 25 basis points… lifting the federal funds rate to a target range of 5.25–5.50 percent",
            url="https://www.reuters.com/business/finance/fed-raises-rates-55-percent-2026-02-19",
        ),
        CitationMapping(
            citation_id="[2]", article_id="art-001-fed-rate-hike", segment_id="fed-seg-2",
            source_name="Bloomberg",
            excerpt="Powell pointed to the core PCE index running at 3.7 percent year-over-year as evidence that the job is not yet finished",
            url="https://www.bloomberg.com/news/articles/2026-02-19/fed-rate-hike-55",
        ),
        CitationMapping(
            citation_id="[3]", article_id="art-001-fed-rate-hike", segment_id="fed-seg-3",
            source_name="Bloomberg",
            excerpt="The two-year Treasury yield edged up 6 basis points to 4.91 percent; the S&P 500 closed down 0.3 percent",
            url="https://www.bloomberg.com/news/articles/2026-02-19/fed-rate-hike-55",
        ),
        CitationMapping(
            citation_id="[4]", article_id="art-001-fed-rate-hike", segment_id="fed-seg-4",
            source_name="Reuters",
            excerpt="Reuters reported that existing home sales fell to a 12-year low in January",
            url="https://www.reuters.com/business/finance/fed-raises-rates-55-percent-2026-02-19",
        ),
        CitationMapping(
            citation_id="[5]", article_id="art-001-fed-rate-hike", segment_id="fed-seg-5",
            source_name="The Guardian",
            excerpt="Senate Democrats renewed calls for the Fed to 'stop inflicting pain on working families'",
            url="https://www.theguardian.com/business/2026/feb/19/federal-reserve-rate-hike-workers",
        ),
        CitationMapping(
            citation_id="[6]", article_id="art-001-fed-rate-hike", segment_id="fed-seg-6",
            source_name="Reuters",
            excerpt="Fed officials' median projections suggest one further 25-bps increase in 2026, followed by three cuts totalling 75 bps in 2027",
            url="https://www.reuters.com/business/finance/fed-raises-rates-55-percent-2026-02-19",
        ),
    ],
    aggregate_political_bias_score=_fed_article_bias,
    aggregate_political_bias_label=bias_score_to_label(_fed_article_bias),
    credibility_score=0.89,
    articles=[ARTICLE_FED],
    article_count=5,
    source_count=5,
    created_at="2026-02-19T22:00:00Z",
    tags=["federal reserve", "interest rates", "inflation", "US economy"],
)

TOPIC_COP = Topic(
    topic_id="topic-002-climate-cop32",
    name="COP32 Dubai Carbon Accord",
    description="153 nations sign a binding agreement at COP32 pledging carbon neutrality by 2045, with a $500B climate finance commitment.",
    rag_summary=(
        "One hundred and fifty-three nations signed the Dubai Carbon Accord at COP32, committing to "
        "carbon neutrality by 2045 [1] — five years ahead of the Paris Agreement target. Key provisions "
        "include a phased coal phase-out by 2035 for developed nations, a standardised Article 6 carbon "
        "market framework, and a $500 billion climate finance fund [2]. Negotiations were contentious: "
        "a bloc of 47 developing nations, led by India, pushed the finance commitment from $200B to "
        "$500B, with an additional $75B Loss and Damage Facility [3]. Critics, including a Heritage "
        "Foundation analysis cited by Fox News, estimated US compliance costs at $3.1–4.8 trillion, "
        "though independent economic models project net positive GDP impacts [4]. A novel satellite-"
        "backed enforcement mechanism ties carbon market access to interim target compliance [5]. "
        "Scientists describe the accord as giving the world 'a fighting chance' at limiting warming to "
        "1.6°C, while cautioning that implementation must be immediate [6]."
    ),
    citation_mapping=[
        CitationMapping(
            citation_id="[1]", article_id="art-002-cop32-climate", segment_id="cop-seg-1",
            source_name="Associated Press",
            excerpt="153 nations signed the Dubai Carbon Accord… committing to achieving carbon neutrality by 2045",
            url="https://apnews.com/article/cop32-climate-agreement-carbon-neutrality-2045",
        ),
        CitationMapping(
            citation_id="[2]", article_id="art-002-cop32-climate", segment_id="cop-seg-2",
            source_name="Financial Times",
            excerpt="A new ITMO framework establishes standardised rules for cross-border carbon credit trading under Article 6",
            url="https://www.ft.com/content/cop32-climate-accord-carbon-markets",
        ),
        CitationMapping(
            citation_id="[3]", article_id="art-002-cop32-climate", segment_id="cop-seg-3",
            source_name="The Guardian",
            excerpt="The final compromise increased the climate finance pledge from $200 billion to $500 billion",
            url="https://www.theguardian.com/environment/2026/feb/15/cop32-carbon-neutrality-deal",
        ),
        CitationMapping(
            citation_id="[4]", article_id="art-002-cop32-climate", segment_id="cop-seg-4",
            source_name="Financial Times",
            excerpt="Most independent economic models project net positive GDP impacts over a 30-year horizon when avoided climate damages are factored in",
            url="https://www.ft.com/content/cop32-climate-accord-carbon-markets",
        ),
        CitationMapping(
            citation_id="[5]", article_id="art-002-cop32-climate", segment_id="cop-seg-5",
            source_name="Associated Press",
            excerpt="Nations failing to meet interim targets will face automatic suspension from ITMO carbon market access",
            url="https://apnews.com/article/cop32-climate-agreement-carbon-neutrality-2045",
        ),
        CitationMapping(
            citation_id="[6]", article_id="art-002-cop32-climate", segment_id="cop-seg-6",
            source_name="BBC News",
            excerpt="Dr. Friederike Otto told the BBC that the accord 'gives us a fighting chance' of limiting warming to 1.6°C",
            url="https://www.bbc.com/news/science-environment-cop32-agreement",
        ),
    ],
    aggregate_political_bias_score=_cop_article_bias,
    aggregate_political_bias_label=bias_score_to_label(_cop_article_bias),
    credibility_score=0.88,
    articles=[ARTICLE_COP],
    article_count=5,
    source_count=5,
    created_at="2026-02-15T21:00:00Z",
    tags=["climate", "COP32", "carbon", "environment", "UN"],
)

TOPIC_AI = Topic(
    topic_id="topic-003-ai-regulation",
    name="US AI Governance and Accountability Act",
    description="The Senate passes landmark bipartisan AI regulation establishing risk-tiered oversight, mandatory audits, and a federal AI safety office.",
    rag_summary=(
        "The US Senate passed the AI Governance and Accountability Act 67–33 in a bipartisan vote [1], "
        "establishing a tiered regulatory framework for AI. Critical-risk systems — including autonomous "
        "weapons and AI in criminal sentencing — require pre-deployment audits by a new Office of AI "
        "Safety (OAIS) [2]. Major tech companies welcomed regulatory clarity while flagging tight audit "
        "timelines; start-ups warned of a regulatory moat favouring incumbents [3]. Conservative critics "
        "raised First Amendment concerns over deepfake disclosure rules, though Reuters noted these "
        "provisions are narrowly scoped to paid electoral advertising [4]. The EU and US may pursue "
        "regulatory alignment given structural similarities between the AGAA and the EU AI Act [5]. "
        "OAIS has 12 months to publish rules, with enforcement beginning February 2028 [6]."
    ),
    citation_mapping=[
        CitationMapping(
            citation_id="[1]", article_id="art-003-senate-ai-act", segment_id="ai-seg-1",
            source_name="Reuters",
            excerpt="The United States Senate passed the AI Governance and Accountability Act by a 67-to-33 margin",
            url="https://www.reuters.com/technology/us-senate-passes-ai-governance-act-2026-02-12",
        ),
        CitationMapping(
            citation_id="[2]", article_id="art-003-senate-ai-act", segment_id="ai-seg-2",
            source_name="The New York Times",
            excerpt="Critical-risk systems… are subject to mandatory pre-deployment audits by a newly created Office of AI Safety",
            url="https://www.nytimes.com/2026/02/12/technology/senate-ai-governance-act-vote.html",
        ),
        CitationMapping(
            citation_id="[3]", article_id="art-003-senate-ai-act", segment_id="ai-seg-3",
            source_name="TechCrunch",
            excerpt="Compliance costs could create a 'regulatory moat' that entrenches incumbents",
            url="https://techcrunch.com/2026/02/12/senate-ai-act-passes-what-it-means",
        ),
        CitationMapping(
            citation_id="[4]", article_id="art-003-senate-ai-act", segment_id="ai-seg-4",
            source_name="Reuters",
            excerpt="The bill's political content provisions were narrowly tailored to apply only to synthetic media in paid electoral advertising",
            url="https://www.reuters.com/technology/us-senate-passes-ai-governance-act-2026-02-12",
        ),
        CitationMapping(
            citation_id="[5]", article_id="art-003-senate-ai-act", segment_id="ai-seg-5",
            source_name="The New York Times",
            excerpt="Brussels officials hoped for coordination mechanisms to avoid a fragmented global AI governance landscape",
            url="https://www.nytimes.com/2026/02/12/technology/senate-ai-governance-act-vote.html",
        ),
        CitationMapping(
            citation_id="[6]", article_id="art-003-senate-ai-act", segment_id="ai-seg-6",
            source_name="TechCrunch",
            excerpt="The effective enforcement date for critical-risk systems is set for February 2028",
            url="https://techcrunch.com/2026/02/12/senate-ai-act-passes-what-it-means",
        ),
    ],
    aggregate_political_bias_score=_ai_article_bias,
    aggregate_political_bias_label=bias_score_to_label(_ai_article_bias),
    credibility_score=0.86,
    articles=[ARTICLE_AI],
    article_count=5,
    source_count=5,
    created_at="2026-02-12T23:30:00Z",
    tags=["AI regulation", "US Senate", "AGAA", "OAIS", "technology law"],
)


# ---------------------------------------------------------------------------
# Public collections
# ---------------------------------------------------------------------------

ALL_ARTICLES: list[Article] = [ARTICLE_FED, ARTICLE_COP, ARTICLE_AI]
ALL_TOPICS: list[Topic] = [TOPIC_FED, TOPIC_COP, TOPIC_AI]

ARTICLES_BY_ID: dict[str, Article] = {a.article_id: a for a in ALL_ARTICLES}
TOPICS_BY_ID: dict[str, Topic] = {t.topic_id: t for t in ALL_TOPICS}
