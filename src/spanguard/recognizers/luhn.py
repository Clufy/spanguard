"""Luhn checksum for candidate credit-card numbers."""

from __future__ import annotations


def luhn_valid(digits: str) -> bool:
    """True iff `digits` (bare digits, no separators) passes the Luhn check."""
    if not digits or not digits.isdigit():
        return False
    total = 0
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        d = ord(ch) - 48
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0
