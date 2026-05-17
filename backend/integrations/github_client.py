import httpx

from config import settings


class GitHubClient:
    base_url = "https://api.github.com"

    def is_configured(self) -> bool:
        return bool(settings.github_token)

    def headers(self) -> dict:
        if not self.is_configured():
            raise RuntimeError("GITHUB_TOKEN is missing.")
        return {
            "Authorization": f"Bearer {settings.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def list_issues(self, repo: str, state: str = "open", limit: int = 10) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/repos/{repo}/issues",
                headers=self.headers(),
                params={"state": state, "per_page": max(1, min(limit, 30))},
            )
            response.raise_for_status()
            issues = response.json()
            return [
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "state": issue["state"],
                    "url": issue["html_url"],
                    "created_at": issue["created_at"],
                    "updated_at": issue["updated_at"],
                    "body": issue.get("body") or "",
                }
                for issue in issues
                if "pull_request" not in issue
            ]

    async def get_issue(self, repo: str, issue_number: int) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/repos/{repo}/issues/{issue_number}",
                headers=self.headers(),
            )
            response.raise_for_status()
            issue = response.json()
            return {
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "url": issue["html_url"],
                "body": issue.get("body") or "",
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
            }

    async def create_issue(self, repo: str, title: str, body: str = "") -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/repos/{repo}/issues",
                headers=self.headers(),
                json={"title": title, "body": body},
            )
            response.raise_for_status()
            issue = response.json()
            return {"number": issue["number"], "title": issue["title"], "url": issue["html_url"]}


github_client = GitHubClient()
