---
name: terminal-image-viewer
description: Show an image inline in the user's terminal from inside a devcell container — screenshots, renders, diffs, generated art. Use when the user asks to see an image, or when reviewing something visual (illustration edits, page renders, chart output, UI screenshots) would be faster to judge by eye than by file path. Requires a Kitty-graphics terminal (ghostty/kitty/WezTerm); tmux needs allow-passthrough on.
---

# Terminal image viewer

Put an image on the user's screen instead of handing them a path to open.

```bash
scripts/show.sh <image> [label]                             # display (auto-scaled)
scripts/show.sh <image> <max_cols> <max_rows> [label]       # display (explicit size)
scripts/compare.sh "BEFORE:a.png" "AFTER:b.png" [...]       # side by side
scripts/clear.sh                                            # remove all images
```

`show.sh` **auto-scales** images: it reads the terminal size, computes 1/3
of terminal width as the target, pre-scales the image to that cell footprint
(saving the scaled version to `$TMPDIR`), and then encodes the scaled copy.
Pass explicit `max_cols`/`max_rows` only if the default 1/3 width is wrong.

The LLM does NOT need to manually compute sizing or pre-scale. Just call
`show.sh <image>` or `show.sh <image> "my label"` and it handles everything.

Comparisons go through `compare.sh`, which composites the panels into **one**
image and then auto-scales the composite. Two separate placements cannot be
aligned to a shared baseline, and each extra id is another thing to clean up.

<constraints>
**Look at the image with the Read tool before showing it.** Every time. The
terminal render is small and lossy, so the user cannot reliably spot a defect
there — and if you have not looked, you are asking them to QA output you never
inspected. This has already produced one bad review round: a generated cutout
went out with a chunk eaten from the middle and its outlines stripped, both
obvious at full size and invisible at 62 cells wide.

Say what you checked and what you found. If the image is wrong, fix it before
sending, or send it and state the defect up front — never send it silently.

**Height is clamped to the viewport** (`TERM_ROWS - 12`). The grid is inline
text, so a taller image scrolls off and the user sees only its tail. Prefer a
smaller footprint over a cropped one.
</constraints>

## Why this is not just `kitten icat`

The agent cannot print bytes to the terminal. Its replies are rendered as
markdown by the harness, and **the ESC byte is stripped from tool output** — an
escape sequence emitted by a Bash call arrives as inert text (`_Ga=T,f=100;…`
with no `\x1b`). The same happens to anything the user runs with the `!`
prefix, since that output is captured too.

The only path to the screen is a **direct write to the pty**, which needs root
because the device is `root:tty 0620` while the agent runs as an unprivileged
uid. `scripts/show.sh` does that with `sudo`.

## How it works

1. **Transmit the image virtually** — `a=T,U=1,f=100,i=1,c=…,r=…,q=2`, wrapped
   in a tmux DCS passthrough. The terminal stores the bytes and draws nothing.
2. **Write a grid of `U+10EEEE` placeholder characters as ordinary text** — not
   wrapped, so tmux parses it into the pane's own screen model. The terminal
   overlays the stored image onto those cells.

Step 2 is the whole design. A plain `a=T` placement is anchored to *physical
screen cells* that tmux knows nothing about, so the picture **floats on top of
every window and session** until explicitly deleted. Placeholders live in the
text grid, so the image is scoped to the pane and disappears when its cells are
overwritten or scrolled — like any other output.

Right-alignment is done by **padding rows with spaces**, never by `CUP`
cursor positioning: an absolute cursor move addresses physical screen cells and
reintroduces the floating behaviour.

## Prerequisites

- Kitty-graphics-capable terminal: ghostty, kitty, WezTerm.
- Inside tmux: `tmux set -g allow-passthrough on` (tmux ≥ 3.3). Without it tmux
  silently swallows the APC sequence and **nothing at all appears** — no error,
  no garbage. Silence is the signature of missing passthrough.
- Passwordless `sudo` in the container, and PIL available (`uv run --with pillow`).

## Traps

Each of these cost real debugging time:

- **Stacking images.** Placements without an `i=` id cannot be deleted later —
  the terminal never associated them with a handle. Always transmit with a
  stable id; re-transmitting the same id *replaces* the image, so no delete is
  needed. `clear.sh` sends `a=d,d=A` to clean up strays from earlier attempts.
- **Vertical tiling.** Every placeholder cell must carry row and column
  diacritics. Without them the SGR reset plus newline between rows breaks the
  terminal's contiguous-run detection and each row renders a full copy of the
  image.
- **The id travels in the foreground colour** — R=high, G=mid, B=low byte. Ids
  above 2^24 need a fourth diacritic per cell, which this skill does not emit.
- **Transparent PNGs render black.** PIL's `convert("RGB")` maps alpha=0 to
  BLACK, so cut-out artwork comes out on a black field — always
  `alpha_composite` onto white instead. `encode.py` flattens by default; set
  `TTY_IMAGE_KEEP_ALPHA=1` to let the terminal background show through.
- **Grid capped at 297×297 cells** — the length of Kitty's diacritic table,
  shipped as `scripts/rowcolumn-diacritics.txt` (with the first 32 inline in
  `encode.py` as a fallback). Anything larger needs a fourth diacritic per cell.
- **`q=2` on transmit** keeps the terminal silent. Responses would be
  unreadable anyway — nothing here can read from the pty.

## Dead ends — do not retry these

- `/proc/<claude_pid>/fd/1` → `EACCES`, even though it points at the right pty.
- Writing as the agent's own uid → `EACCES` on `/dev/pts/N` (`root:tty 0620`).
- Env vars or settings to make the harness pass escapes through: none exist.
- Talking to tmux from the container: `TMUX` is unset and there is no socket —
  tmux runs on the host. So no `list-panes`, no targeting another pane.
- Mounting the host tmux socket on **macOS**: Docker Desktop's file sharing
  does not carry Unix sockets across the VM boundary (`/var/run/docker.sock`
  works only because it is special-cased).

## When the image must persist

Anything the agent writes competes with a live TUI repainting the pane. For a
picture that stays put, have the user open a second terminal attached to the
container and write there instead:

```bash
docker exec -it <container> zsh -c 'tty; exec zsh'   # prints e.g. /dev/pts/1
```

Pass that device as `TTY_IMAGE_DEV=/dev/pts/1` to `show.sh`. A tab with no tmux
also removes the passthrough requirement entirely.

## Attribution

The placeholder technique, the stable-id fix and the diacritic requirement are
taken from [DimmKirr/addiplay](https://github.com/DimmKirr/addiplay)
(`internal/fanart/placeholder.go`, `internal/fanart/tmuxwrap.go`), which solved
the same problems for a Bubble Tea TUI.
