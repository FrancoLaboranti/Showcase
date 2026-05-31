# Showcase

A collection of small games and visual demos written in **Python** using the
[pygame](https://www.pygame.org/) library. Every program is a single, self-contained
`.py` file with no external assets (images, sounds or font files) to download —
you only need Python and pygame installed.

## Programs

| File | Type | Description |
|------|------|-------------|
| [Pong.py](Pong.py) | Game | Classic two-paddle Pong with a menu. |
| [Snake.py](Snake.py) | Game | A mouse-driven take on Snake. |
| [Tron.py](Tron.py) / [TronV2.py](TronV2.py) | Game | Light-cycle Tron with up to 4 players. |
| [CrazyTanks.py](CrazyTanks.py) | Game | Two-player tank battle. |
| [TankWARS.py](TankWARS.py) | Game | Wave-based tank survival shooter. |
| [MineSweeperGPT.py](MineSweeperGPT.py) | Game | Minesweeper. |
| [SimonSays.py](SimonSays.py) | Game | Memory / Simon-Says game. |
| [Clock.py](Clock.py) | Demo | Animated analog clock. |
| [Newton's Cradle.py](Newton's%20Cradle.py) | Demo | Newton's cradle physics simulation. |
| [Fireworks.py](Fireworks.py) / [FireworksV2.py](FireworksV2.py) | Demo | Fireworks particle simulation. |
| [Balls.py](Balls.py) / [MiniBalls.py](MiniBalls.py) | Demo | Bouncing-balls particle simulation. |

## Requirements

- **Python 3.8+** (any recent Python 3 works)
- **pygame** (the only third-party dependency)

---

## Setup & Running

The steps below use a [virtual environment](https://docs.python.org/3/library/venv.html)
so pygame is installed cleanly without touching your system Python. This is optional
but recommended.

### Windows

Open **PowerShell** (or Command Prompt) in the project folder, then:

```powershell
# 1. Create a virtual environment (once)
python -m venv .venv

# 2. Activate it (each new terminal session)
.\.venv\Scripts\Activate.ps1
# If PowerShell blocks the script, run this once first:
#   Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# 3. Install dependencies (once)
pip install -r requirements.txt

# 4. Run any program
python Pong.py
```

> Filenames with a space or apostrophe must be quoted, e.g.:
> `python ".\Newton's Cradle.py"`

### Linux

Open a **terminal** in the project folder, then:

```bash
# 1. Create a virtual environment (once)
python3 -m venv .venv

# 2. Activate it (each new terminal session)
source .venv/bin/activate

# 3. Install dependencies (once)
pip install -r requirements.txt

# 4. Run any program
python3 Pong.py
```

Some minimal Linux installs need the SDL system libraries that pygame relies on.
If pygame fails to open a window, install them via your package manager, e.g. on
Debian/Ubuntu:

```bash
sudo apt update
sudo apt install python3-pygame
# or, if installing pygame via pip:
sudo apt install libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0
```

### Without a virtual environment

If you'd rather install pygame globally, just run steps 3 and 4:

```bash
pip install -r requirements.txt     # Windows
pip3 install -r requirements.txt    # Linux

python Pong.py                      # Windows
python3 Pong.py                     # Linux
```

---

## Controls

Most games share a few common keys:

- **Esc** — quit / back to menu
- **Enter / Return** — confirm or start (menu screens)
- **P** — pause (where supported)
- **F** — toggle fullscreen (some games; `Snake` uses **Alt+Enter**)

Per-program:

| Program | Controls |
|---------|----------|
| **Pong** | Player 1: **W / S** · Player 2: **↑ / ↓** · **P** pause |
| **Snake** | Move the **mouse** to steer · hold **left mouse button** to speed up |
| **Tron / TronV2** | P1: **arrow keys** · P2: **Q / W** · P3: **O / P** · P4: **V / B** |
| **CrazyTanks** | P1: **arrows** + **Right Ctrl** to fire · P2: **WASD** + **Space** to fire |
| **TankWARS** | Move **WASD** · fire **Space** · **Tab** scoreboard · **P** pause |
| **MineSweeper** | **Left/right mouse** to reveal/flag · **R** restart |
| **SimonSays** | Follow the on-screen prompts (mouse / keys) |
| **Fireworks / Balls / Clock / Newton's Cradle** | Visual demos — **Space** / arrow keys adjust effects where available; **Esc** to exit |

> Controls vary slightly between programs; check the top of each `.py` file for the
> exact key bindings.

---

## Troubleshooting

- **`ModuleNotFoundError: No module named 'pygame'`** — pygame isn't installed in the
  Python you're running. Make sure your virtual environment is activated, or run
  `pip install pygame`.
- **`python` not found (Linux)** — use `python3` instead.
- **Window won't open / SDL error (Linux)** — install the SDL libraries listed above.
- **PowerShell won't activate the venv** — run
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then reopen PowerShell.
