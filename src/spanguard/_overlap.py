"""Deterministic overlap resolution: longest-wins, priority tiebreak."""

from __future__ import annotations

from spanguard.result import Span

PRIORITY: dict[str, int] = {
    "SSN": 0,
    "CREDIT_CARD": 0,
    "API_KEY": 0,
    "EMAIL": 1,
    "PHONE": 1,
    "MRN": 1,
    "DOB": 1,
    "PERSON": 2,
    "LOCATION": 2,
}
_DEFAULT_PRIORITY = 3


def _rank(span: Span) -> tuple[int, int, int]:
    """Sort key for 'best' span: longer first, then higher priority, then earlier."""
    return (-span.length, PRIORITY.get(span.type, _DEFAULT_PRIORITY), span.start)


def resolve_overlaps(spans: list[Span]) -> list[Span]:
    """Greedily keep the best span in each overlapping region.

    Best = longest; ties broken by priority (lower rank wins), then start.
    Returns the surviving spans sorted by start.

    Groups overlapping spans into connected regions and keeps only the best
    span in each region.
    """
    if not spans:
        return []

    # Build overlap graph: spans[i] overlaps with spans[j]?
    n = len(spans)
    overlaps = [[False] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            if spans[i].start < spans[j].end and spans[j].start < spans[i].end:
                overlaps[i][j] = overlaps[j][i] = True

    # Find connected components (overlapping regions) via DFS
    visited = [False] * n
    components: list[list[int]] = []

    def dfs(i: int, component: list[int]) -> None:
        visited[i] = True
        component.append(i)
        for j in range(n):
            if overlaps[i][j] and not visited[j]:
                dfs(j, component)

    for i in range(n):
        if not visited[i]:
            component: list[int] = []
            dfs(i, component)
            components.append(component)

    # In each component, keep only the best span
    chosen_indices: set[int] = set()
    for component in components:
        best_idx = min(component, key=lambda i: _rank(spans[i]))
        chosen_indices.add(best_idx)

    # Return kept spans sorted by start
    chosen = [spans[i] for i in chosen_indices]
    return sorted(chosen, key=lambda s: s.start)
