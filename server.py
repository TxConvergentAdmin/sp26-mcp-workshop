import json
from typing import Any

from fastmcp import FastMCP
from course_store import store

# Solution file 


mcp = FastMCP("UT Course Explorer MCP")


@mcp.tool
def search_courses(
    department: str | None = None,
    keyword: str | None = None,
    status: str | None = None,
    instruction_mode: str | None = None,
    course_level: int | None = None,
    days: str | None = None,
    limit: int | None = 10,
    return_all: bool = False,
) -> list[dict[str, Any]]:
    """Search UT courses with simple structured filters."""
    return store.search_courses(
        department=department,
        keyword=keyword,
        status=status,
        instruction_mode=instruction_mode,
        course_level=course_level,
        days=days,
        limit=limit,
        return_all=return_all,
    )


@mcp.tool
def get_course_details(unique_id: int) -> dict[str, Any]:
    """Return the normalized course record for a single uniqueId."""
    return store.get_course_details(unique_id)


@mcp.resource("resource://dataset-info")
def dataset_info() -> str:
    return json.dumps(store.dataset_info(), indent=2)


@mcp.resource("resource://departments")
def departments() -> str:
    return json.dumps(store.departments, indent=2)


if __name__ == "__main__":
    mcp.run()
