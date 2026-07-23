"""
generate_and_place_images.

M2: swapped Gemini (paid) -> Pollinations.ai (free, no API key) for image
generation. Pollinations serves images over a simple GET request:
https://image.pollinations.ai/prompt/{url-encoded prompt}
"""
import re
import time
import urllib.parse
from pathlib import Path

import requests

from state import State

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"


def _pollinations_generate_image_bytes(prompt: str, size: str = "1024x1024") -> bytes:
    """
    size is an ImageSpec-style string like "1024x1024" or "1024x1536".
    nologo=true strips the Pollinations watermark. A random seed is used
    so re-running with the same prompt after a failed write doesn't
    silently reuse a cached identical image.
    """
    try:
        width, height = (int(x) for x in size.split("x"))
    except (ValueError, AttributeError):
        width, height = 1024, 1024

    encoded_prompt = urllib.parse.quote(prompt.strip())
    url = f"{POLLINATIONS_BASE}/{encoded_prompt}"
    params = {
        "width": width,
        "height": height,
        "nologo": "true",
        "seed": int(time.time()),
    }

    resp = requests.get(url, params=params, timeout=60)
    resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")
    if "image" not in content_type:
        raise RuntimeError(
            f"Pollinations did not return an image (content-type={content_type!r})."
        )

    return resp.content


def _safe_slug(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "blog"


def generate_and_place_images(state: State) -> dict:
    plan = state["plan"]
    assert plan is not None

    md = state.get("md_with_placeholders") or state["merged_md"]
    image_specs = state.get("image_specs", []) or []

    if not image_specs:
        filename = f"{_safe_slug(plan.blog_title)}.md"
        Path(filename).write_text(md, encoding="utf-8")
        return {"final": md}

    images_dir = Path("images")
    images_dir.mkdir(exist_ok=True)

    for spec in image_specs:
        placeholder = spec["placeholder"]
        filename = spec["filename"]
        out_path = images_dir / filename

        if not out_path.exists():
            try:
                img_bytes = _pollinations_generate_image_bytes(
                    spec["prompt"], spec.get("size", "1024x1024")
                )
                out_path.write_bytes(img_bytes)
            except Exception as e:
                prompt_block = (
                    f"> **[IMAGE GENERATION FAILED]** {spec.get('caption','')}\n>\n"
                    f"> **Alt:** {spec.get('alt','')}\n>\n"
                    f"> **Prompt:** {spec.get('prompt','')}\n>\n"
                    f"> **Error:** {e}\n"
                )
                md = md.replace(placeholder, prompt_block)
                continue

        img_md = f"![{spec['alt']}](images/{filename})\n*{spec['caption']}*"
        md = md.replace(placeholder, img_md)

    filename = f"{_safe_slug(plan.blog_title)}.md"
    Path(filename).write_text(md, encoding="utf-8")
    return {"final": md}
