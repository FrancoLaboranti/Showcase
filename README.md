# Showcase

A collection of standalone games, simulations and visual toys. Each one started as
a [Pygame](https://www.pygame.org/) prototype and most also have a hand-rolled
**browser port** (plain HTML + Canvas 2D, no build step) living in a `<Folder>Web/`
subfolder next to the Python original.

A landing page at [index.html](index.html) ties them together: a grid of cards that
links straight to each game's web version. It's published with GitHub Pages at:

**https://francolaboranti.github.io/Showcase/**

> The URL is case-sensitive — it's `Showcase` (capital `S`, the rest lowercase).

## Games

| Game | Python | Web |
|------|--------|-----|
| Canicas (marble physics sandbox) | — | [Balls/BallsWeb](Balls/BallsWeb/index.html) |
| Ajedrez | [Chess](Chess/Chess.py) | [Chess/ChessWeb](Chess/ChessWeb/index.html) |
| Reloj | [Clock](Clock/Clock.py) | [Clock/ClockWeb](Clock/ClockWeb/index.html) |
| Crazy Tanks | [CrazyTanks](CrazyTanks/CrazyTanks.py) | [CrazyTanks/CrazyTanksWeb](CrazyTanks/CrazyTanksWeb/index.html) |
| Fuegos Artificiales | [Fireworks](Fireworks/Fireworks.py) | [Fireworks/FireworksWeb](Fireworks/FireworksWeb/index.html) |
| Fuegos Artificiales V2 | [FireworksV2](FireworksV2/FireworksV2.py) | [FireworksV2/FireworksV2Web](FireworksV2/FireworksV2Web/index.html) |
| Ahorcado | [Hangman](Hangman/Hangman.py) | [Hangman/HangmanWeb](Hangman/HangmanWeb/index.html) |
| Buscaminas | [MineSweeperGPT](MineSweeperGPT/MineSweeperGPT.py) | [MineSweeperGPT/MineSweeperWeb](MineSweeperGPT/MineSweeperWeb/index.html) |
| Mini Canicas | [MiniBalls](MiniBalls/MiniBalls.py) | [MiniBalls/MiniBallsWeb](MiniBalls/MiniBallsWeb/index.html) |
| Péndulo de Newton | [Newton's Cradle](Newton's%20Cradle/Newton's%20Cradle.py) | [Newton's Cradle/NewtonsCradleWeb](Newton's%20Cradle/NewtonsCradleWeb/index.html) |
| Póker | [Poker](Poker/Poker.py) | [Poker/PokerWeb](Poker/PokerWeb/index.html) |
| Pong | [Pong](Pong/Pong.py) | [Pong/PongWeb](Pong/PongWeb/index.html) |
| Simón Dice | [SimonSays](SimonSays/SimonSays.py) | [SimonSays/SimonSaysWeb](SimonSays/SimonSaysWeb/index.html) |
| Snake | [Snake](Snake/Snake.py) | [Snake/SnakeWeb](Snake/SnakeWeb/index.html) |
| Tank Wars | [TankWARS](TankWARS/TankWARS.py) | [TankWARS/TankWARSWeb](TankWARS/TankWARSWeb/index.html) |
| Ta-Te-Ti | [Tateti](Tateti/Tateti.py) | [Tateti/TatetiWeb](Tateti/TatetiWeb/index.html) |
| Tron | [Tron](Tron/Tron.py) | [Tron/TronWeb](Tron/TronWeb/index.html) |
| Tron V2 | [TronV2](TronV2/TronV2.py) | [TronV2/TronV2Web](TronV2/TronV2Web/index.html) |

## Running the web version

The browser ports are static files, but some fetch assets (sounds, etc.), so open
them through a local web server rather than `file://`:

```powershell
# from the repo root
python -m http.server 8000
# then open http://localhost:8000 in a browser
```

Any static server works. The landing page and every game are reachable from there.

## Running the Python version

The only dependency is `pygame` (install with `pip install pygame`). Each project is
launched directly — there is no entry-point script:

```powershell
python <Folder>\<Folder>.py
```

The folder `Newton's Cradle` contains an apostrophe — quote the path when running it.

## Notes

- The web ports are faithful reimplementations of the Pygame originals, **not**
  transpiled from the `.py` — the two are edited independently.
- [Balls/BallsWeb](Balls/BallsWeb/index.html) (the marble sandbox) is the reference
  port and the only one with a vendored dependency (`matter.min.js` for physics);
  every other port is dependency-free hand-rolled JS.
