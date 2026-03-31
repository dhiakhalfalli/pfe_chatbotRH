"""
GitHub Tool: Fetch and score a candidate's GitHub profile.
Uses the GitHub REST API with optional authentication.
"""
import logging
import re
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not available – GitHub tool disabled")

from backend.config.settings import settings


class GitHubTool:
    """Fetches GitHub profile data and computes a contribution score."""

    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HR-Platform/1.0",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def extract_username(self, github_url: str) -> Optional[str]:
        """Extract GitHub username from a URL."""
        if not github_url:
            return None
        patterns = [
            r'github\.com/([A-Za-z0-9\-_.]+)',
            r'^([A-Za-z0-9\-_.]+)$',  # Raw username
        ]
        for pat in patterns:
            match = re.search(pat, github_url)
            if match:
                username = match.group(1).rstrip("/")
                if username not in {"repos", "", "features"}:
                    return username
        return None

    def fetch_profile(self, github_url: str) -> Optional[Dict[str, Any]]:
        """Fetch full GitHub profile for a given URL or username."""
        if not REQUESTS_AVAILABLE:
            return None

        username = self.extract_username(github_url)
        if not username:
            logger.warning(f"Could not extract GitHub username from: {github_url}")
            return None

        try:
            # User profile
            user_resp = requests.get(
                f"{self.BASE_URL}/users/{username}",
                headers=self.headers,
                timeout=10
            )
            if user_resp.status_code == 404:
                logger.warning(f"GitHub user not found: {username}")
                return None
            if user_resp.status_code != 200:
                logger.error(f"GitHub API error: {user_resp.status_code}")
                return None

            user_data = user_resp.json()

            # Repositories
            repos_resp = requests.get(
                f"{self.BASE_URL}/users/{username}/repos",
                headers=self.headers,
                params={"per_page": 100, "sort": "updated"},
                timeout=10
            )
            repos = repos_resp.json() if repos_resp.status_code == 200 else []

            return self._process_profile(user_data, repos)

        except requests.exceptions.ConnectionError:
            logger.warning("Cannot reach GitHub API – no internet or rate limited")
            return self._mock_profile(username)
        except Exception as e:
            logger.error(f"GitHub fetch error: {e}")
            return None

    def _process_profile(self, user: Dict, repos: List[Dict]) -> Dict[str, Any]:
        """Process raw GitHub API response into structured profile."""
        # Language analysis
        lang_counts: Dict[str, int] = {}
        total_stars = 0
        for repo in repos:
            if repo.get("language"):
                lang_counts[repo["language"]] = lang_counts.get(repo["language"], 0) + 1
            total_stars += repo.get("stargazers_count", 0)

        top_languages = sorted(lang_counts.keys(), key=lambda x: lang_counts[x], reverse=True)[:5]

        # Compute contribution score (0–100)
        profile = {
            "username": user.get("login"),
            "url": user.get("html_url"),
            "public_repos": user.get("public_repos", 0),
            "followers": user.get("followers", 0),
            "following": user.get("following", 0),
            "stars_total": total_stars,
            "top_languages": top_languages,
            "bio": user.get("bio"),
            "company": user.get("company"),
            "location": user.get("location"),
            "created_at": user.get("created_at"),
            "contribution_score": self._compute_score(user, repos, total_stars),
        }
        return profile

    def _compute_score(self, user: Dict, repos: List[Dict], total_stars: int) -> float:
        """
        Compute a normalized GitHub activity score (0–100).
        Factors: repos, stars, followers, account age, repo diversity.
        """
        score = 0.0

        # Repos (max 25 points)
        score += min(25, user.get("public_repos", 0) * 2)

        # Stars (max 25 points)
        score += min(25, total_stars * 0.5)

        # Followers (max 20 points)
        score += min(20, user.get("followers", 0) * 0.5)

        # Account age (max 15 points)
        created = user.get("created_at", "")
        if created:
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                age_years = (datetime.now(created_dt.tzinfo) - created_dt).days / 365
                score += min(15, age_years * 3)
            except Exception:
                pass

        # Repo diversity – different languages (max 15 points)
        languages = set(r.get("language") for r in repos if r.get("language"))
        score += min(15, len(languages) * 3)

        return round(min(100, score), 2)

    def _mock_profile(self, username: str) -> Dict[str, Any]:
        """Return a mock profile when GitHub is unreachable."""
        return {
            "username": username,
            "url": f"https://github.com/{username}",
            "public_repos": 0,
            "followers": 0,
            "stars_total": 0,
            "top_languages": [],
            "contribution_score": 0.0,
            "bio": None,
            "_mock": True,
        }


github_tool = GitHubTool()
