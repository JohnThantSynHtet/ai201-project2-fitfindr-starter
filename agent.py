"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import re

from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,
        "description": query,
        "size": None,
        "max_price": None,
        "results": [],
        "selected_item": None,
        "wardrobe": wardrobe if isinstance(wardrobe, dict) else get_example_wardrobe(),
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


def _parse_query(query: str) -> dict:
    """Extract simple search values from a user query."""
    max_price = None
    size = None

    price_patterns = [
        r"under\s*\$?\s*(\d+(?:\.\d+)?)",
        r"below\s*\$?\s*(\d+(?:\.\d+)?)",
        r"\$\s*(\d+(?:\.\d+)?)",
    ]
    for pattern in price_patterns:
        match = re.search(pattern, query, flags=re.IGNORECASE)
        if match:
            max_price = float(match.group(1))
            break

    size_match = re.search(
        r"\bsize\s+((?:XXS|XS|S|M|L|XL|XXL))\b|\b(XXS|XS|S|M|L|XL|XXL)\b",
        query,
        flags=re.IGNORECASE,
    )
    if size_match:
        size = (size_match.group(1) or size_match.group(2)).upper()

    description = query
    description = re.sub(r"under\s*\$?\s*\d+(?:\.\d+)?", " ", description, flags=re.IGNORECASE)
    description = re.sub(r"below\s*\$?\s*\d+(?:\.\d+)?", " ", description, flags=re.IGNORECASE)
    description = re.sub(r"\$\s*\d+(?:\.\d+)?", " ", description)
    description = re.sub(
        r"\bsize\s+(?:XXS|XS|S|M|L|XL|XXL)\b",
        " ",
        description,
        flags=re.IGNORECASE,
    )
    description = re.sub(r"\b(XXS|XS|S|M|L|XL|XXL)\b", " ", description, flags=re.IGNORECASE)
    description = " ".join(description.split()).strip(" ,.-")

    if not description:
        description = query

    return {
        "description": description,
        "size": size,
        "max_price": max_price,
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    session = _new_session(query, wardrobe)
    parsed = _parse_query(query)
    session["description"] = parsed["description"]
    session["size"] = parsed["size"]
    session["max_price"] = parsed["max_price"]

    session["results"] = search_listings(
        description=session["description"],
        size=session["size"],
        max_price=session["max_price"],
    )

    if not session["results"]:
        session["error"] = (
            "I couldn't find listings that matched your search. Try a broader "
            "description, higher budget, or fewer filters."
        )
        session["selected_item"] = None
        session["outfit_suggestion"] = None
        session["fit_card"] = None
        return session

    session["selected_item"] = session["results"][0]
    session["outfit_suggestion"] = suggest_outfit(
        session["selected_item"],
        session["wardrobe"],
    )

    if not session["outfit_suggestion"] or not session["outfit_suggestion"].strip():
        session["error"] = (
            "I found a listing, but I couldn't generate an outfit suggestion "
            "right now."
        )
        return session

    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"],
        session["selected_item"],
    )

    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Successful Query ===")
    success_session = run_agent(
        query="looking for a vintage graphic tee under $30 size M",
        wardrobe=get_example_wardrobe(),
    )
    print(success_session)

    print("\n=== Impossible Query ===")
    no_results_session = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(no_results_session)
