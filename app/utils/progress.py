from __future__ import annotations

from collections.abc import Callable

ProgressCallback = Callable[[int], None]


class RangedProgress:
    def __init__(
        self,
        callback: ProgressCallback | None,
        start: int,
        end: int,
        total_steps: int,
    ) -> None:
        self.callback = callback
        self.end = end
        self.span = max(0, end - start)
        self.modulo = max(1, total_steps)
        self.remainder = 0
        self.value = start

    def advance(self) -> None:
        if not self.callback or not self.span:
            return

        self.remainder += self.span
        increment = self.remainder // self.modulo
        self.remainder %= self.modulo
        if increment:
            self.value = min(self.end, self.value + increment)
            self.callback(self.value)

    def finish(self) -> None:
        if self.callback:
            self.callback(self.end)
