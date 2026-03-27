"""
ATS Score Calculator and Resume Analyzer.
Compares resume with job description to generate ATS compatibility score.
"""

import re
import logging
from typing import Dict, List, Any, Tuple
from collections import Counter

logger = logging.getLogger(__name__)

# Weights for different scoring components
WEIGHTS = {
    "keyword_match": 0.40,      # 40% - skill/keyword matching
    "education_match": 0.15,    # 15% - education relevance
    "experience_indicators": 0.20,  # 20% - experience signals
    "formatting_quality": 0.10,  # 10% - document quality
    "contact_info": 0.05,       # 5%  - contact completeness
    "action_verbs": 0.10        # 10% - strong action verbs usage
}

STRONG_ACTION_VERBS = [
    "achieved", "accelerated", "architected", "automated", "built", "championed",
    "collaborated", "created", "delivered", "designed", "developed", "drove",
    "engineered", "established", "exceeded", "executed", "generated", "implemented",
    "improved", "increased", "innovated", "integrated", "launched", "led", "managed",
    "mentored", "optimized", "oversaw", "pioneered", "produced", "reduced", "scaled",
    "streamlined", "transformed", "unified"
]

def extract_keywords(text: str) -> List[str]:
    """Extract meaningful keywords from text."""
    # Remove common stop words
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "up", "about", "into", "through", "during",
        "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "will", "would", "could", "should", "may", "might",
        "must", "can", "this", "that", "these", "those", "we", "you", "they",
        "he", "she", "it", "our", "your", "their", "its", "we", "i"
    }
    
    # Tokenize and clean
    text_lower = text.lower()
    # Extract words and multi-word phrases
    words = re.findall(r'\b[a-z][a-z\+\#\.\/\-]*[a-z]\b', text_lower)
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    
    return keywords

def calculate_keyword_score(resume_text: str, jd_text: str) -> Tuple[float, List[str], List[str]]:
    """
    Calculate keyword match score between resume and job description.
    Returns: (score 0-100, matched_keywords, missing_keywords)
    """
    jd_keywords = set(extract_keywords(jd_text))
    resume_keywords = set(extract_keywords(resume_text))
    
    if not jd_keywords:
        return 50.0, [], []
    
    # Find matches and misses
    matched = jd_keywords.intersection(resume_keywords)
    missing = jd_keywords - resume_keywords
    
    # Calculate score
    score = (len(matched) / len(jd_keywords)) * 100
    
    # Filter to meaningful keywords only (length > 3)
    matched_list = sorted([k for k in matched if len(k) > 3])[:20]
    missing_list = sorted([k for k in missing if len(k) > 3])[:20]
    
    return min(score, 100), matched_list, missing_list

def calculate_experience_score(resume_text: str) -> float:
    """Score based on experience indicators in resume."""
    score = 0
    text_lower = resume_text.lower()
    
    # Check for quantified achievements (numbers in context)
    number_pattern = re.compile(r'\b\d+[\%\+]?\s*(percent|million|thousand|users|customers|team|members|projects|years|months|x)\b', re.IGNORECASE)
    quantified = number_pattern.findall(resume_text)
    score += min(len(quantified) * 8, 40)  # Up to 40 points
    
    # Check for job titles/positions
    position_keywords = ["senior", "lead", "manager", "engineer", "developer", "analyst",
                        "architect", "director", "intern", "associate", "principal"]
    position_count = sum(1 for kw in position_keywords if kw in text_lower)
    score += min(position_count * 5, 30)  # Up to 30 points
    
    # Check for year ranges (work experience periods)
    year_ranges = re.findall(r'\b20\d{2}\s*[-–]\s*(20\d{2}|present|current)\b', resume_text, re.IGNORECASE)
    score += min(len(year_ranges) * 10, 30)  # Up to 30 points
    
    return min(score, 100)

