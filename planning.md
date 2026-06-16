# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
Searches the mock secondhand listings dataset for clothing items that match the user's requested description, size, and maximum price.

**Input parameters:**
- `description` (str): The item or style the user is searching for, such as `"vintage graphic tee"`.
- `size` (str | None): The requested clothing size, such as `"M"`. If the user does not give a size, this is `None`.
- `max_price` (float | None): The highest price the user wants to pay. If the user does not give a budget, this is `None`.

**What it returns:**
A list of listing dictionaries. Each result can contain fields like `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

**What happens if it fails or returns nothing:**
If no listings match, the tool returns an empty list `[]`. The agent should stop early, explain that no matching listings were found, and suggest trying a broader description, higher budget, or removing the size filter.

---

### Tool 2: suggest_outfit

**What it does:**
Suggests a complete outfit using the selected thrift item and the user's wardrobe.

**Input parameters:**
- `new_item` (dict): The selected listing from `search_listings`.
- `wardrobe` (dict): The user's wardrobe data, including an `items` list of clothing pieces the user already owns.

**What it returns:**
A string with one or more outfit suggestions. The suggestion should explain what to pair with the new item and include styling details like fit, shoes, colors, or layering.

**What happens if it fails or returns nothing:**
If the wardrobe is empty or too small, the tool should still return a useful general outfit suggestion based on the new item. It should not crash or return an empty string.

---

### Tool 3: create_fit_card

**What it does:**
Creates a short, shareable outfit caption based on the selected thrift item and the outfit suggestion.

**Input parameters:**
- `outfit` (str): The outfit suggestion created by `suggest_outfit`.
- `new_item` (dict): The selected thrift listing used in the outfit.

**What it returns:**
A short caption-style string that sounds like something a user could post online. It should mention the item and the overall outfit vibe.

**What happens if it fails or returns nothing:**
If the outfit string is empty or missing, the tool should return a clear error message string instead of crashing. Example: `"I couldn't create a fit card because there was no outfit suggestion to summarize."`

---

### Additional Tools (if any)

No additional tools for the required version. If I add a stretch feature later, I will document it here before implementing it.

---

## Planning Loop

**How does your agent decide which tool to call next?**

The agent decides what to do next by checking the result of each tool before moving forward.

First, the agent reads the user's query and extracts the item description, size if provided, max price if provided, and any wardrobe or style details. Then it calls `search_listings(description, size, max_price)`.

After search runs, the agent checks the results. If the results list is empty, the agent stores an error message in `session["error"]`, leaves `session["selected_item"]`, `session["outfit_suggestion"]`, and `session["fit_card"]` as `None`, and returns early. It does not call `suggest_outfit` or `create_fit_card`.

If search returns results, the agent selects the first result and stores it in `session["selected_item"]`. Then it calls `suggest_outfit(session["selected_item"], wardrobe)`.

After the outfit suggestion is created, the agent stores it in `session["outfit_suggestion"]`. If the outfit suggestion is empty, the agent stores an error message in `session["error"]` and returns early.

If the outfit suggestion is valid, the agent calls `create_fit_card(session["outfit_suggestion"], session["selected_item"])`. The fit card is stored in `session["fit_card"]`. The agent is done when it returns the final session containing the selected item, outfit suggestion, fit card, and any error message.

---

## State Management

**How does information from one tool get passed to the next?**

The agent stores information in a session dictionary so each tool can use the output from the previous tool.

The session tracks:
- `query`: the original user request
- `results`: the listings returned by `search_listings`
- `selected_item`: the first matching listing chosen from the results
- `wardrobe`: the wardrobe data used by `suggest_outfit`
- `outfit_suggestion`: the outfit text returned by `suggest_outfit`
- `fit_card`: the caption returned by `create_fit_card`
- `error`: an error message if a tool fails or returns unusable data

The main state flow is:

1. `search_listings` returns a list of matching items.
2. The agent saves the first item as `session["selected_item"]`.
3. `session["selected_item"]` is passed into `suggest_outfit`.
4. The outfit suggestion is saved as `session["outfit_suggestion"]`.
5. `session["outfit_suggestion"]` and `session["selected_item"]` are passed into `create_fit_card`.
6. The final caption is saved as `session["fit_card"]`.

This means the user does not need to re-enter the item between steps. The agent carries the selected item and outfit suggestion forward inside the session.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Store a message in `session["error"]` saying no listings were found. Stop the workflow early and suggest using a broader description, higher budget, or fewer filters. |
| suggest_outfit | Wardrobe is empty | Return a general styling suggestion based on the selected item instead of crashing. The agent still saves this as `session["outfit_suggestion"]` and continues to `create_fit_card`. |
| create_fit_card | Outfit input is missing or incomplete | Return a clear error message string explaining that a fit card cannot be created without an outfit suggestion. The agent saves the message instead of crashing. |

---

## Architecture

```mermaid
flowchart TD
    A[User query] --> B[Planning Loop]

    B --> C[Extract description, size, and max_price]
    C --> D[search_listings(description, size, max_price)]

    D --> E{Were listings found?}

    E -->|No| F[Save message in session error]
    F --> G[Return early to user]

    E -->|Yes| H[Save first result as session selected_item]
    H --> I[suggest_outfit(selected_item, wardrobe)]

    I --> J{Was outfit suggestion created?}

    J -->|No| K[Save outfit error in session error]
    K --> G

    J -->|Yes| L[Save suggestion as session outfit_suggestion]
    L --> M[create_fit_card(outfit_suggestion, selected_item)]

    M --> N[Save caption as session fit_card]
    N --> O[Return selected item, outfit suggestion, and fit card to user]
