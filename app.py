import os
import fastapi
from typing import Any


from actions import (
    create_github_repo,
    enable_github_pages,
    write_code,
    push_files,
    get_latest_sha,
    send_evaluation_response,
)

# background api & fix response sender function DONEEEEEEEEEEEEE
# ai to generate/edit [attachments] DONEEEEEEEE
# round 2 NEEDS CHECKING, REPO ALREADY UP
# deployment ad form fillup HOSTING NEEDED


def match_secret(s: str) -> bool:
    return s == os.getenv("secret")


def round1(data: dict[str, Any]):
    files = write_code(
        data["brief"], data.get("checks", []), data.get("attachments", [])
    )
    creation_data = create_github_repo(data["task"])
    push_files(creation_data["full_name"], files)
    pages_data = enable_github_pages(creation_data["full_name"])

    EVAL_REQUEST: dict[str, str] = {
        "email": data["email"],
        "task": data["task"],
        "round": "1",
        "nonce": data["nonce"],
        "repo_url": creation_data["html_url"],
        "commit_sha": get_latest_sha(creation_data["full_name"]),
        "pages_url": pages_data["html_url"],
    }

    print(EVAL_REQUEST)

    send_evaluation_response(data["evaluation_url"], EVAL_REQUEST)


def round2(data: dict[str, Any]):
    files = write_code(
        data["brief"], data.get("checks", []), data.get("attachments", [])
    )
    # FIXED: Use single quotes inside the f-string
    push_files(f"souhardyasengupta05/{data['task']}", files)

    EVAL_REQUEST: dict[str, str] = {
        "email": data["email"],
        "task": data["task"],
        "round": "2",
        "nonce": data["nonce"],
        "repo_url": f"https://github.com/souhardyasengupta05/{data['task']}",
        "commit_sha": get_latest_sha(f"souhardyasengupta05/{data['task']}"),
        "pages_url": f"https://souhardyasengupta05.github.io/{data['task']}/",
    }

    print(EVAL_REQUEST)

    send_evaluation_response(data["evaluation_url"], EVAL_REQUEST)


def function_response(data: dict[str, Any]):
    round = str(data["round"])
    
    match round:
        case "1":
            round1(data)
        case "2":
            round2(data)
        case _:
            pass


app = fastapi.FastAPI()


@app.post("/handle_task")
async def handle_task(data: dict[str, Any], background_tasks: fastapi.BackgroundTasks):
    if not match_secret(data.get("secret", "")):
        return {"error": "Invalid credentials"}

    background_tasks.add_task(function_response, data)
    return {"message": "received"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app=app, host="0.0.0.0", port=8080)