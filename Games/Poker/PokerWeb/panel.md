# Poker
> Heads-up Hold'em: read the CPU, size the bet.

Two cards against the CPU's two, five on the board, one pot between you. Every raise is built from real chips, the CPU bets its good hands and bluffs now and then, and the showdown tells you exactly which hand won and why.

## How a hand goes
- Each hand starts at [DEAL], which posts the blinds ($10 and $20, taking turns) and deals two cards each. The board comes out three cards (the flop), then one (the turn) and one (the river), with a round of betting before each and after the last.
- The best five of your seven cards wins. From the flop on, the line between the board and your cards names the hand you hold.
- When either of you runs out of chips, [DEAL] gives both a fresh $10000.

## Your move
- [CHECK] [CALL] pass when nothing is owed, or match the bet (the button shows the price)
- [RAISE] bet more, with the chips you stacked
- [ALL IN] your whole stack
- [FOLD] give up the hand and the pot
- touch: Tap the chips in the bar ([10] to [1000]) to stack the total you raise to. Tap a column on the table to take one back; [CANCEL] clears them all.
- keys: Click the chips in the bar ([10] to [1000]) to stack the total you raise to. Click a column on the table to take one back; [CANCEL] clears them all.
- **RAISE** lights up once the stack reaches the minimum shown under it.

## Reading the CPU
- **Bet size matters**: the more your bet costs against the pot, the more hands the CPU lets go.
- It raises its strong hands, and bluffs too, most often on the flop.
- Two hands of one kind? The showdown names the pair or the kicker that decided it, and the winning cards stay lit until the next deal.