```

---

## AI Tool Plan

**Milestone 3 — Individual tool implementations:**

I will use Codex to help implement each tool one at a time in `tools.py`. For `search_listings`, I will give Codex the Tool 1 spec from this planning document and ask it to use `load_listings()` from `utils/data_loader.py` instead of rewriting the JSON loading logic. I will verify the output by checking that it filters by description, size, and max price, and that it returns an empty list when no listings match.

For `suggest_outfit`, I will give Codex the Tool 2 spec and ask it to use local Ollama instead of Groq. I will verify that it accepts `new_item` and `wardrobe`, handles an empty wardrobe, and returns a useful string instead of crashing.

For `create_fit_card`, I will give Codex the Tool 3 spec and ask it to use local Ollama to generate a short caption from the outfit suggestion and selected item. I will verify that it handles an empty outfit string with a clear error message and that different inputs produce different captions.

I will also use Codex to help create `tests/test_tools.py`. I will check that the tests cover normal search results, empty search results, price filtering, empty wardrobe handling, and missing outfit input.

**Milestone 4 — Planning loop and state management:**

I will use Codex to help implement `run_agent()` in `agent.py`. I will give Codex the Planning Loop section, State Management section, and Architecture diagram from this planning document. I expect it to produce code that calls `search_listings` first, branches early if no results are found, stores the selected item in the session, passes that item into `suggest_outfit`, stores the outfit suggestion, and then passes both the outfit and item into `create_fit_card`.

Before trusting the generated code, I will verify that it does not call all three tools blindly. I will test one successful query and one impossible query. For the impossible query, I will confirm that `session["error"]` is set and `session["fit_card"]` stays `None`.

I will also use Codex to help implement `handle_query()` in `app.py`. I will verify that the Gradio output panels display the selected listing, outfit suggestion, and fit card from the session dictionary.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish, tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
The agent reads the user query and identifies the search information:
- description: "vintage graphic tee"
- size: None, because the user did not give a size
- max_price: 30.0

The agent calls:

`search_listings(description="vintage graphic tee", size=None, max_price=30.0)`

This tool searches the listings dataset for items that match the description and are priced at or below $30.

**Step 2:**
If `search_listings` returns an empty list, the agent stops early and tells the user that no matching listings were found. It suggests trying a higher budget, a different description, or removing some filters.

If results are found, the agent saves the first result in session state:

`session["selected_item"] = results[0]`

Example selected item:

`"Faded Band Tee" from Depop for $22`

Then the agent calls:

`suggest_outfit(new_item=session["selected_item"], wardrobe=example_wardrobe)`

This tool uses the selected item and the user's wardrobe to suggest a complete outfit.

**Step 3:**
The outfit suggestion is saved in session state:

`session["outfit_suggestion"] = outfit_suggestion`

Example outfit suggestion:

`Pair the faded band tee with baggy jeans and chunky sneakers for a relaxed 90s-inspired outfit. Add a simple jacket if the user wants more layering.`

Then the agent calls:

`create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])`

This tool creates a short, shareable outfit caption based on the selected thrift item and the outfit suggestion.

**Final output to user:**
Selected listing: Faded Band Tee, $22 on Depop, good condition.

Outfit suggestion: Pair it with baggy jeans and chunky sneakers for a relaxed 90s-inspired thrift look. Add a simple jacket if you want more shape and layering.

Fit card: Thrifted this faded band tee for $22 and styled it with baggy denim and chunky sneakers. Easy 90s energy without trying too hard.
