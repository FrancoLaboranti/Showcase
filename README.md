# Showcase

Thirty games, simulations and visual toys, each one a self-contained prototype. Most began as
[Pygame](https://www.pygame.org/) experiments and every one of them now has a **browser version**:
plain HTML and Canvas 2D, hand-rolled, no framework and no build step.

### ▶ Play them: **https://francolaboranti.github.io/Showcase/**

> The URL is case-sensitive: `Showcase` with a capital `S`.

That link opens the **Arcade**: an installable web app that launches every game. On a phone, "Add
to Home Screen" and it runs fullscreen like a native app. Landscape games rotate themselves, so you
just turn the phone sideways.

## The games

Twelve of them were born in the browser and have no Python original.

| | Play |
|---|---|
| **Loop**: arena arcade roguelite that fuses every other game in the repo | [▶](Loop/LoopWeb/index.html) |
| **Stick Fight**: platformer-brawler sandbox | [▶](StickFight/StickFightWeb/index.html) |
| **Donkey Kong** | [▶](DonkeyKong/DonkeyKongWeb/index.html) |
| **Pac-Man** | [▶](Pacman/PacmanWeb/index.html) |
| **Kung-Fu Master**: side-scrolling martial arts, five floors and their guardians | [▶](KungFuMaster/KungFuMasterWeb/index.html) |
| **Truco**: Argentine truco against the CPU, with the calls, the envido and the score in matches | [▶](Truco/TrucoWeb/index.html) |
| **Doom**: a 90s first-person shooter down five floors of a foundry buried under the city | [▶](Doom/DoomWeb/index.html) |
| **Stone Crown**: real-time strategy on a procedural map: gather, build, train an army and raze the rival's base | [▶](StoneCrown/StoneCrownWeb/index.html) |
| **Cave-In**: a grid bomber down a mine that is coming apart, four strata and a boss at the bottom of each | [▶](CaveIn/CaveInWeb/index.html) |
| **Cinderheart**: a turn-based party RPG up a stair into a dead sky: six zones, a skill tree, loot and a boss at the top of each | [▶](Cinderheart/CinderheartWeb/index.html) |
| **Lanternvale**: a top-down action RPG in the spirit of the old Flash RPGs: a village, five wild zones, quests, loot and three bosses | [▶](Lanternvale/LanternvaleWeb/index.html) |
| **Rumble Cup**: five-a-side arcade football after Nintendo World Cup, with five pitches, ten specials and a cup to win | [▶](RumbleCup/RumbleCupWeb/index.html) |
| Marbles: marble physics sandbox | [▶](Balls/BallsWeb/index.html) |
| Mini Marbles | [▶](MiniBalls/MiniBallsWeb/index.html) |
| Tank Wars | [▶](TankWARS/TankWARSWeb/index.html) |
| Crazy Tanks | [▶](CrazyTanks/CrazyTanksWeb/index.html) |
| Sleepy Pong | [▶](Pong/PongWeb/index.html) |
| Snake | [▶](Snake/SnakeWeb/index.html) |
| Tron | [▶](Tron/TronWeb/index.html) |
| Tron V2 | [▶](TronV2/TronV2Web/index.html) |
| Fireworks | [▶](Fireworks/FireworksWeb/index.html) |
| Fireworks V2 | [▶](FireworksV2/FireworksV2Web/index.html) |
| Chess | [▶](Chess/ChessWeb/index.html) |
| Poker | [▶](Poker/PokerWeb/index.html) |
| Minesweeper | [▶](MineSweeperGPT/MineSweeperWeb/index.html) |
| Hangman | [▶](Hangman/HangmanWeb/index.html) |
| Tic Tac Toe | [▶](Tateti/TatetiWeb/index.html) |
| Simon | [▶](SimonSays/SimonSaysWeb/index.html) |
| Newton's Cradle | [▶](Newton's%20Cradle/NewtonsCradleWeb/index.html) |
| Clock | [▶](Clock/ClockWeb/index.html) |

## How it's built

Each folder is independent except for two small pieces every game loads from the Arcade: its shell
(the corner buttons and the info panel) and its audio module. There is no package and no bundler:
a game is one HTML file with its CSS and JavaScript inside it, drawing to a single `<canvas>`.

The browser versions are **reimplementations, not ports run through a transpiler**: the Python and
the JavaScript are edited separately and have drifted apart on purpose, since a phone wants
different controls than a keyboard.

Almost everything is written from scratch, including the physics, the audio synthesis and the
touch joysticks. The third-party code is [Matter.js](https://brm.io/matter-js/) for rigid-body
physics, used by four of the games, and [Stockfish](https://stockfishchess.org/), the engine Chess
plays against.

[Arcade/](Arcade/index.html) is the launcher: a Progressive Web App with its own
[manifest](Arcade/manifest.json), icons and service worker. It runs each game in an iframe without
navigating away, so the fullscreen it asks for on the first tap lasts the whole session.

---

© 2026 Franco Laboranti. All rights reserved. See [LICENSE](LICENSE). This repository is the site as it is served; the source code is not published.
