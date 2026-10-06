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

Fifteen of them were born in the browser and have no Python original.

| | Play |
|---|---|
| **Loop**: arena arcade roguelite that fuses every other game in the repo | [▶](Games/Loop/LoopWeb/index.html) |
| **Stick Fight**: platformer-brawler sandbox | [▶](Games/Stick%20Fight/StickFightWeb/index.html) |
| **Donkey Kong** | [▶](Games/Donkey%20Kong/DonkeyKongWeb/index.html) |
| **Pac-Man** | [▶](Games/Pac-Man/PacManWeb/index.html) |
| **Kung-Fu Master**: side-scrolling martial arts, five floors and their guardians | [▶](Games/Kung-Fu%20Master/KungFuMasterWeb/index.html) |
| **Truco**: Argentine truco against the CPU, with the calls, the envido and the score in matches | [▶](Games/Truco/TrucoWeb/index.html) |
| **Doom**: a 90s first-person shooter down five floors of a foundry buried under the city | [▶](Games/Doom/DoomWeb/index.html) |
| **Stone Crown**: real-time strategy on a procedural map: gather, build, train an army and raze the rival's base | [▶](Games/Stone%20Crown/StoneCrownWeb/index.html) |
| **Cave-In**: a grid bomber down a mine that is coming apart, four strata and a boss at the bottom of each | [▶](Games/Cave%20In/CaveInWeb/index.html) |
| **Cinderheart**: a turn-based party RPG up a stair into a dead sky: six zones, a skill tree, loot and a boss at the top of each | [▶](Games/Cinder%20Heart/CinderHeartWeb/index.html) |
| **Lanternvale**: a top-down action RPG in the spirit of the old Flash RPGs: a village, five wild zones, quests, loot and three bosses | [▶](Games/Lantern%20Vale/LanternValeWeb/index.html) |
| **Rumble Cup**: five-a-side arcade football after Nintendo World Cup, with five pitches, ten specials and a cup to win | [▶](Games/Rumble%20Cup/RumbleCupWeb/index.html) |
| Marbles: marble physics sandbox | [▶](Games/Marbles/MarblesWeb/index.html) |
| Tank Wars | [▶](Games/Tank%20Wars/TankWarsWeb/index.html) |
| Crazy Tanks | [▶](Games/Crazy%20Tanks/CrazyTanksWeb/index.html) |
| Sleepy Pong | [▶](Games/Sleepy%20Pong/SleepyPongWeb/index.html) |
| Snake | [▶](Games/Snake/SnakeWeb/index.html) |
| Tron | [▶](Games/Tron/TronWeb/index.html) |
| Fireworks | [▶](Games/Fireworks/FireworksWeb/index.html) |
| Chess | [▶](Games/Chess/ChessWeb/index.html) |
| Poker | [▶](Games/Poker/PokerWeb/index.html) |
| Minesweeper | [▶](Games/Minesweeper/MinesweeperWeb/index.html) |
| Hangman | [▶](Games/Hangman/HangmanWeb/index.html) |
| Tic Tac Toe | [▶](Games/Tic-Tac-Toe/TicTacToeWeb/index.html) |
| Simon | [▶](Games/Simon/SimonWeb/index.html) |
| Newton's Cradle | [▶](Games/Newton's%20Cradle/NewtonsCradleWeb/index.html) |
| Clock | [▶](Games/Clock/ClockWeb/index.html) |
| **Al Paso!**: Run a street food stand on the Costanera of Buenos Aires: cook, plate, serve and collect before the line loses patience (Spanish interface) | [▶](Games/Al%20Paso!/AlPasoWeb/index.html) |
| **Bloom**: a relaxing garden where you plant and harvest flowers for their pigments, mix them, paint your decorations and unlock more garden | [▶](Games/Bloom/BloomWeb/index.html) |
| **Afterfall**: a first-person zombie survival game: scavenge a dead town from a shelter with a small backpack, mind the noise you make, and repair the truck that takes you out | [▶](Games/Afterfall/AfterfallWeb/index.html) |

## How it's built

Each game lives in its own folder under `Games/`, independent except for two small pieces every game
loads from the Arcade: its shell (the corner buttons and the info panel) and its audio module. There is no package and no bundler:
a game is one HTML file with its CSS and JavaScript inside it, drawing to a single `<canvas>`.

The browser versions are **reimplementations, not ports run through a transpiler**: the Python and
the JavaScript are edited separately and have drifted apart on purpose, since a phone wants
different controls than a keyboard.

Almost everything is written from scratch, including the physics, the audio synthesis and the
touch joysticks. The third-party code is [Matter.js](https://brm.io/matter-js/) for rigid-body
physics, used by three of the games, and [Stockfish](https://stockfishchess.org/), the engine Chess
plays against.

[Arcade/](Arcade/index.html) is the launcher: a Progressive Web App with its own
[manifest](Arcade/manifest.json), icons and service worker. It runs each game in an iframe without
navigating away, so the fullscreen it asks for on the first tap lasts the whole session.

---

© 2026 Franco Laboranti. All rights reserved. See [LICENSE](LICENSE). This repository is the site as it is served; the source code is not published.
