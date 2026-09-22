# Showcase

Twenty-two games, simulations and visual toys, each one a self-contained prototype. Most began as
[Pygame](https://www.pygame.org/) experiments and every one of them now has a **browser version** —
plain HTML and Canvas 2D, hand-rolled, no framework and no build step.

### ▶ Play them: **https://francolaboranti.github.io/Showcase/**

> The URL is case-sensitive — `Showcase` with a capital `S`.

That link opens the **Arcade**: an installable web app that launches every game. On a phone, "Add
to Home Screen" and it runs fullscreen like a native app. Landscape games rotate themselves, so you
just turn the phone sideways.

## The games

Four of them were born in the browser and have no Python original.

| | Play | Python |
|---|---|---|
| **Loop** — arena arcade roguelite that fuses every other game in the repo | [▶](Loop/LoopWeb/index.html) | — |
| **Stick Fight** — platformer-brawler sandbox | [▶](StickFight/StickFightWeb/index.html) | — |
| **Donkey Kong** | [▶](DonkeyKong/DonkeyKongWeb/index.html) | — |
| **Pac-Man** | [▶](Pacman/PacmanWeb/index.html) | — |
| Canicas — marble physics sandbox | [▶](Balls/BallsWeb/index.html) | [Balls.py](Balls/Balls.py) |
| Mini Canicas | [▶](MiniBalls/MiniBallsWeb/index.html) | [MiniBalls.py](MiniBalls/MiniBalls.py) |
| Tank Wars | [▶](TankWARS/TankWARSWeb/index.html) | [TankWARS.py](TankWARS/TankWARS.py) |
| Crazy Tanks | [▶](CrazyTanks/CrazyTanksWeb/index.html) | [CrazyTanks.py](CrazyTanks/CrazyTanks.py) |
| Sleepy Pong | [▶](Pong/PongWeb/index.html) | [Pong.py](Pong/Pong.py) |
| Snake | [▶](Snake/SnakeWeb/index.html) | [Snake.py](Snake/Snake.py) |
| Tron | [▶](Tron/TronWeb/index.html) | [Tron.py](Tron/Tron.py) |
| Tron V2 | [▶](TronV2/TronV2Web/index.html) | [TronV2.py](TronV2/TronV2.py) |
| Fuegos Artificiales | [▶](Fireworks/FireworksWeb/index.html) | [Fireworks.py](Fireworks/Fireworks.py) |
| Fuegos Artificiales V2 | [▶](FireworksV2/FireworksV2Web/index.html) | [FireworksV2.py](FireworksV2/FireworksV2.py) |
| Ajedrez | [▶](Chess/ChessWeb/index.html) | [Chess.py](Chess/Chess.py) |
| Póker | [▶](Poker/PokerWeb/index.html) | [Poker.py](Poker/Poker.py) |
| Buscaminas | [▶](MineSweeperGPT/MineSweeperWeb/index.html) | [MineSweeperGPT.py](MineSweeperGPT/MineSweeperGPT.py) |
| Ahorcado | [▶](Hangman/HangmanWeb/index.html) | [Hangman.py](Hangman/Hangman.py) |
| Ta-Te-Ti | [▶](Tateti/TatetiWeb/index.html) | [Tateti.py](Tateti/Tateti.py) |
| Simón Dice | [▶](SimonSays/SimonSaysWeb/index.html) | [SimonSays.py](SimonSays/SimonSays.py) |
| Péndulo de Newton | [▶](Newton's%20Cradle/NewtonsCradleWeb/index.html) | [Newton's Cradle.py](Newton's%20Cradle/Newton's%20Cradle.py) |
| Reloj | [▶](Clock/ClockWeb/index.html) | [Clock.py](Clock/Clock.py) |

## How it's built

Each folder is independent — no shared modules, no package, no bundler. A game is one HTML file
with its CSS and JavaScript inside it, drawing to a single `<canvas>`.

The browser versions are **reimplementations, not ports run through a transpiler**: the Python and
the JavaScript are edited separately and have drifted apart on purpose, since a phone wants
different controls than a keyboard.

Almost everything is written from scratch, including the physics, the audio synthesis and the
touch joysticks. The one third-party library in the whole repo is
[Matter.js](https://brm.io/matter-js/) for rigid-body physics, used by four of the games.

[Arcade/](Arcade/index.html) is the launcher: a Progressive Web App with its own
[manifest](Arcade/manifest.json), icons and service worker. It runs each game in an iframe without
navigating away, so the fullscreen it asks for on the first tap lasts the whole session.

## Running it yourself

The web versions are static files, but they fetch assets, so serve them rather than opening
`file://`:

```powershell
python -m http.server 8000
# then open http://localhost:8000
```

The Python originals need `pygame` (`pip install pygame`), plus `pymunk` for Canicas. Each one runs
on its own — there is no entry point:

```powershell
python <Folder>\<Folder>.py
```

The folder `Newton's Cradle` has an apostrophe in its name; quote the path when running it.
