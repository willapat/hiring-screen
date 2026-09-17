from tools.review_models import ReviewIssue, ReviewReport, Segment, SpanModel
from tools.text_anchor import Anchor, build_segments, resolve_anchors


def build_review_report(text: str, issues: list[ReviewIssue]) -> ReviewReport:
    """Resolve each issue's quote to a span in `text`, attach it, and flatten
    everything into a ReviewReport. Shared by the review and tailoring
    endpoints — both produce ReviewIssue lists that need the same anchoring."""
    anchors = [Anchor(issue_id=issue.id, quote=issue.quote, line=issue.line) for issue in issues]
    resolved = resolve_anchors(text, anchors)
    resolved_by_id = dict(resolved)

    for issue in issues:
        span = resolved_by_id.get(issue.id)
        if span:
            issue.span = SpanModel(start=span.start, end=span.end)

    segments = [Segment(text=s.text, issue_ids=s.issue_ids) for s in build_segments(text, resolved)]
    anchor_rate = sum(1 for _, span in resolved if span) / len(resolved) if resolved else 1.0

    return ReviewReport(issues=issues, segments=segments, anchor_rate=anchor_rate)
