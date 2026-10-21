"""Small helpers for putting ranks into sentences, so a sentence cannot claim a rank the data do not have."""

from __future__ import annotations


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def rank_largest(rank: int) -> str:
    """'largest' for rank 1, otherwise '2nd largest', '3rd largest' and so on."""
    return "largest" if rank == 1 else f"{ordinal(rank)} largest"


def largest_phrase(rank: int, n: int) -> str:
    """'the largest gap among 138 economies' or 'the 2nd largest gap among 138 economies'."""
    return f"the {rank_largest(rank)} gap among {n} economies"
