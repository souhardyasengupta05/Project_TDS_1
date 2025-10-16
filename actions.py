import os
import requests
import base64
import time
from typing import Final

from llm import Attachments, File, agent, handle_attachments

HEADERS = {
    "Authorization": f"Bearer {os.getenv("GITHUB_TOKEN")}",
    "Accept": "application/vnd.github+json",
}


def write_code(
    brief: str, checks: list[str], attachments: list[Attachments]
) -> list[File]:
    prompt = f"""
        TASK:
        {brief}

        CHECKS:
        {"\n".join(list(map(lambda x: f"- {x}", checks)))}

        REQUIREMENTS:
        1. CRITICAL: The output must contain a README. The README should contain FEATURES, DOCUMENTATION, HOW TO USE and PROJECT STRUCTURE.
        2. CRITICAL: The output must contain an index.html page in the root directory. This is what Github pages will deploy.
        3. Use the attachments for data. If it is missing, handle it with mock data if external apis cannot be used/web scraped data cannot be found.
        4. Do NOT use any triple backticks (```) or markdown formatting.
        5. Return only valid code inside the files. No natural language should be used.
    """
    result = agent.run_sync([prompt] + handle_attachments(attachments))
    return result.output


def create_github_repo(name: str):
    PAYLOAD: Final = {  # pyright: ignore[reportUnknownVariableType]
        "name": name,
        "private": False,
        "auto_init": True,
        "license_template": "mit",
    }

    response = requests.post(
        "https://api.github.com/user/repos",
        headers=HEADERS,
        json=PAYLOAD,  # pyright: ignore[reportUnknownArgumentType]
    )

    if response.status_code != 201:
        raise Exception(f"Failed to create repo: {response.text}")
    else:
        return response.json()


def push_files(full_name: str, files: list[File]):
    for file in files:
        response = requests.get(
            f"https://api.github.com/repos/{full_name}/contents/{file.path}",
            headers=HEADERS,
        )

        PAYLOAD = {  # pyright: ignore[reportUnknownVariableType]
            "message": f"Modify {file.path} - Round {round}",
            "content": base64.b64encode(file.content.encode()).decode(),
        }

        latest_sha = response.json()["sha"] if response.status_code == 200 else None

        if latest_sha:
            PAYLOAD["sha"] = latest_sha

        response = requests.put(
            f"https://api.github.com/repos/{full_name}/contents/{file.path}",
            headers=HEADERS,
            json=PAYLOAD,  # pyright: ignore[reportUnknownArgumentType]
        )

        if response.status_code not in (201, 200):
            raise Exception(f"Failed to push file {file.path}: {response.text}")


def enable_github_pages(full_name: str):
    PAYLOAD: Final = {  # pyright: ignore[reportUnknownVariableType]
        "source": {"branch": "main", "path": "/"},
    }

    response = requests.post(
        f"https://api.github.com/repos/{full_name}/pages",
        headers=HEADERS,
        json=PAYLOAD,  # pyright: ignore[reportUnknownArgumentType]
    )

    if response.status_code != 201:
        raise Exception(f"Failed to create pages: {response.text}")
    else:
        return response.json()


def get_latest_sha(full_name: str, branch: str = "main") -> str:
    response = requests.get(
        f"https://api.github.com/repos/{full_name}/commits/{branch}",
        headers=HEADERS,
    )

    if response.status_code != 200:
        raise Exception(f"Failed to get latest SHA: {response.text}")
    else:
        data = response.json()
        return data["sha"]


def send_evaluation_response(evaluation_url: str, response_json: dict[str, str]):
    LOCAL_HEADERS = {"Content-Type": "application/json"}
    delay = 1

    for attempt in range(100):
        try:
            resp = requests.post(
                evaluation_url, json=response_json, headers=LOCAL_HEADERS, timeout=10
            )

            if resp.status_code == 200:
                print(f"✅ Success on attempt {attempt + 1}: HTTP 200")
                return
            else:
                print(f"⚠️ Attempt {attempt + 1} ({delay}): HTTP {resp.status_code}")
        except requests.RequestException as e:
            print(f"❌ Error on attempt {attempt + 1}: {e}, retrying in {delay}s...")

        time.sleep(delay)
        delay *= 2
