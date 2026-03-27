"""
Resume parsing utility using spaCy and pattern matching.
Extracts skills, education, experience from resume text.
"""

import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# Comprehensive skills database
SKILLS_DATABASE = {
    "programming": [
        "python", "java", "javascript", "typescript", "c++", "c#", "c", "ruby", "go", "golang",
        "rust", "swift", "kotlin", "scala", "php", "r", "matlab", "perl", "shell", "bash",
        "powershell", "dart", "flutter", "elixir", "haskell", "clojure", "groovy", "lua"
    ],
    "web": [
        "html", "css", "react", "angular", "vue", "node.js", "nodejs", "express", "django",
        "flask", "fastapi", "spring", "laravel", "rails", "next.js", "nuxt", "gatsby",
        "webpack", "vite", "tailwind", "bootstrap", "jquery", "graphql", "rest api",
        "websocket", "sass", "less"
    ],
    "data_ml": [
        "machine learning", "deep learning", "neural networks", "tensorflow", "pytorch",
        "keras", "scikit-learn", "pandas", "numpy", "scipy", "matplotlib", "seaborn",
        "nlp", "computer vision", "data science", "statistics", "reinforcement learning",
        "transformers", "bert", "gpt", "llm", "spacy", "nltk", "opencv"
    ],
    "cloud_devops": [
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
        "ansible", "jenkins", "ci/cd", "github actions", "devops", "mlops", "linux",
        "nginx", "apache", "microservices", "serverless", "lambda", "s3", "ec2"
    ],
    "database": [
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch", "cassandra",
        "oracle", "sqlite", "dynamodb", "firebase", "nosql", "data warehouse",
        "snowflake", "bigquery", "spark", "hadoop", "kafka", "airflow", "etl"
    ],
    "tools": [
        "git", "github", "gitlab", "jira", "confluence", "agile", "scrum", "kanban",
        "figma", "sketch", "photoshop", "illustrator", "tableau", "power bi",
        "excel", "jupyter", "vs code", "postman", "linux", "unix", "vim"
    ],
    "soft_skills": [
        "leadership", "communication", "teamwork", "problem solving", "critical thinking",
        "project management", "time management", "analytical", "collaborative", "mentoring"
    ]
}

# Flatten skills list
ALL_SKILLS = []
for category, skills in SKILLS_DATABASE.items():
    ALL_SKILLS.extend(skills)

# Education keywords
EDUCATION_KEYWORDS = [
    "bachelor", "master", "phd", "doctorate", "b.s.", "m.s.", "b.tech", "m.tech",
    "b.e.", "m.e.", "mba", "b.sc", "m.sc", "associate", "diploma", "degree",
    "university", "college", "institute", "school", "graduated", "graduation",
    "computer science", "engineering", "mathematics", "physics", "statistics",
    "information technology", "data science", "artificial intelligence"
]

# Experience action verbs
ACTION_VERBS = [
    "developed", "designed", "implemented", "built", "created", "led", "managed",
    "architected", "optimized", "improved", "deployed", "maintained", "collaborated",
    "analyzed", "researched", "engineered", "automated", "integrated", "delivered",
    "launched", "established", "streamlined", "reduced", "increased", "achieved",
    "coordinated", "supervised", "mentored", "trained", "presented", "published"
]

def extract_skills(text: str) -> List[str]:
    """Extract skills from resume text."""
    text_lower = text.lower()
    found_skills = []
    
    for skill in ALL_SKILLS:
        # Use word boundary matching for better accuracy
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_skills.append(skill)
    
    # Deduplicate while preserving order
    seen = set()
    unique_skills = []
    for skill in found_skills:
        if skill not in seen:
            seen.add(skill)
            unique_skills.append(skill)
    
    return unique_skills

def extract_education(text: str) -> List[Dict[str, str]]:
    """Extract education information from resume text."""
    education_entries = []
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in EDUCATION_KEYWORDS):
            # Get surrounding context (lines before/after)
            start = max(0, i - 1)
            end = min(len(lines), i + 3)
            context = ' '.join(lines[start:end]).strip()
            
            if context and len(context) > 10:
                education_entries.append({
                    "detail": context[:200],
                    "line": line.strip()
                })
    
    # Deduplicate
    seen = set()
    unique_education = []
    for entry in education_entries:
        key = entry["line"][:50]
        if key not in seen and len(entry["line"]) > 5:
            seen.add(key)
            unique_education.append(entry)
    
    return unique_education[:5]  # Limit to 5 entries

def extract_experience(text: str) -> List[Dict[str, str]]:
    """Extract work experience from resume text."""
    experience_entries = []
    lines = text.split('\n')
    
    # Year pattern for identifying experience entries
    year_pattern = re.compile(r'\b(19|20)\d{2}\b')
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        line_stripped = line.strip()
        
        # Check for action verbs (bullet points of experience)
        has_action_verb = any(verb in line_lower for verb in ACTION_VERBS)
        has_year = bool(year_pattern.search(line))
        
        if (has_action_verb or has_year) and len(line_stripped) > 20:
            experience_entries.append({
                "detail": line_stripped[:250],
                "has_year": has_year
            })
    
    return experience_entries[:10]  # Limit to 10 entries

def extract_contact_info(text: str) -> Dict[str, str]:
    """Extract contact information from resume."""
    contact = {}
    
    # Email
    email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    emails = email_pattern.findall(text)
    if emails:
        contact['email'] = emails[0]
    
    # Phone
    phone_pattern = re.compile(r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}')
    phones = phone_pattern.findall(text)
    if phones:
        contact['phone'] = phones[0]
    
    # LinkedIn
    linkedin_pattern = re.compile(r'linkedin\.com/in/[\w-]+', re.IGNORECASE)
    linkedin = linkedin_pattern.findall(text)
    if linkedin:
        contact['linkedin'] = linkedin[0]
    
    # GitHub
    github_pattern = re.compile(r'github\.com/[\w-]+', re.IGNORECASE)
    github = github_pattern.findall(text)
    if github:
        contact['github'] = github[0]
    
    return contact

def extract_name(text: str) -> str:
    """Attempt to extract candidate name from resume."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    if lines:
        # First non-empty line is often the name
        first_line = lines[0]
        # Check it's likely a name (no special chars, reasonable length)
        if 2 < len(first_line) < 50 and re.match(r'^[A-Za-z\s\.\-]+$', first_line):
            return first_line
    
    return "Candidate"

def parse_resume(text: str) -> Dict[str, Any]:
    """
    Main function to parse resume and extract all information.
    
    Args:
        text: Raw text content of the resume
        
    Returns:
        Dictionary containing parsed resume data
    """
    try:
        result = {
            "name": extract_name(text),
            "contact": extract_contact_info(text),
            "skills": extract_skills(text),
            "education": extract_education(text),
            "experience": extract_experience(text),
            "word_count": len(text.split()),
            "char_count": len(text)
        }
        
        logger.info(f"Resume parsed: {len(result['skills'])} skills, "
                   f"{len(result['education'])} education entries, "
                   f"{len(result['experience'])} experience entries")
        
        return result
        
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        return {
            "name": "Unknown",
            "contact": {},
            "skills": [],
            "education": [],
            "experience": [],
            "word_count": 0,
            "char_count": 0,
            "error": str(e)
        }
