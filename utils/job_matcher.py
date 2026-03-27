"""
Job Role Matcher - Recommends job roles based on extracted resume skills.
"""

import json
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def load_job_roles() -> List[Dict]:
    """Load job roles from JSON dataset."""
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'job_roles.json')
    try:
        with open(data_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading job roles: {e}")
        return []

def calculate_match_score(resume_skills: List[str], job_skills: List[str]) -> float:
    """Calculate match percentage between resume skills and job requirements."""
    if not job_skills:
        return 0.0
    
    resume_skills_lower = [s.lower() for s in resume_skills]
    job_skills_lower = [s.lower() for s in job_skills]
    
    matched = 0
    for job_skill in job_skills_lower:
        # Check exact match or partial match
        for resume_skill in resume_skills_lower:
            if job_skill in resume_skill or resume_skill in job_skill:
                matched += 1
                break
    
    return (matched / len(job_skills_lower)) * 100

def match_jobs(resume_skills: List[str], top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Match resume skills against job roles dataset.
    
    Args:
        resume_skills: List of skills extracted from resume
        top_n: Number of top matches to return
        
    Returns:
        List of matched job roles with scores
    """
    job_roles = load_job_roles()
    
    if not job_roles:
        return []
    
    scored_roles = []
    for role in job_roles:
        score = calculate_match_score(resume_skills, role.get("skills", []))
        
        # Get matched and missing skills
        resume_skills_lower = [s.lower() for s in resume_skills]
        job_skills_lower = [s.lower() for s in role.get("skills", [])]
        
        matched_skills = []
        missing_skills = []
        
        for skill in job_skills_lower:
            is_matched = any(skill in rs or rs in skill for rs in resume_skills_lower)
            if is_matched:
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)
        
        scored_roles.append({
            "title": role["title"],
            "match_score": round(score, 1),
            "description": role.get("description", ""),
            "avg_salary": role.get("avg_salary", "N/A"),
            "demand": role.get("demand", "Moderate"),
            "required_skills": role.get("skills", []),
            "matched_skills": matched_skills,
            "missing_skills": missing_skills[:5],  # Top 5 missing skills
            "skill_gap": len(missing_skills)
        })
    
    # Sort by match score descending
    scored_roles.sort(key=lambda x: x["match_score"], reverse=True)
    
    return scored_roles[:top_n]
