
"""Computational helpers."""


def perc(current: int, total: int) -> float:
    """Calculate percentage.

    If total is 0, returns 0%.
    """
    if total <= 0:
        return 0.

    return current * 100 / total
