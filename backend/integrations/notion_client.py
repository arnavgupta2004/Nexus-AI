import httpx

from config import settings


class NotionClient:
    base_url = "https://api.notion.com/v1"
    notion_version = "2022-06-28"

    def is_configured(self) -> bool:
        return bool(settings.notion_api_key)

    def headers(self) -> dict:
        if not self.is_configured():
            raise RuntimeError("NOTION_API_KEY is missing.")
        return {
            "Authorization": f"Bearer {settings.notion_api_key}",
            "Notion-Version": self.notion_version,
            "Content-Type": "application/json",
        }

    def default_parent(self) -> dict:
        if settings.notion_database_id:
            return {"database_id": settings.notion_database_id}
        if settings.notion_parent_page_id:
            return {"page_id": settings.notion_parent_page_id}
        raise RuntimeError("Set NOTION_DATABASE_ID or NOTION_PARENT_PAGE_ID before creating Notion pages.")

    async def search(self, query: str = "", limit: int = 10) -> dict:
        payload = {"page_size": max(1, min(limit, 25))}
        if query:
            payload["query"] = query
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/search",
                headers=self.headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "results": [
                    {
                        "id": item["id"],
                        "object": item["object"],
                        "url": item.get("url"),
                    }
                    for item in data.get("results", [])
                ]
            }

    async def create_page(self, title: str, content: str = "", parent_id: str | None = None) -> dict:
        parent = (
            {"page_id": parent_id}
            if parent_id
            else self.default_parent()
        )

        payload = {
            "parent": parent,
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": content or ""},
                            }
                        ]
                    },
                }
            ],
        }

        if "database_id" in parent:
            payload["properties"] = {
                "Name": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": title},
                        }
                    ]
                }
            }
        else:
            payload["properties"] = {
                "title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": title},
                        }
                    ]
                }
            }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/pages",
                headers=self.headers(),
                json=payload,
            )
            response.raise_for_status()
            page = response.json()
            return {"id": page["id"], "url": page.get("url")}


notion_client = NotionClient()
