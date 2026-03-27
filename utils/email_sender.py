"""
Email Report Sender.
Sends formatted HTML resume analysis reports via SMTP (Gmail).
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

def build_html_report(analysis: Dict[str, Any]) -> str:
    """Build a beautiful HTML email report."""
    
    ats_score = analysis.get("ats_score", {}).get("total_score", 0)
    tier = analysis.get("ats_score", {}).get("tier", "N/A")
    candidate_name = analysis.get("parsed_resume", {}).get("name", "Candidate")
    skills = analysis.get("parsed_resume", {}).get("skills", [])
    matched_keywords = analysis.get("ats_score", {}).get("matched_keywords", [])
    missing_keywords = analysis.get("ats_score", {}).get("missing_keywords", [])
    job_matches = analysis.get("job_matches", [])
    suggestions = analysis.get("suggestions", {})
    
    # Score color
    if ats_score >= 80:
        score_color = "#10b981"
    elif ats_score >= 65:
        score_color = "#3b82f6"
    elif ats_score >= 50:
        score_color = "#f59e0b"
    else:
        score_color = "#ef4444"
    
    # Build skills HTML
    skills_html = ""
    for skill in skills[:15]:
        skills_html += f'<span style="background:#1e3a5f;color:#60a5fa;padding:4px 10px;border-radius:4px;font-size:12px;margin:3px;display:inline-block;">{skill}</span>'
    
    # Build matched keywords HTML
    matched_html = ""
    for kw in matched_keywords[:10]:
        matched_html += f'<span style="background:#064e3b;color:#34d399;padding:3px 8px;border-radius:4px;font-size:12px;margin:2px;display:inline-block;">✓ {kw}</span>'
    
    # Build missing keywords HTML
    missing_html = ""
    for kw in missing_keywords[:10]:
        missing_html += f'<span style="background:#450a0a;color:#f87171;padding:3px 8px;border-radius:4px;font-size:12px;margin:2px;display:inline-block;">✗ {kw}</span>'
    
    # Build job matches HTML
    jobs_html = ""
    for job in job_matches[:3]:
        bar_width = job.get("match_score", 0)
        bar_color = "#10b981" if bar_width >= 70 else "#f59e0b" if bar_width >= 50 else "#ef4444"
        jobs_html += f"""
        <div style="background:#0f1e35;border:1px solid #1e3a5f;border-radius:8px;padding:16px;margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
                <strong style="color:#e2e8f0;font-size:16px;">{job.get('title','')}</strong>
                <span style="color:{bar_color};font-weight:bold;">{job.get('match_score',0):.0f}% Match</span>
            </div>
            <p style="color:#94a3b8;font-size:13px;margin:0 0 8px 0;">{job.get('description','')}</p>
            <div style="background:#1e3a5f;border-radius:4px;height:6px;overflow:hidden;">
                <div style="width:{bar_width}%;height:100%;background:{bar_color};"></div>
            </div>
            <div style="margin-top:8px;">
                <span style="color:#94a3b8;font-size:12px;">💰 {job.get('avg_salary','N/A')} &nbsp;|&nbsp; 📈 Demand: {job.get('demand','N/A')}</span>
            </div>
        </div>
        """
    
    # Build suggestions HTML
    all_suggestions = (
        suggestions.get("critical", []) +
        suggestions.get("improvements", []) +
        suggestions.get("skill_additions", []) +
        suggestions.get("formatting", []) +
        suggestions.get("keywords", [])
    )
    
    sugg_html = ""
    for sugg in all_suggestions[:6]:
        impact_color = "#ef4444" if sugg.get("impact") == "High" else "#f59e0b"
        sugg_html += f"""
        <div style="background:#0f1e35;border-left:3px solid {impact_color};border-radius:4px;padding:12px;margin-bottom:10px;">
            <div style="color:#e2e8f0;font-weight:bold;margin-bottom:4px;">{sugg.get('icon','')} {sugg.get('title','')}</div>
            <div style="color:#94a3b8;font-size:13px;">{sugg.get('detail','')}</div>
            <div style="margin-top:6px;"><span style="background:{impact_color}22;color:{impact_color};padding:2px 8px;border-radius:3px;font-size:11px;font-weight:bold;">{sugg.get('impact','')} IMPACT</span></div>
        </div>
        """
    
    html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0a0f1e;font-family:'Segoe UI',Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;background:#0a0f1e;">
    
    <!-- Header -->
    <div style="background:linear-gradient(135deg,#0f2044,#1a3a6b);padding:40px 32px;text-align:center;">
        <div style="font-size:36px;font-weight:900;color:#ffffff;letter-spacing:-1px;">
            ⚒ TalentForge
        </div>
        <div style="color:#93c5fd;font-size:14px;margin-top:4px;letter-spacing:2px;text-transform:uppercase;">
            Forging Careers with AI
        </div>
        <div style="color:#60a5fa;margin-top:16px;font-size:16px;">
            Resume Analysis Report for <strong>{candidate_name}</strong>
        </div>
    </div>
    
    <!-- ATS Score Hero -->
    <div style="background:#0f1e35;padding:32px;text-align:center;border-bottom:1px solid #1e3a5f;">
        <div style="font-size:80px;font-weight:900;color:{score_color};line-height:1;">{ats_score}</div>
        <div style="font-size:18px;color:#94a3b8;margin-top:4px;">ATS Compatibility Score</div>
        <div style="display:inline-block;background:{score_color}22;color:{score_color};padding:6px 20px;border-radius:20px;font-weight:bold;margin-top:12px;font-size:14px;">
            {tier}
        </div>
        <div style="background:#1e3a5f;border-radius:6px;height:10px;margin-top:20px;overflow:hidden;">
            <div style="width:{ats_score}%;height:100%;background:linear-gradient(90deg,{score_color},{score_color}88);border-radius:6px;"></div>
        </div>
    </div>
    
    <!-- Skills Section -->
    <div style="padding:28px 32px;border-bottom:1px solid #1e3a5f;">
        <h2 style="color:#e2e8f0;font-size:18px;margin:0 0 16px 0;">🛠 Detected Skills ({len(skills)})</h2>
        <div>{skills_html if skills_html else '<p style="color:#64748b;">No skills detected</p>'}</div>
    </div>
    
    <!-- Keyword Analysis -->
    <div style="padding:28px 32px;border-bottom:1px solid #1e3a5f;">
        <h2 style="color:#e2e8f0;font-size:18px;margin:0 0 16px 0;">🔍 Keyword Analysis</h2>
        <div style="margin-bottom:16px;">
            <div style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Matched ({len(matched_keywords)})</div>
            {matched_html if matched_html else '<span style="color:#64748b;font-size:13px;">No keywords matched</span>'}
        </div>
        <div>
            <div style="color:#64748b;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Missing ({len(missing_keywords)})</div>
            {missing_html if missing_html else '<span style="color:#34d399;font-size:13px;">✓ All keywords matched!</span>'}
        </div>
    </div>
    
    <!-- Job Matches -->
    <div style="padding:28px 32px;border-bottom:1px solid #1e3a5f;">
        <h2 style="color:#e2e8f0;font-size:18px;margin:0 0 16px 0;">💼 Top Job Matches</h2>
        {jobs_html if jobs_html else '<p style="color:#64748b;">No job matches available</p>'}
    </div>
    
    <!-- Suggestions -->
    <div style="padding:28px 32px;border-bottom:1px solid #1e3a5f;">
        <h2 style="color:#e2e8f0;font-size:18px;margin:0 0 16px 0;">💡 AI Improvement Suggestions</h2>
        <div style="background:#1e3a5f22;border-radius:8px;padding:12px 16px;margin-bottom:16px;color:#93c5fd;font-style:italic;">
            {suggestions.get('summary', '')}
        </div>
        {sugg_html}
    </div>
    
    <!-- Footer -->
    <div style="padding:24px 32px;text-align:center;background:#080d1a;">
        <div style="color:#374151;font-size:12px;">
            This report was generated by <strong style="color:#3b82f6;">TalentForge</strong> AI Resume Analyzer<br>
            Developed by <strong style="color:#60a5fa;">Abhishek Kumar Mishra</strong><br>
            <span style="color:#1f2937;margin-top:8px;display:block;">© 2024 TalentForge. All rights reserved.</span>
        </div>
    </div>
    
</div>
</body>
</html>
    """
    
    return html


