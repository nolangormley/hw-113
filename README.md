# hw-113

Sokoban — A graphical puzzle game built with pygame.

## HOW TO PLAY:
Push all boxes onto goal squares to win.
Move with arrow keys or WASD.

## ARCHITECTURE:
- SokobanGame class holds all game state and logic.
- The grid is a 2D list of single-character strings.
- The player's position is tracked separately from the grid;
  the grid stores what is "underneath" the player (floor or goal).
- Rendering uses pygame — each cell is drawn as a colored square.

## COLLABORATION:
This file contains a working foundation with five features left
unimplemented as stub methods.  Search for "TODO(peer)" to find
all five stubs that need to be completed:
1. push_box()             — box pushing logic
2. check_win()            — win condition detection
3. undo()                 — undo last move
4. increment_move_count() — move counter
5. reset_level()          — restart the current level

Each stub has a detailed docstring explaining what to implement
and hints on how to do it.

## CELL TYPES:
```
#   wall              .   goal            (space)   floor
@   player            +   player on goal
$   box               *   box on goal
```