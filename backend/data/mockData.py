from ..models import StoryWrapper, Story, Segment, NewsProvider, User, Comment

mock_providers = [
    NewsProvider(name="The Guardian", bias_score=-0.3, trust_score=0.9),
    NewsProvider(name="BBC",          bias_score=0.0,  trust_score=0.95),
    NewsProvider(name="Fox News",     bias_score=0.7,  trust_score=0.7),
]

mock_users = [
    User(username="alice", email="alice@example.com", reputation=100),
    User(username="bob",   email="bob@example.com", reputation=50),
]

mock_comments = [
    Comment(text="Interesting segment!", like_count=5, dislike_count=1, parent=None, user=mock_users[0]),
    Comment(text="I disagree with the bias score.", like_count=2, dislike_count=3, parent=None, user=mock_users[1]),
]

mock_stories = [
    StoryWrapper(
        story=Story(
            heading="Climate Change Policy Updates",
            political_bias=0.1,
            factual_accuracy=0.92,
            sources=mock_providers,
            segments=[
                Segment(text="Governments worldwide are updating climate policies.",
                        sources=[mock_providers[0], mock_providers[1]],
                        avg_bias=0.05, avg_truth=0.93, article_count=2,
                        notes="Consensus among mainstream sources.", comments=[mock_comments[0]]),
                Segment(text="Some sources question the effectiveness of new measures.",
                        sources=[mock_providers[2]],
                        avg_bias=0.7, avg_truth=0.7, article_count=1,
                        notes="Skepticism from right-leaning outlets.", comments=[mock_comments[1]]),
            ]
        ),
        comments=mock_comments,
    ),
    StoryWrapper(
        story=Story(
            heading="Economic Recovery Post-Pandemic",
            political_bias=-0.1,
            factual_accuracy=0.88,
            sources=mock_providers,
            segments=[
                Segment(text="Global economies are showing signs of recovery.",
                        sources=[mock_providers[1]],
                        avg_bias=0.0, avg_truth=0.9, article_count=1,
                        notes="Neutral reporting.", comments=[]),
                Segment(text="Debate continues on stimulus effectiveness.",
                        sources=[mock_providers[0], mock_providers[2]],
                        avg_bias=0.2, avg_truth=0.85, article_count=2,
                        notes="Mixed opinions from left and right.", comments=[]),
            ]
        ),
        comments=[],
    ),
    StoryWrapper(
        story=Story(
            heading="Tech Regulation in 2026",
            political_bias=0.3,
            factual_accuracy=0.81,
            sources=mock_providers,
            segments=[
                Segment(text="New laws target big tech companies.",
                        sources=[mock_providers[0], mock_providers[2]],
                        avg_bias=0.2, avg_truth=0.8, article_count=2,
                        notes="Focus on privacy and antitrust.", comments=[]),
                Segment(text="Industry groups lobby for less regulation.",
                        sources=[mock_providers[2]],
                        avg_bias=0.7, avg_truth=0.75, article_count=1,
                        notes="Business perspective.", comments=[]),
            ]
        ),
        comments=[],
    ),
]