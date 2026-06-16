from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.data_loader import get_empty_wardrobe, get_example_wardrobe, load_listings
from tools import create_fit_card, search_listings, suggest_outfit


def test_search_returns_results():
    results = search_listings("butterfly baby tee")

    assert results
    assert results[0]["id"] == "lst_002"


def test_search_empty_results_returns_empty_list():
    results = search_listings("neon astronaut kimono")

    assert results == []


def test_search_price_filter_works():
    results = search_listings("platform", max_price=50)

    assert results
    assert all(item["price"] <= 50 for item in results)
    assert not any(item["id"] == "lst_009" for item in results)


def test_suggest_outfit_works_with_example_wardrobe(monkeypatch):
    captured = {}

    def fake_call(prompt: str, temperature: float = 0.7) -> str:
        captured["prompt"] = prompt
        captured["temperature"] = temperature
        return "Wear it with the baggy straight-leg jeans, the white ribbed tank top, and the chunky white sneakers for an easy everyday look."

    monkeypatch.setattr("tools._call_ollama", fake_call)

    result = suggest_outfit(load_listings()[0], get_example_wardrobe())

    assert result
    assert "Baggy straight-leg jeans" in captured["prompt"]
    assert captured["temperature"] == 0.7


def test_suggest_outfit_works_with_empty_wardrobe(monkeypatch):
    captured = {}

    def fake_call(prompt: str, temperature: float = 0.7) -> str:
        captured["prompt"] = prompt
        return "Try it with a fitted tank, clean sneakers, and simple layers for a relaxed vintage vibe."

    monkeypatch.setattr("tools._call_ollama", fake_call)

    result = suggest_outfit(load_listings()[0], get_empty_wardrobe())

    assert result
    assert "No wardrobe items were provided." in captured["prompt"]


def test_create_fit_card_returns_error_message_for_empty_outfit():
    result = create_fit_card("   ", load_listings()[0])

    assert (
        result
        == "I couldn't create a fit card because there was no outfit suggestion to summarize."
    )


def test_create_fit_card_returns_non_empty_caption_for_valid_outfit(monkeypatch):
    captured = {}

    def fake_call(prompt: str, temperature: float = 0.7) -> str:
        captured["prompt"] = prompt
        captured["temperature"] = temperature
        return "Thrifted the Vintage Levi's 501 Jeans for $38.0 on depop and built the easiest off-duty look around them. The whole outfit feels casual, broken-in, and actually wearable."

    monkeypatch.setattr("tools._call_ollama", fake_call)

    result = create_fit_card(
        "Wear it with a white tank and chunky sneakers for a casual vintage look.",
        load_listings()[0],
    )

    assert result
    assert "Vintage Levi's 501 Jeans" in captured["prompt"]
    assert "depop" in captured["prompt"]
    assert captured["temperature"] == 0.9
