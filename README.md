# FitFindr

## Project Overview

FitFindr is a multi-tool AI agent for secondhand fashion. The goal of the project is to help a user search a small thrift-style listings dataset, pick a good match, suggest an outfit using that item, and then generate a short social-style fit card caption.

For this project, I used local Ollama with the `llama3.2` model instead of Groq. The interface is built with Gradio, the search data comes from the provided JSON dataset, and the agent logic lives in `agent.py`.

## Tool Inventory

FitFindr uses three required tools in `tools.py`:

1. `search_listings(description: str, size: str | None, max_price: float | None) -> list[dict]`
   This tool loads the dataset with `load_listings()` from `utils/data_loader.py`, filters by price and size, scores listings by keyword overlap, and returns matching listing dictionaries sorted from best match to worst match.

2. `suggest_outfit(new_item: dict, wardrobe: dict) -> str`
   This tool takes the selected listing and the user wardrobe, then calls local Ollama to generate styling advice. If the wardrobe is empty, it still returns general advice instead of failing.

3. `create_fit_card(outfit: str, new_item: dict) -> str`
   This tool takes the outfit suggestion and selected listing, then calls local Ollama again to generate a short caption that sounds like a real outfit post.

## Planning Loop

The agent logic is implemented in `run_agent(query, wardrobe)` inside `agent.py`.

The flow is:

1. The agent creates a session dictionary.
2. It parses the user query to pull out a basic `description`, `size`, and `max_price`.
3. It calls `search_listings(...)` first.
4. If `search_listings` returns `[]`, the agent stops early and does not call `suggest_outfit` or `create_fit_card`.
5. If search succeeds, the agent saves the first result as `session["selected_item"]`.
6. It passes `selected_item` and `wardrobe` into `suggest_outfit(...)`.
7. It saves the returned text as `session["outfit_suggestion"]`.
8. It passes `outfit_suggestion` and `selected_item` into `create_fit_card(...)`.
9. It saves the result as `session["fit_card"]`.
10. It returns the final session dictionary.

This keeps the tool order explicit and makes the early-stop failure branch easy to reason about.

## State Management

The session dictionary is the main state container for one query. It uses these keys:

- `query`: the original user input
- `description`: the parsed description text used for search
- `size`: the parsed size filter, if found
- `max_price`: the parsed budget filter, if found
- `results`: the list returned by `search_listings`
- `selected_item`: the first listing chosen from results
- `wardrobe`: the user wardrobe dictionary
- `outfit_suggestion`: the string returned by `suggest_outfit`
- `fit_card`: the string returned by `create_fit_card`
- `error`: any error message that caused the agent to stop early

This structure made debugging easier because I could inspect the full state after both successful and failed queries.

## Error Handling

I handled errors at each stage instead of assuming every step would work.

- If search returns no matches, the agent sets `session["error"]` to a helpful message and returns early.
- In that case, `selected_item`, `outfit_suggestion`, and `fit_card` stay `None`.
- Example: the query `"designer ballgown size XXS under $5"` returns no listings, sets an error, and `fit_card` stays `None`.
- If the wardrobe is empty, `suggest_outfit` does not crash. It asks Ollama for general styling advice instead.
- If `create_fit_card` gets an empty outfit string, it returns:

```text
I couldn't create a fit card because there was no outfit suggestion to summarize.
```

I also kept the Gradio handler defensive by using `.get()` when reading session values so the app does not crash if a key is missing.

## Testing

I tested the tools both manually and with `pytest`.

Current test result:

```text
7 passed
```

The tests cover:

1. search returns results
2. search empty results returns `[]`
3. search price filter works
4. `suggest_outfit` works with the example wardrobe
5. `suggest_outfit` works with the empty wardrobe
6. `create_fit_card` returns the correct error message for empty outfit input
7. `create_fit_card` returns a non-empty caption for a valid outfit

I also manually tested the agent success branch and no-results branch through `agent.py` and the Gradio app.

## Spec Reflection

I think the final project matches the Milestone 3 and Milestone 4 requirements closely.

- The project uses the required three-tool structure.
- `search_listings` is deterministic and easy to test.
- The planning loop calls the tools in the correct order.
- The early-stop no-results branch is implemented correctly.
- Session state is explicit instead of hidden in temporary variables.

One tradeoff is that the query parsing in `agent.py` is intentionally simple. It handles cases like `under $30`, `below 30`, and size words like `M` or `XXL`, but it is not a full natural language parser. I kept it simple because that matched the project scope and made the code easier to read and debug.

Another tradeoff is that the search scoring is lightweight keyword overlap, not semantic search. That means it is predictable and easy to explain, but it can miss more subtle matches.

## AI Usage

I used Codex as a coding assistant during implementation.

1. I used Codex to review my `tools.py` from my `planning.md` tool specs, then tested each function manually and with `pytest`.
2. I used Codex to review my `agent.py` using my Planning Loop, State Management, and Architecture sections, then verified the success and failure branches.

I still checked the code and behavior myself after each step, especially the early-stop logic and the session state fields.

## How to Run

1. Make sure Ollama is running locally and that the `llama3.2` model is available.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python app.py
```

4. Open the local Gradio URL shown in the terminal.

Example query to test a successful run:

```text
vintage graphic tee under $30
```

Example query to test the no-results branch:

```text
designer ballgown size XXS under $5
```
