"""
CV Parser: Extracts structured information from raw CV text.
Uses spaCy NER + regex patterns + LLM enrichment.
"""
import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

# ─── spaCy ────────────────────────────────────────────────────────────────────
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not available – NER disabled")

from backend.config.settings import settings
from backend.models.candidate import (
    Skill, Education, Experience, CandidateProfile, CandidateCreate
)


# ─── Known skill keywords ─────────────────────────────────────────────────────
TECH_SKILLS = {
    # Programming Languages
    "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
    "kotlin", "swift", "php", "ruby", "scala", "r", "matlab", "dart", "sql", "bash", "powershell",
    # Frameworks & Libraries
    "react", "angular", "vue", "next.js", "nuxt.js", "fastapi", "django",
    "flask", "spring", "express", "nestjs", "laravel", "rails",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "langchain", "langgraph", "huggingface", "transformers", "tailwind", "bootstrap",
    # Databases & Storage
    "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "sqlite",
    "cassandra", "dynamodb", "neo4j", "oracle", "mariadb", "bigquery", "snowflake", "nosql",
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform", "ansible",
    "jenkins", "github actions", "gitlab ci", "helm", "devops", "ci/cd", "prometheus", "grafana",
    # AI/ML
    "machine learning", "deep learning", "nlp", "computer vision",
    "data science", "ai", "llm", "rag", "fine-tuning", "bert", "gpt", "opencv",
    # Other / Concepts
    "git", "linux", "rest api", "graphql", "microservices", "agile", "scrum", "api", "rest", "soap",
    "backend", "frontend", "fullstack", "full-stack", "unit testing", "ci-cd",
}

DEGREE_KEYWORDS = {
    "bachelor", "master", "phd", "doctorate", "associate", "diploma",
    "bsc", "msc", "mba", "licence", "ingénieur", "engineer",
    "b.s.", "m.s.", "b.e.", "m.e.",
}

SECTION_MARKERS = {
    "experience": ["experience", "work experience", "professional experience",
                   "employment", "career", "expérience"],
    "education": ["education", "academic", "qualifications", "formation",
                  "études", "university", "degree"],
    "skills": ["skills", "technical skills", "competencies", "technologies",
               "stack", "compétences"],
    "certifications": ["certifications", "certificates", "courses", "licenses"],
    "projects": ["projects", "portfolio", "projets"],
    "languages": ["languages", "langues"],
}


