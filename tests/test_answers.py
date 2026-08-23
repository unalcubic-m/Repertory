import pytest

from library.answers import match_answer, normalize_answer
from library.models import AnswerAlias


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  ALLEGRO—Moderato!  ", "allegro moderato"),
        ("L\u2019été", "lété"),
        ("\uff22\uff37\uff36\uff11\uff10\uff14\uff18", "bwv 1048"),
        ("Op. 67, No. 1", "op 67 no 1"),
        ("No III", "no iii"),
    ],
)
def test_normalize_answer_is_deterministic(raw: str, expected: str) -> None:
    assert normalize_answer(raw) == expected


@pytest.mark.django_db
def test_match_answer_accepts_only_canonical_or_explicit_alias(part) -> None:
    AnswerAlias.objects.create(
        owner=part.owner,
        part=part,
        value="Brandenburg 3",
        normalized_value=normalize_answer("Brandenburg 3"),
    )

    assert match_answer(part, "brandenburg 3") == (True, "Brandenburg 3")
    assert match_answer(part, "some Bach concerto") == (False, None)
