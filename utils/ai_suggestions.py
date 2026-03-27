"""
AI Resume Suggestions Generator.
Provides actionable improvement suggestions for resumes.
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Weak phrases to replace
WEAK_PHRASES = {
    "responsible for": "Led / Managed / Oversaw",
    "worked on": "Developed / Built / Engineered",
    "helped with": "Contributed to / Collaborated on",
    "was involved in": "Participated in / Executed",
    "did": "Accomplished / Delivered / Achieved",
    "made": "Developed / Designed / Created",
    "good at": "Proficient in / Expert in",
    "familiar with": "Proficient in / Experienced with",
    "know": "Expert in / Proficient in",
    "tried to": "Successfully / Effectively"
}

# High-demand skills by category
HIGH_DEMAND_SKILLS = {
    "AI/ML": ["machine learning", "deep learning", "pytorch", "tensorflow", "llm", "transformers"],
    "Cloud": ["aws", "azure", "gcp", "kubernetes", "docker", "terraform"],
    "Data": ["sql", "python", "spark", "data visualization", "power bi", "tableau"],
    "Web": ["react", "node.js", "typescript", "graphql", "next.js"],
    "DevOps": ["ci/cd", "github actions", "ansible", "monitoring", "linux"]
}

def check_quantification(text: str) -> Dict[str, Any]:
    """Check if resume has quantified achievements."""
    pattern = re.compile(
        r'\b\d+[\%\+]?\s*(percent|%|million|thousand|users|customers|'
        r'team members|engineers|projects|years|months|x|times|hours|'
        r'minutes|seconds|dollars|revenue|growth|improvement)\b',
        re.IGNORECASE
    )
    matches = pattern.findall(text)
    
    return {
        "has_quantification": len(matches) > 2,
        "count": len(matches),
        "sufficient": len(matches) >= 5
    }

def check_weak_language(text: str) -> List[Dict[str, str]]:
    """Identify weak language patterns."""
    findings = []
    text_lower = text.lower()
    
    for phrase, replacement in WEAK_PHRASES.items():
        if phrase in text_lower:
            findings.append({
                "weak": phrase,
                "strong": replacement,
                "type": "language"
            })
    
    return findings

def check_skills_gaps(skills: List[str]) -> List[Dict[str, Any]]:
    """Identify high-demand skill gaps."""
    skills_lower = [s.lower() for s in skills]
    gaps = []
    
    for category, category_skills in HIGH_DEMAND_SKILLS.items():
        has_any = any(
            any(cs in rs or rs in cs for rs in skills_lower)
            for cs in category_skills
        )
        if not has_any:
            gaps.append({
                "category": category,
                "suggested_skills": category_skills[:3],
                "priority": "High" if category in ["AI/ML", "Cloud"] else "Medium"
            })
    
    return gaps

def check_resume_sections(text: str) -> List[Dict[str, str]]:
    """Check for missing important resume sections."""
    text_lower = text.lower()
    missing_sections = []
    
    sections = {
        "Professional Summary": ["summary", "objective", "profile", "about"],
        "Skills Section": ["skills", "technical skills", "competencies"],
        "Work Experience": ["experience", "employment", "work history", "positions"],
        "Education": ["education", "academic", "degree", "university"],
        "Projects": ["projects", "portfolio", "work samples"],
        "Certifications": ["certifications", "certificates", "licensed", "certified"]
    }
    
    for section_name, keywords in sections.items():
        if not any(kw in text_lower for kw in keywords):
            missing_sections.append({
                "section": section_name,
                "importance": "Critical" if section_name in ["Work Experience", "Skills Section"] else "Recommended"
            })
    
    return missing_sections

def generate_suggestions(
    resume_text: str,
    skills: List[str],
    ats_score: float,
    missing_keywords: List[str]
) -> Dict[str, Any]:
    """
    Generate comprehensive resume improvement suggestions.
    
    Args:
        resume_text: Full resume text
        skills: Extracted skills list
        ats_score: Current ATS score
        missing_keywords: Keywords missing from job description match
        
    Returns:
        Dictionary of categorized suggestions
    """
    suggestions = {
        "critical": [],
        "improvements": [],
        "skill_additions": [],
        "formatting": [],
        "keywords": [],
        "summary": ""
    }
    
    try:
        # 1. Check quantification
        quant_check = check_quantification(resume_text)
        if not quant_check["sufficient"]:
            suggestions["critical"].append({
                "title": "Add Quantified Achievements",
                "detail": "Add specific numbers to showcase impact. Example: 'Improved system performance by 40%' instead of 'Improved performance'.",
                "impact": "High",
                "icon": "📊"
            })
        
        # 2. Check weak language
        weak_lang = check_weak_language(resume_text)
        if weak_lang:
            examples = "; ".join([f'"{w["weak"]}" → {w["strong"]}' for w in weak_lang[:3]])
            suggestions["improvements"].append({
                "title": "Replace Weak Language",
                "detail": f"Upgrade passive phrases with powerful action verbs. Examples: {examples}",
                "impact": "High",
                "icon": "✍️"
            })
        
        # 3. Check skills gaps
        skill_gaps = check_skills_gaps(skills)
        for gap in skill_gaps[:3]:
            suggestions["skill_additions"].append({
                "title": f"Add {gap['category']} Skills",
                "detail": f"Consider adding: {', '.join(gap['suggested_skills'])}",
                "impact": gap["priority"],
                "icon": "🚀"
            })
        
        # 4. Check missing sections
        missing_sections = check_resume_sections(resume_text)
        for section in missing_sections[:3]:
            suggestions["formatting"].append({
                "title": f"Add {section['section']}",
                "detail": f"A {section['section']} section is {section['importance'].lower()} for a complete resume.",
                "impact": section["importance"],
                "icon": "📋"
            })
        
        # 5. Missing keywords from JD
        if missing_keywords:
            top_missing = missing_keywords[:8]
            suggestions["keywords"].append({
                "title": "Incorporate Missing Keywords",
                "detail": f"Add these job-relevant keywords naturally: {', '.join(top_missing)}",
                "impact": "High",
                "icon": "🔑"
            })
        
        # 6. Word count check
        word_count = len(resume_text.split())
        if word_count < 250:
            suggestions["formatting"].append({
                "title": "Expand Resume Content",
                "detail": f"Your resume has {word_count} words. Aim for 400-700 words with detailed descriptions.",
                "impact": "Medium",
                "icon": "📝"
            })
        elif word_count > 1000:
            suggestions["formatting"].append({
                "title": "Trim Resume Length",
                "detail": f"Your resume has {word_count} words. Aim for 400-700 words; be concise and impactful.",
                "impact": "Medium",
                "icon": "✂️"
            })
        
        # 7. Skills count check
        if len(skills) < 8:
            suggestions["skill_additions"].append({
                "title": "Expand Your Skills List",
                "detail": f"Only {len(skills)} skills detected. Aim for 12-20 relevant technical and soft skills.",
                "impact": "High",
                "icon": "💡"
            })
        
        # Generate summary
        total_suggestions = (len(suggestions["critical"]) + len(suggestions["improvements"]) + 
                           len(suggestions["skill_additions"]) + len(suggestions["formatting"]))
        
        if ats_score >= 80:
            summary = f"Strong resume! {total_suggestions} minor improvements identified to reach ATS excellence."
        elif ats_score >= 60:
            summary = f"Good foundation! Focus on {total_suggestions} key areas to significantly boost your ATS score."
        else:
            summary = f"Major opportunity! Address these {total_suggestions} improvements to dramatically increase your chances."
        
        suggestions["summary"] = summary
        
    except Exception as e:
        logger.error(f"Error generating suggestions: {e}")
        suggestions["summary"] = "Analysis complete. Review suggestions above."
    
    return suggestions