class CVParser:
    """
    Parses raw CV text into structured CandidateProfile data.
    Strategy: regex extraction + spaCy NER + pattern matching.
    """

    _nlp = None

    @classmethod
    def _get_nlp(cls):
        if cls._nlp is None and SPACY_AVAILABLE:
            try:
                cls._nlp = spacy.load(settings.SPACY_MODEL)
                logger.info(f"spaCy model loaded: {settings.SPACY_MODEL}")
            except OSError:
                logger.warning(
                    f"spaCy model '{settings.SPACY_MODEL}' not found. "
                    f"Run: python -m spacy download {settings.SPACY_MODEL}"
                )
                cls._nlp = None
        return cls._nlp

    def parse(self, raw_text: str, filename: str = "") -> Dict[str, Any]:
        """
        Parse raw CV text and return a structured dictionary.
        """
        if not raw_text or not raw_text.strip():
            return {}

        result: Dict[str, Any] = {
            "raw_text": raw_text,
            "full_name": None,
            "email": None,
            "phone": None,
            "location": None,
            "linkedin_url": None,
            "github_url": None,
            "portfolio_url": None,
            "skills": [],
            "education": [],
            "experience": [],
            "certifications": [],
            "languages": [],
            "summary": None,
            "years_experience": None,
        }

        # Extract contact info via regex
        result["email"] = self._extract_email(raw_text)
        result["phone"] = self._extract_phone(raw_text)
        result["linkedin_url"] = self._extract_url(raw_text, "linkedin")
        result["github_url"] = self._extract_url(raw_text, "github")
        result["portfolio_url"] = self._extract_portfolio_url(raw_text)

        # Extract name via NER or heuristics
        result["full_name"] = self._extract_name(raw_text, filename)

        # Extract structured sections
        sections = self._split_into_sections(raw_text)
        result["skills"] = self._extract_skills(raw_text, sections.get("skills", ""))
        result["education"] = self._extract_education(sections.get("education", ""))
        result["experience"] = self._extract_experience(sections.get("experience", ""))
        result["certifications"] = self._extract_certifications(sections.get("certifications", ""))
        result["languages"] = self._extract_languages(sections.get("languages", ""))
        result["summary"] = self._extract_summary(raw_text)
        result["years_experience"] = self._calculate_years_experience(result["experience"])

        return result

    # ─── Contact extraction ───────────────────────────────────────────────────

    def _extract_email(self, text: str) -> Optional[str]:
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(pattern, text)
        return match.group(0).lower() if match else None

    def _extract_phone(self, text: str) -> Optional[str]:
        patterns = [
            r'\+?[\d\s\-\(\)]{10,15}',
            r'\b\d{2}[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2}[\s\-]?\d{2}\b',
            r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',
        ]
        for pat in patterns:
            match = re.search(pat, text)
            if match:
                phone = re.sub(r'\s+', ' ', match.group(0).strip())
                if len(re.sub(r'\D', '', phone)) >= 8:
                    return phone
        return None

    def _extract_url(self, text: str, platform: str) -> Optional[str]:
        pattern = rf'https?://(?:www\.)?{platform}\.com/[^\s<>"\']+'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
        # Try handle-only format
        pattern2 = rf'{platform}\.com/([A-Za-z0-9\-_]+)'
        match2 = re.search(pattern2, text, re.IGNORECASE)
        if match2:
            return f"https://{platform}.com/{match2.group(1)}"
        return None

    def _extract_portfolio_url(self, text: str) -> Optional[str]:
        pattern = r'https?://[^\s<>"\']+\.(dev|io|com|net|me|app)[^\s<>"\']*'
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            url = m if isinstance(m, str) else m[0]
            if "linkedin" not in url and "github" not in url:
                return url
        return None

    # ─── Name extraction ──────────────────────────────────────────────────────

    def _extract_name(self, text: str, filename: str = "") -> Optional[str]:
        # Try spaCy first
        nlp = self._get_nlp()
        if nlp:
            doc = nlp(text[:500])  # Only first 500 chars
            persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
            if persons:
                return persons[0]

        # Try from first non-empty line
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if lines:
            first_line = lines[0]
            if len(first_line.split()) <= 5 and first_line.replace(" ", "").isalpha():
                return first_line.title()

        # Try from filename
        if filename:
            base = re.sub(r'[_\-\.]+', ' ', filename.replace(".pdf", "").replace(".docx", ""))
            words = base.split()
            if 2 <= len(words) <= 4:
                filtered = [w for w in words if w.lower() not in {"cv", "resume", "fr", "en"}]
                if filtered:
                    return " ".join(filtered).title()

        return None

    # ─── Section splitting ────────────────────────────────────────────────────

    def _split_into_sections(self, text: str) -> Dict[str, str]:
        sections: Dict[str, str] = {}
        lines = text.split("\n")
        current_section: Optional[str] = None
        current_content: List[str] = []

        for line in lines:
            line_lower = line.strip().lower()
            found_section = None
            for section_name, markers in SECTION_MARKERS.items():
                if any(marker in line_lower for marker in markers):
                    if len(line_lower) < 50:  # It's likely a header
                        found_section = section_name
                        break

            if found_section:
                if current_section:
                    sections[current_section] = "\n".join(current_content)
                current_section = found_section
                current_content = []
            else:
                if current_section:
                    current_content.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_content)

        return sections

    # ─── Skills extraction ────────────────────────────────────────────────────

    def _extract_skills(self, full_text: str, skills_section: str) -> List[Dict[str, Any]]:
        search_text = (skills_section or full_text).lower()
        found: List[Dict[str, Any]] = []
        seen: set = set()

        for skill in TECH_SKILLS:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, search_text):
                if skill not in seen:
                    seen.add(skill)
                    found.append({
                        "name": skill.title() if len(skill) > 3 else skill.upper(),
                        "level": None,
                        "years": None
                    })

        return found[:30]  # Cap at 30 skills

    # ─── Education extraction ─────────────────────────────────────────────────

    def _extract_education(self, section_text: str) -> List[Dict[str, Any]]:
        if not section_text:
            return []

        educations: List[Dict[str, Any]] = []
        blocks = re.split(r'\n{2,}', section_text.strip())

        for block in blocks:
            if not block.strip():
                continue
            edu: Dict[str, Any] = {
                "degree": None, "field": None,
                "institution": None, "year": None, "gpa": None
            }
            block_lower = block.lower()

            # Detect degree
            for deg in DEGREE_KEYWORDS:
                if deg in block_lower:
                    edu["degree"] = deg.title()
                    break

            # Detect year
            year_match = re.search(r'\b(19|20)\d{2}\b', block)
            if year_match:
                edu["year"] = int(year_match.group(0))

            # First non-empty line is likely institution or degree
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if lines:
                edu["institution"] = lines[0]

            if edu["degree"] or edu["institution"]:
                educations.append(edu)

        return educations

    # ─── Experience extraction ────────────────────────────────────────────────

    def _extract_experience(self, section_text: str) -> List[Dict[str, Any]]:
        if not section_text:
            return []

        experiences: List[Dict[str, Any]] = []
        blocks = re.split(r'\n{2,}', section_text.strip())

        for block in blocks:
            if len(block.strip()) < 20:
                continue
            exp: Dict[str, Any] = {
                "title": None, "company": None,
                "start_date": None, "end_date": None,
                "duration_months": None, "description": None,
                "technologies": []
            }

            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if lines:
                exp["title"] = lines[0]
            if len(lines) > 1:
                exp["company"] = lines[1]

            # Date patterns
            date_pattern = r'(\w+\s+\d{4}|\d{4})\s*[-–—]\s*(\w+\s+\d{4}|\d{4}|present|now|current)'
            date_match = re.search(date_pattern, block, re.IGNORECASE)
            if date_match:
                exp["start_date"] = date_match.group(1)
                exp["end_date"] = date_match.group(2)

            # Tech keywords in this block
            block_lower = block.lower()
            techs = [s["name"] for s in self._extract_skills("", block_lower)]
            exp["technologies"] = techs[:10]
            exp["description"] = "\n".join(lines[2:])[:300]

            if exp["title"]:
                experiences.append(exp)

        return experiences

    # ─── Other extractions ────────────────────────────────────────────────────

    def _extract_certifications(self, section_text: str) -> List[str]:
        if not section_text:
            return []
        certs = []
        for line in section_text.split("\n"):
            line = line.strip("•-–* \t")
            if len(line) > 5:
                certs.append(line)
        return certs[:10]

    def _extract_languages(self, section_text: str) -> List[str]:
        known_languages = [
            "english", "french", "arabic", "spanish", "german", "italian",
            "portuguese", "chinese", "japanese", "russian", "dutch",
            "anglais", "français", "arabe", "espagnol", "allemand"
        ]
        found = []
        text_lower = (section_text or "").lower()
        for lang in known_languages:
            if lang in text_lower:
                found.append(lang.title())
        return list(set(found))

    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract professional summary or objective section."""
        patterns = [
            r'(?:summary|objective|profile|about me)[:\n]+(.{50,500})',
            r'(?:résumé|profil|à propos)[:\n]+(.{50,500})',
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE | re.DOTALL)
            if match:
                summary = match.group(1).strip()
                # Limit to first paragraph
                summary = summary.split("\n\n")[0]
                return summary[:500]
        return None

    def _calculate_years_experience(self, experiences: List[Dict[str, Any]]) -> Optional[float]:
        """Estimate total years of experience from experience blocks."""
        if not experiences:
            return None
        years = 0
        for exp in experiences:
            if exp.get("start_date") and exp.get("end_date"):
                start_y = re.search(r'\d{4}', str(exp["start_date"]))
                end_y = re.search(r'\d{4}', str(exp["end_date"]))
                if start_y and end_y:
                    end_year = int(end_y.group(0))
                    if str(exp["end_date"]).lower() in ("present", "now", "current"):
                        end_year = datetime.now().year
                    years += max(0, end_year - int(start_y.group(0)))
        return float(years) if years > 0 else None


# Module singleton
cv_parser = CVParser()
