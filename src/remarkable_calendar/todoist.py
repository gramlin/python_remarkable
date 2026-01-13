from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://api.todoist.com/rest/v2"


@dataclass(frozen=True)
class TodoistProject:
    project_id: str
    name: str


@dataclass(frozen=True)
class TodoistTask:
    content: str
    description: str | None
    due: str | None


def _request_json(token: str, path: str, params: dict[str, str] | None = None) -> object:
    url = f"{BASE_URL}/{path.lstrip('/')}"
    if params:
        url = f"{url}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request) as response:
            payload = response.read().decode("utf-8")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8")
        raise RuntimeError(
            f"Todoist-anrop misslyckades ({exc.code} {exc.reason}): {error_body}"
        ) from exc
    return json.loads(payload) if payload else {}


def fetch_projects(token: str) -> list[TodoistProject]:
    data = _request_json(token, "projects")
    return [
        TodoistProject(project_id=item["id"], name=item["name"])
        for item in data
    ]


def fetch_tasks(token: str, project_id: str) -> list[TodoistTask]:
    data = _request_json(token, "tasks", params={"project_id": project_id})
    tasks: list[TodoistTask] = []
    for item in data:
        due = item.get("due") or {}
        due_value = due.get("datetime") or due.get("date") or due.get("string")
        tasks.append(
            TodoistTask(
                content=item.get("content", "(utan titel)"),
                description=item.get("description"),
                due=due_value,
            )
        )
    return tasks
