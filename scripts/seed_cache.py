import asyncio

from overbuild.search.ecosystems import search_ecosystems
from overbuild.search.github_search import search_github
from overbuild.search.librariesio import search_librariesio
from overbuild.search.npm_registry import search_npm
from overbuild.search.stackoverflow import search_stackoverflow

QUERIES = [
    ("rate limiter fastapi", "python"),
    ("rust cleanup target folders", "rust"),
    ("markdown to html python", "python"),
]


async def main() -> None:
    for query, language in QUERIES:
        print(f"Seeding cache for: {query} ({language})")
        await asyncio.gather(
            search_librariesio(query, language),
            search_github(query, language),
            search_stackoverflow(query, language),
            search_ecosystems(query, language),
            search_npm(query, language),
            return_exceptions=True,
        )


if __name__ == "__main__":
    asyncio.run(main())
