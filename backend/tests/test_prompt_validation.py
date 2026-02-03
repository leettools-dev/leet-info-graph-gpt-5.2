import pytest
from pydantic import ValidationError

from app.schemas.sessions import ResearchSessionCreate


def test_prompt_rejects_empty_string():
    with pytest.raises(ValidationError):
        ResearchSessionCreate(prompt="")


def test_prompt_rejects_whitespace_only():
    with pytest.raises(ValidationError):
        ResearchSessionCreate(prompt="   \n\t ")


@pytest.mark.parametrize("prompt", ["a", "ok"])
def test_prompt_rejects_too_short(prompt: str):
    with pytest.raises(ValidationError):
        ResearchSessionCreate(prompt=prompt)


def test_prompt_rejects_too_long():
    with pytest.raises(ValidationError):
        ResearchSessionCreate(prompt="x" * 4001)


def test_prompt_accepts_natural_language():
    payload = ResearchSessionCreate(prompt="Summarize current EV market trends")
    assert payload.prompt.startswith("Summarize")
