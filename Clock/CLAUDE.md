# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Analog clock face rendered from `datetime.now()`. Click anywhere to toggle the second hand between **ticking** (`segundero == 0`, snaps per second) and **smooth** (`segundero == 1`, interpolated via `microsecond`). The smooth-second math packs microseconds into seconds as `(ca_ms + ca_s*999999) / (60*999999)` — that 999999 magic number is the multiplier, not a typo.

Window is 650×650. Spanish identifiers (`radio`, `centro_x/y`, `fuente`, `crear_texto`, `segundero`, `pressed`). No `ESC`-to-quit — only the window-close button exits.

This file shadows the stdlib `time` module by reassigning `time = datetime.datetime.now()` inside the loop. The `import time` at the top is currently unused; don't add `time.sleep(...)` without renaming the local first.

See [../CLAUDE.md](../CLAUDE.md) for shared conventions across the repo.