def send_report_email(
    recipient_email: str,
    analysis: Dict[str, Any],
    smtp_user: str,
    smtp_password: str,
    smtp_host: str = "smtp.gmail.com",
    smtp_port: int = 587
) -> Dict[str, Any]:
    """
    Send resume analysis report via email.
    
    Args:
        recipient_email: Recipient's email address
        analysis: Complete analysis results dictionary
        smtp_user: Gmail address for sending
        smtp_password: Gmail App Password
        smtp_host: SMTP server host
        smtp_port: SMTP server port
        
    Returns:
        Dictionary with success/failure status
    """
    try:
        candidate_name = analysis.get("parsed_resume", {}).get("name", "Candidate")
        ats_score = analysis.get("ats_score", {}).get("total_score", 0)
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🎯 Your TalentForge Resume Report — ATS Score: {ats_score}/100"
        msg["From"] = f"TalentForge <{smtp_user}>"
        msg["To"] = recipient_email
        
        # Plain text fallback
        plain_text = f"""
TalentForge Resume Analysis Report
===================================
Candidate: {candidate_name}
ATS Score: {ats_score}/100
Tier: {analysis.get('ats_score', {}).get('tier', 'N/A')}

Skills Detected: {len(analysis.get('parsed_resume', {}).get('skills', []))}
Matched Keywords: {len(analysis.get('ats_score', {}).get('matched_keywords', []))}
Missing Keywords: {len(analysis.get('ats_score', {}).get('missing_keywords', []))}

Top Job Matches:
{chr(10).join([f"- {j.get('title','')}: {j.get('match_score',0):.0f}% match" for j in analysis.get('job_matches', [])[:3]])}

Generated by TalentForge | Developed by Abhishek Kumar Mishra
        """
        
        # HTML version
        html_content = build_html_report(analysis)
        
        # Attach both parts
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_content, "html"))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipient_email, msg.as_string())
        
        logger.info(f"Report email sent successfully to {recipient_email}")
        return {
            "success": True,
            "message": f"Report sent successfully to {recipient_email}"
        }
        
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed — check Gmail App Password")
        return {
            "success": False,
            "message": "Email authentication failed. Please check SMTP credentials."
        }
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return {
            "success": False,
            "message": f"Failed to send email: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Unexpected error sending email: {e}")
        return {
            "success": False,
            "message": f"An error occurred: {str(e)}"
        }
