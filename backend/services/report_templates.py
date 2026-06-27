"""
Report Templates — HTML templates for export reports.

Generates well-styled, print-ready HTML that serves as a downloadable
report (either .html or rendered to PDF via weasyprint if available).

Uses @media print CSS for clean printable output.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional


def _base_styles() -> str:
    """Shared CSS for all report templates."""
    return """
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: #1a1a2e;
            background: #ffffff;
            line-height: 1.6;
            padding: 40px;
        }
        .report-header {
            border-bottom: 3px solid #6366f1;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .report-header h1 {
            font-size: 28px;
            color: #1a1a2e;
            margin-bottom: 4px;
        }
        .report-header .subtitle {
            color: #64748b;
            font-size: 14px;
        }
        .report-header .logo-text {
            font-size: 12px;
            color: #6366f1;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }
        .meta-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
            background: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
        .meta-item {
            display: flex;
            flex-direction: column;
        }
        .meta-item .label {
            font-size: 11px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .meta-item .value {
            font-size: 16px;
            font-weight: 600;
            color: #1a1a2e;
        }
        .score-badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 14px;
        }
        .score-high { background: #dcfce7; color: #166534; }
        .score-mid { background: #fef9c3; color: #854d0e; }
        .score-low { background: #fee2e2; color: #991b1b; }
        .section-title {
            font-size: 18px;
            font-weight: 700;
            color: #1a1a2e;
            margin: 30px 0 16px 0;
            padding-bottom: 8px;
            border-bottom: 1px solid #e2e8f0;
        }
        .question-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            page-break-inside: avoid;
        }
        .question-card .q-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .question-card .q-number {
            font-size: 12px;
            color: #6366f1;
            font-weight: 600;
            text-transform: uppercase;
        }
        .question-card .q-text {
            font-size: 14px;
            font-weight: 600;
            color: #1a1a2e;
            margin-bottom: 10px;
        }
        .question-card .a-text {
            font-size: 13px;
            color: #475569;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 10px;
        }
        .question-card .feedback {
            font-size: 12px;
            color: #64748b;
        }
        .question-card .feedback strong {
            color: #1a1a2e;
        }
        table.summary-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }
        table.summary-table th {
            background: #6366f1;
            color: #ffffff;
            padding: 12px 16px;
            text-align: left;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        table.summary-table td {
            padding: 12px 16px;
            border-bottom: 1px solid #e2e8f0;
            font-size: 13px;
            color: #1a1a2e;
        }
        table.summary-table tr:nth-child(even) {
            background: #f8fafc;
        }
        table.summary-table tr:hover {
            background: #f1f5f9;
        }
        .violations-summary {
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            padding: 16px;
            margin-top: 16px;
        }
        .violations-summary h3 {
            color: #991b1b;
            font-size: 14px;
            margin-bottom: 8px;
        }
        .violations-summary ul {
            list-style: none;
            padding: 0;
        }
        .violations-summary li {
            font-size: 13px;
            color: #7f1d1d;
            padding: 4px 0;
        }
        .recommendation-box {
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 8px;
            padding: 16px;
            margin-top: 20px;
        }
        .recommendation-box.hire {
            background: #f0fdf4;
            border-color: #bbf7d0;
        }
        .recommendation-box.reject {
            background: #fef2f2;
            border-color: #fecaca;
        }
        .recommendation-box h3 {
            font-size: 14px;
            margin-bottom: 6px;
        }
        .recommendation-box p {
            font-size: 13px;
            color: #475569;
        }
        .footer {
            margin-top: 40px;
            padding-top: 16px;
            border-top: 1px solid #e2e8f0;
            font-size: 11px;
            color: #94a3b8;
            text-align: center;
        }

        /* Print-specific styles */
        @media print {
            body { padding: 20px; font-size: 12px; }
            .report-header { border-bottom-width: 2px; }
            .question-card { page-break-inside: avoid; }
            .meta-grid { background: #f9f9f9; }
            table.summary-table { page-break-inside: auto; }
            table.summary-table tr { page-break-inside: avoid; }
            .footer { position: fixed; bottom: 0; width: 100%; }
        }
    </style>
    """


def _score_badge(score: Optional[float]) -> str:
    """Generate a colored score badge."""
    if score is None:
        return '<span class="score-badge score-mid">N/A</span>'
    s = float(score)
    if s >= 7.0:
        cls = "score-high"
    elif s >= 5.0:
        cls = "score-mid"
    else:
        cls = "score-low"
    return f'<span class="score-badge {cls}">{s:.1f}/10</span>'


def _recommendation_class(rec: Optional[str]) -> str:
    """Map recommendation text to CSS class."""
    if not rec:
        return ""
    lower = rec.lower()
    if "strong" in lower or "hire" in lower:
        return "hire"
    elif "not" in lower or "reject" in lower:
        return "reject"
    return ""


def render_single_candidate_report(session_data: Dict[str, Any]) -> str:
    """
    Render a full HTML report for a single candidate's interview session.

    Args:
        session_data: Dictionary containing:
            - candidate_name, created_at, status, average_score,
              recommendation, overall_feedback, skills_detected,
              experience_years, questions (list of dicts with
              question_text, answer_text, score, strengths, improvements),
              violations (list of dicts with event_type, timestamp, details)
    """
    name = session_data.get("candidate_name", "Unknown Candidate")
    date = session_data.get("created_at", "")
    if isinstance(date, datetime):
        date = date.strftime("%B %d, %Y at %I:%M %p")
    score = session_data.get("average_score")
    recommendation = session_data.get("recommendation", "Pending")
    overall_feedback = session_data.get("overall_feedback", "")
    skills = session_data.get("skills_detected", [])
    experience = session_data.get("experience_years", "N/A")
    questions = session_data.get("questions", [])
    violations = session_data.get("violations", [])
    status = session_data.get("status", "unknown")

    # Build questions section
    questions_html = ""
    for i, q in enumerate(questions, 1):
        q_text = q.get("question_text", "")
        a_text = q.get("answer_text", "No answer provided")
        q_score = q.get("score")
        strengths = q.get("strengths", [])
        improvements = q.get("improvements", [])

        # Truncate long answers for report readability
        if len(a_text) > 500:
            a_text = a_text[:500] + "..."

        feedback_parts = []
        if strengths:
            feedback_parts.append(f"<strong>Strengths:</strong> {', '.join(strengths[:3])}")
        if improvements:
            feedback_parts.append(f"<strong>Areas to improve:</strong> {', '.join(improvements[:3])}")
        feedback_html = "<br>".join(feedback_parts) if feedback_parts else ""

        questions_html += f"""
        <div class="question-card">
            <div class="q-header">
                <span class="q-number">Question {i}</span>
                {_score_badge(q_score)}
            </div>
            <div class="q-text">{q_text}</div>
            <div class="a-text">{a_text}</div>
            {"<div class='feedback'>" + feedback_html + "</div>" if feedback_html else ""}
        </div>
        """

    # Build violations section
    violations_html = ""
    if violations:
        violation_items = ""
        for v in violations:
            event = v.get("event_type", "Unknown")
            ts = v.get("timestamp", "")
            violation_items += f"<li>⚠️ {event} — {ts}</li>"
        violations_html = f"""
        <div class="violations-summary">
            <h3>⚠️ Proctoring Violations ({len(violations)} detected)</h3>
            <ul>{violation_items}</ul>
        </div>
        """

    # Recommendation box
    rec_class = _recommendation_class(recommendation)
    rec_html = f"""
    <div class="recommendation-box {rec_class}">
        <h3>Recommendation: {recommendation}</h3>
        <p>{overall_feedback if overall_feedback else "No additional feedback provided."}</p>
    </div>
    """ if recommendation else ""

    skills_str = ", ".join(skills) if skills else "None detected"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interview Report — {name}</title>
    {_base_styles()}
</head>
<body>
    <div class="report-header">
        <div class="logo-text">AI Interview Assistant</div>
        <h1>Interview Report</h1>
        <div class="subtitle">Candidate Assessment Summary</div>
    </div>

    <div class="meta-grid">
        <div class="meta-item">
            <span class="label">Candidate</span>
            <span class="value">{name}</span>
        </div>
        <div class="meta-item">
            <span class="label">Date</span>
            <span class="value">{date}</span>
        </div>
        <div class="meta-item">
            <span class="label">Overall Score</span>
            <span class="value">{_score_badge(score)}</span>
        </div>
        <div class="meta-item">
            <span class="label">Status</span>
            <span class="value">{status.replace('_', ' ').title()}</span>
        </div>
        <div class="meta-item">
            <span class="label">Experience</span>
            <span class="value">{experience}</span>
        </div>
        <div class="meta-item">
            <span class="label">Skills</span>
            <span class="value" style="font-size: 13px;">{skills_str}</span>
        </div>
    </div>

    {rec_html}

    <h2 class="section-title">Question-by-Question Breakdown</h2>
    {questions_html if questions_html else "<p style='color: #64748b;'>No questions answered yet.</p>"}

    {violations_html}

    <div class="footer">
        Generated by AI Interview Assistant &bull; {datetime.now().strftime("%Y-%m-%d %H:%M")} &bull; Confidential
    </div>
</body>
</html>"""

    return html


def render_candidates_summary_report(
    sessions: List[Dict[str, Any]],
    filters_applied: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Render an HTML summary table of all candidates for printing/sharing.

    Args:
        sessions: List of session dicts with keys:
            candidate_name, average_score, status, recommendation, created_at
        filters_applied: Optional dict of filters that were active
    """
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    total = len(sessions)

    # Build filter description
    filter_desc = ""
    if filters_applied:
        parts = []
        for k, v in filters_applied.items():
            if v is not None:
                parts.append(f"{k.replace('_', ' ').title()}: {v}")
        if parts:
            filter_desc = f"<p style='font-size: 12px; color: #64748b; margin-top: 8px;'>Filters: {' | '.join(parts)}</p>"

    # Build table rows
    rows_html = ""
    for i, s in enumerate(sessions, 1):
        name = s.get("candidate_name", "Unknown")
        score = s.get("average_score")
        status = s.get("status", "—")
        rec = s.get("recommendation", "—")
        date = s.get("created_at", "")
        if isinstance(date, datetime):
            date = date.strftime("%Y-%m-%d")
        elif isinstance(date, str) and "T" in date:
            date = date.split("T")[0]

        rows_html += f"""
        <tr>
            <td>{i}</td>
            <td><strong>{name}</strong></td>
            <td>{_score_badge(score)}</td>
            <td>{status.replace('_', ' ').title()}</td>
            <td>{rec or '—'}</td>
            <td>{date}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Candidates Summary Report</title>
    {_base_styles()}
</head>
<body>
    <div class="report-header">
        <div class="logo-text">AI Interview Assistant</div>
        <h1>Candidates Summary Report</h1>
        <div class="subtitle">{total} candidate(s) &bull; Generated {now}</div>
        {filter_desc}
    </div>

    <table class="summary-table">
        <thead>
            <tr>
                <th>#</th>
                <th>Candidate</th>
                <th>Score</th>
                <th>Status</th>
                <th>Recommendation</th>
                <th>Date</th>
            </tr>
        </thead>
        <tbody>
            {rows_html if rows_html else "<tr><td colspan='6' style='text-align: center; padding: 20px;'>No candidates found</td></tr>"}
        </tbody>
    </table>

    <div class="footer">
        Generated by AI Interview Assistant &bull; {datetime.now().strftime("%Y-%m-%d %H:%M")} &bull; Confidential
    </div>
</body>
</html>"""

    return html
