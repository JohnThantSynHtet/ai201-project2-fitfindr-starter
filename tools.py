"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price) -> list[dict]
    suggest_outfit(new_item, wardrobe) -> str
    create_fit_card(outfit, new_item) -> str
"""

import re

import requests

from utils.data_loader import load_listings

OLLAMA_MODEL = "llama3.2"


def _call_ollama(prompt: str, temperature: float = 0.7) -> str:
    """Call the local Ollama API and return the generated text."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        return f"Could not reach local Ollama: {exc}"
    except ValueError:
        return "Ollama returned an invalid response."

    text = data.get("response", "").strip()
    if not text:
        return "Ollama returned an empty response."
    return text


def _tokenize(text: str) -> list[str]:
    """Split text into lowercase word tokens."""
    return re.findall(r"\w+", text.lower())


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches - does NOT raise an exception.
    """
    listings = load_listings()
    keywords = _tokenize(description)
    requested_size = size.lower() if size else None
    scored_results: list[tuple[int, dict]] = []

    for listing in listings:
        if max_price is not None and listing.get("price", 0) > max_price:
            continue

        if requested_size is not None:
            size_tokens = _tokenize(str(listing.get("size", "")))
            if requested_size not in size_tokens:
                continue

        searchable_text = " ".join(
            [
                str(listing.get("title", "")),
                str(listing.get("description", "")),
                str(listing.get("category", "")),
                " ".join(listing.get("style_tags", [])),
            ]
        ).lower()

        score = sum(1 for keyword in keywords if keyword in searchable_text)
        if score > 0:
            scored_results.append((score, listing))

    scored_results.sort(key=lambda item: item[0], reverse=True)
    return [listing for score, listing in scored_results]


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1-2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty - handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.
    """
    if not isinstance(new_item, dict) or not new_item.get("title"):
        return "Invalid item: please provide a valid listing dictionary."

    wardrobe_items = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []
    item_summary = "\n".join(
        [
            f"Title: {new_item.get('title', 'Unknown item')}",
            f"Category: {new_item.get('category', 'Unknown category')}",
            f"Description: {new_item.get('description', 'No description provided.')}",
            f"Colors: {', '.join(new_item.get('colors', [])) or 'Unknown'}",
            f"Style tags: {', '.join(new_item.get('style_tags', [])) or 'None'}",
        ]
    )

    if not wardrobe_items:
        prompt = f"""
You are a helpful styling assistant for a student fashion app.

No wardrobe items were provided.

New item:
{item_summary}

Give concise styling advice in 4 to 6 sentences. Suggest common pairings,
colors that work well, shoe ideas, and the overall vibe this piece fits.
Keep the response practical and easy to understand.
""".strip()
    else:
        wardrobe_lines = []
        for item in wardrobe_items:
            name = item.get("name", "Unnamed item")
            category = item.get("category", "unknown category")
            colors = ", ".join(item.get("colors", [])) or "unknown colors"
            wardrobe_lines.append(f"- {name} ({category}; colors: {colors})")

        prompt = f"""
You are a helpful styling assistant for a student fashion app.

New item:
{item_summary}

Wardrobe items:
{chr(10).join(wardrobe_lines)}

Suggest 1 to 2 complete outfits in about 4 to 6 sentences total. Use the new
item and mention specific wardrobe pieces by name. Include shoes or accessories
when they help, and keep the response concise and useful.
""".strip()

    result = _call_ollama(prompt, temperature=0.7).strip()
    if not result:
        return "I couldn't generate an outfit suggestion right now."
    return result


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2-4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string - do NOT raise an exception.
    """
    if not outfit or not outfit.strip():
        return (
            "I couldn't create a fit card because there was no outfit "
            "suggestion to summarize."
        )

    item_title = new_item.get("title", "this thrifted piece") if isinstance(new_item, dict) else "this thrifted piece"
    item_price = new_item.get("price", "unknown price") if isinstance(new_item, dict) else "unknown price"
    item_platform = new_item.get("platform", "unknown platform") if isinstance(new_item, dict) else "unknown platform"

    prompt = f"""
You are writing a casual outfit post caption for a student fashion app.

Item title: {item_title}
Price: {item_price}
Platform: {item_platform}

Outfit idea:
{outfit}

Write a short caption in 2 to 4 sentences. Mention the item title, price, and
platform naturally once each. Keep it casual, authentic, and specific, like a
real outfit post instead of a product listing.
""".strip()

    result = _call_ollama(prompt, temperature=0.9).strip()
    if not result:
        return "I couldn't create a fit card right now."
    return result
