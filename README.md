# Showcase

Thirty games, simulations and visual toys, each one a self-contained prototype that runs in the browser:
plain HTML and Canvas 2D, hand-rolled, with no framework and no build step.

### ▶ Play them: **https://francolaboranti.github.io/Showcase/**

That link opens the **Arcade**: an installable web app that launches every game. On a phone, "Add
to Home Screen" and it runs fullscreen like a native app. Landscape games rotate themselves, so you
just turn the phone sideways.

## The games

Fifteen of them were born in the browser and have no Python original (in bold); the other fifteen began as
[Pygame](https://www.pygame.org/) experiments, linked beside them.

| | Play |
|---|---|
| **Loop**: arena arcade roguelite that fuses every other game in the repo | [▶](Games/Loop/LoopWeb/index.html) |
| **Stick Fight**: platformer-brawler sandbox | [▶](Games/Stick%20Fight/StickFightWeb/index.html) |
| **Donkey Kong**: a homage to the 1981 arcade game: climb the girders past rolling barrels and fireballs to reach Pauline | [▶](Games/Donkey%20Kong/DonkeyKongWeb/index.html) |
| **Pac-Man**: the maze chase, with a second honeycomb maze and a Hard mode | [▶](Games/Pac-Man/PacManWeb/index.html) |
| **Kung-Fu Master**: side-scrolling martial arts up five floors, where each guardian's hall opens only once you have beaten enough fighters | [▶](Games/Kung-Fu%20Master/KungFuMasterWeb/index.html) |
| **Truco**: Argentine truco against the CPU, with the calls, the envido and the score in matches | [▶](Games/Truco/TrucoWeb/index.html) |
| **Doom**: a 90s first-person shooter down five floors of a foundry buried under the city | [▶](Games/Doom/DoomWeb/index.html) |
| **Stone Crown**: real-time strategy on a procedural map: gather, build, train an army and raze the rival's base | [▶](Games/Stone%20Crown/StoneCrownWeb/index.html) |
| **Cave In**: a grid bomber down a mine that is coming apart, four strata and a boss at the bottom of each | [▶](Games/Cave%20In/CaveInWeb/index.html) |
| **Cinder Heart**: a pixel-art, turn-based party RPG up a stair into a dead sky: six zones, a skill tree, loot and a boss at the top of each | [▶](Games/Cinder%20Heart/CinderHeartWeb/index.html) |
| **Lanternvale**: a top-down action RPG in the spirit of the old Flash RPGs: a village, five wild zones, quests, loot and three bosses | [▶](Games/Lanternvale/LanternvaleWeb/index.html) |
| **Rumble Cup**: five-a-side arcade football after Nintendo World Cup, with five pitches, ten specials and a cup to win | [▶](Games/Rumble%20Cup/RumbleCupWeb/index.html) |
| **Al Paso!**: run a street food stand on the Costanera of Buenos Aires for a week: cook, plate and serve before the line loses patience (Spanish interface) | [▶](Games/Al%20Paso!/AlPasoWeb/index.html) |
| **Bloom**: a relaxing isometric garden: grow flowers, spend their petals on land wherever you like, then arrange it and paint your own designs on its objects | [▶](Games/Bloom/BloomWeb/index.html) |
| **Afterfall**: a first-person zombie survival game: scavenge a town laid out anew each run from a shelter with a small backpack, mind the noise you make, and repair the truck that takes you out | [▶](Games/Afterfall/AfterfallWeb/index.html) |
| Marbles: a marble physics sandbox: drag a marble to throw it, make them all jump, add or remove them | [▶](Games/Marbles/MarblesWeb/index.html) |
| Tank Wars: a top-down tank shooter: survive the waves and spend their gold on upgrades | [▶](Games/Tank%20Wars/TankWarsWeb/index.html) |
| Crazy Tanks: a top-down tank race against 15 rivals on a circuit generated for every race, with bombs and nitro | [▶](Games/Crazy%20Tanks/CrazyTanksWeb/index.html) |
| Sleepy Pong: Pong against a line of rivals who nap in the middle of a rally, plus a Bricks mode | [▶](Games/Sleepy%20Pong/SleepyPongWeb/index.html) |
| Snake: a snake brawl in a circular lake: dash into enemy snakes, beat three bosses and pick upgrade cards (the Python original is the classic snake) | [▶](Games/Snake/SnakeWeb/index.html) |
| Tron: light cycles: leave a trail, cut the others off, and be the last one riding | [▶](Games/Tron/TronWeb/index.html) |
| Fireworks: launch rockets and watch them burst into smaller bursts | [▶](Games/Fireworks/FireworksWeb/index.html) |
| Chess: full chess against the Stockfish engine or a friend on the same screen | [▶](Games/Chess/ChessWeb/index.html) |
| Poker: heads-up Texas Hold'em against the CPU | [▶](Games/Poker/PokerWeb/index.html) |
| Minesweeper: the classic, plus a Gold Rush mode and a difficulty in stars | [▶](Games/Minesweeper/MinesweeperWeb/index.html) |
| Hangman: guess the word before the gallows is finished, in English or Spanish, with a category and a hint | [▶](Games/Hangman/HangmanWeb/index.html) |
| Tic-Tac-Toe: against a friend or a CPU that slips now and then, with a running score | [▶](Games/Tic-Tac-Toe/TicTacToeWeb/index.html) |
| Simon: repeat the growing sequence of lights and tones | [▶](Games/Simon/SimonWeb/index.html) |
| Newton's Cradle: pull a ball back and let the chain carry its momentum, with 1 to 10 balls | [▶](Games/Newton's%20Cradle/NewtonsCradleWeb/index.html) |
| Clock: an analog clock with a ticking or a sweeping second hand | [▶](Games/Clock/ClockWeb/index.html) |

## How it's built

Each game lives in its own folder under `Games/`, independent except for two small pieces every game
loads from the Arcade: its shell (the corner buttons and the info panel) and its audio module. A game
is one HTML file with its CSS and JavaScript inside it, drawing to a single `<canvas>`.

Where a Python original exists, the browser version is a **reimplementation, not a port run through a
transpiler**: the two are edited separately and have drifted apart on purpose, since a phone wants
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
