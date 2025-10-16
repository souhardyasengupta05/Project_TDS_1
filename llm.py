from pydantic_ai import (
    Agent,
    UserContent,
    ImageUrl,
    DocumentUrl,
)
from pydantic import BaseModel, Field
from typing import TypedDict
import os


class File(BaseModel):
    path: str = Field(
        alias="name of file",
        description="The name of the file. Put everything at the root.",
    )
    content: str


class Attachments(TypedDict):
    name: str
    url: str


SYSTEMS = """
    You are a code-generator that generates readable and clear html, css and js files.
    You will output ONLY valid html, css and js files with no explanation, no markdown formatting and no backticks.
    The code must be ready to be used by Github Pages to deploy as-is.
    IMPORTANT: Be sure to pass all the checks provided, if any.
    CRITICAL: The output MUST contain a README.md file that documents the generated code.
    """

agent = Agent(
    "openai:gpt-5-nano", output_type=list[File], retries=3, system_prompt=SYSTEMS
)  # type: ignore


def handle_attachments(attachments: list[Attachments]) -> list[UserContent]:
    return list(
        map(
            lambda file: (
                ImageUrl(url=file["url"])
                if is_image(file["name"])
                else DocumentUrl(url=file["url"])
            ),
            attachments,
        )
    )


def is_image(filename: str) -> bool:
    image_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".webp",
        ".svg",
    }
    _, extension = os.path.splitext(filename)
    return extension.lower() in image_extensions