def calculate_formatting_score(resume_text: str) -> float:
    """Score based on resume formatting quality."""
    score = 0
    
    # Check word count (ideal: 300-800 words)
    word_count = len(resume_text.split())
    if 300 <= word_count <= 800:
        score += 40
    elif 200 <= word_count < 300 or 800 < word_count <= 1000:
        score += 25
    else:
        score += 10
    
    # Check for section headers
    headers = ["experience", "education", "skills", "projects", "summary", 
               "objective", "certifications", "achievements", "publications"]
    header_count = sum(1 for h in headers if h in resume_text.lower())
    score += min(header_count * 8, 40)  # Up to 40 points
    
    # Check for bullet points / structured content
    bullet_patterns = re.findall(r'^[\s]*[•\-\*\➢\▸\►]', resume_text, re.MULTILINE)
    if len(bullet_patterns) >= 5:
        score += 20
    elif len(bullet_patterns) >= 2:
        score += 10
    
    return min(score, 100)

def calculate_action_verb_score(resume_text: str) -> float:
    """Score based on use of strong action verbs."""
    text_lower = resume_text.lower()
    verb_count = sum(1 for verb in STRONG_ACTION_VERBS if re.search(r'\b' + verb + r'\b', text_lower))
    return min((verb_count / 8) * 100, 100)

def calculate_contact_score(contact_info: Dict) -> float:
    """Score based on completeness of contact information."""
    score = 0
    if contact_info.get("email"):
        score += 40
    if contact_info.get("phone"):
        score += 30
    if contact_info.get("linkedin"):
        score += 20
    if contact_info.get("github"):
        score += 10
    return score

def calculate_ats_score(
    resume_text: str, 
    jd_text: str,
    contact_info: Dict = None
) -> Dict[str, Any]:
    """
    Calculate comprehensive ATS score for a resume against a job description.
    
    Args:
        resume_text: Raw text of resume
        jd_text: Job description text
        contact_info: Extracted contact information
        
    Returns:
        Dictionary with scores and analysis
    """
    try:
        contact_info = contact_info or {}
        
        # Calculate component scores
        keyword_score, matched_keywords, missing_keywords = calculate_keyword_score(resume_text, jd_text)
        experience_score = calculate_experience_score(resume_text)
        formatting_score = calculate_formatting_score(resume_text)
        action_verb_score = calculate_action_verb_score(resume_text)
        contact_score = calculate_contact_score(contact_info)
        
        # Education always gets partial credit
        education_score = 70.0  # Base score, adjust with actual parsing
        
        # Calculate weighted total
        total_score = (
            keyword_score * WEIGHTS["keyword_match"] +
            education_score * WEIGHTS["education_match"] +
            experience_score * WEIGHTS["experience_indicators"] +
            formatting_score * WEIGHTS["formatting_quality"] +
            contact_score * WEIGHTS["contact_info"] +
            action_verb_score * WEIGHTS["action_verbs"]
        )
        
        total_score = round(min(total_score, 100), 1)
        
        # Determine score tier
        if total_score >= 80:
            tier = "Excellent"
            tier_color = "#10b981"
            tier_description = "Your resume is highly optimized for ATS systems!"
        elif total_score >= 65:
            tier = "Good"
            tier_color = "#3b82f6"
            tier_description = "Your resume performs well but has room for improvement."
        elif total_score >= 50:
            tier = "Average"
            tier_color = "#f59e0b"
            tier_description = "Your resume needs moderate improvements to pass ATS filters."
        else:
            tier = "Needs Work"
            tier_color = "#ef4444"
            tier_description = "Your resume requires significant improvements for ATS compatibility."
        
        return {
            "total_score": total_score,
            "tier": tier,
            "tier_color": tier_color,
            "tier_description": tier_description,
            "component_scores": {
                "keyword_match": round(keyword_score, 1),
                "experience": round(experience_score, 1),
                "formatting": round(formatting_score, 1),
                "action_verbs": round(action_verb_score, 1),
                "contact_info": round(contact_score, 1),
                "education": round(education_score, 1)
            },
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "keyword_match_count": len(matched_keywords),
            "missing_keyword_count": len(missing_keywords)
        }
        
    except Exception as e:
        logger.error(f"Error calculating ATS score: {e}")
        return {
            "total_score": 0,
            "tier": "Error",
            "tier_color": "#ef4444",
            "tier_description": "An error occurred during scoring.",
            "component_scores": {},
            "matched_keywords": [],
            "missing_keywords": [],
            "error": str(e)
        }
