import copy
import sys

import pygame


# ---------------------------------------------------------------------------
# Cell-type symbols used in the grid
# ---------------------------------------------------------------------------
WALL = "#"
FLOOR = " "
GOAL = "."
PLAYER = "@"
PLAYER_ON_GOAL = "+"
BOX = "$"
BOX_ON_GOAL = "*"

# Direction vectors keyed by input character (row_delta, col_delta)
DIRECTIONS = {
    "w": (-1, 0),   # up
    "a": (0, -1),   # left
    "s": (1, 0),    # down
    "d": (0, 1),    # right
}

# ---------------------------------------------------------------------------
# Pygame rendering constants
# ---------------------------------------------------------------------------
TILE_SIZE = 64          # pixels per grid cell
FPS = 30                # frame rate cap
HUD_HEIGHT = 80         # pixel height for the status bar below the grid

# RGB color for each cell type
COLORS = {
    WALL:          (100, 100, 100),   # dark gray
    FLOOR:         (220, 220, 220),   # light gray
    GOAL:          (220, 220, 220),   # light gray (dot drawn on top)
    BOX:           (180, 120,  60),   # brown
    BOX_ON_GOAL:   (100, 180, 100),   # green — box successfully on goal
    PLAYER:        ( 50, 100, 200),   # blue
}
COLOR_GOAL_DOT   = (220, 200, 50)    # yellow dot marking goal cells
COLOR_BACKGROUND = ( 40,  40,  40)   # window / HUD background
COLOR_TEXT        = (255, 255, 255)   # white text
COLOR_TILE_BORDER = (  0,   0,   0)  # black border between tiles

# ---------------------------------------------------------------------------
# Level data — each level is a list of strings, one string per row.
# Rows may differ in length; shorter rows are padded during parsing.
# ---------------------------------------------------------------------------

# Testing level
# LEVEL_1 = [
#     "#####",
#     "#@$.#",
#     "#####",
# ]

LEVEL_1 = [
    "  #####",
    "###   #",
    "#.@$  #",
    "### $.#",
    "#.##$ #",
    "# # . ##",
    "#$ *$$.#",
    "#   .  #",
    "########",
]


class SokobanGame:
    """Core game engine for Sokoban.

    Attributes:
        grid (list[list[str]]): 2D grid of cell characters.  The player
            is NOT stored in the grid — the grid holds what is underneath
            the player (FLOOR or GOAL).
        player_row (int): Current row of the player.
        player_col (int): Current column of the player.
        move_count (int): Number of moves made so far.
        history (list[tuple]): Stack of snapshots for undo.  Each entry is
            (grid_copy, player_row, player_col, move_count).
        initial_level (list[str]): Original level strings, kept so the
            level can be reset.
        screen (pygame.Surface): The pygame display surface (set by run()).
        font (pygame.font.Font): Font used for HUD text (set by run()).
    """

    def __init__(self, level_lines):
        """Initialize game state from a list of strings representing a level.

        Args:
            level_lines: List of strings where each string is one row of the
                level.  See the module docstring for the symbol key.
        """
        self.initial_level = level_lines
        self.grid, self.player_row, self.player_col = self._parse_level(
            level_lines
        )
        self.move_count = 0
        self.history = []

        # These are set by run() once pygame is initialized
        self.screen = None
        self.font = None

    # ------------------------------------------------------------------
    # Level parsing
    # ------------------------------------------------------------------

    def _parse_level(self, level_lines):
        """Parse a list of strings into a 2D grid and locate the player.

        Each character in the input maps directly to a grid cell.  Rows
        shorter than the longest row are right-padded with FLOOR spaces.

        The player symbol (@ or +) is replaced in the grid with the
        underlying cell (FLOOR or GOAL) because the player position is
        tracked separately in self.player_row / self.player_col.

        Args:
            level_lines: List of strings, one per row.

        Returns:
            A tuple (grid, player_row, player_col).
        """
        max_width = max(len(row) for row in level_lines)
        grid = []
        player_row = None
        player_col = None

        for r, row in enumerate(level_lines):
            grid_row = []
            for c in range(max_width):
                ch = row[c] if c < len(row) else FLOOR

                if ch == PLAYER:
                    # Player on a normal floor tile
                    player_row, player_col = r, c
                    grid_row.append(FLOOR)
                elif ch == PLAYER_ON_GOAL:
                    # Player standing on a goal tile
                    player_row, player_col = r, c
                    grid_row.append(GOAL)
                else:
                    grid_row.append(ch)

            grid.append(grid_row)

        if player_row is None:
            raise ValueError("Level has no player symbol (@ or +).")

        return grid, player_row, player_col

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self):
        """Draw the current board state to the pygame window.

        Each grid cell is drawn as a colored square.  The player is
        overlaid as a blue square at (player_row, player_col).  Goal
        cells that are not covered by a box or the player are marked
        with a small yellow dot.  A HUD bar below the grid shows the
        move count and controls.
        """
        self.screen.fill(COLOR_BACKGROUND)

        for r, row in enumerate(self.grid):
            for c, cell in enumerate(row):
                x = c * TILE_SIZE
                y = r * TILE_SIZE
                rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

                # Determine what to draw at this cell
                if r == self.player_row and c == self.player_col:
                    # Player square — draw floor/goal underneath first,
                    # then the player on top
                    under_color = COLORS.get(cell, COLORS[FLOOR])
                    pygame.draw.rect(self.screen, under_color, rect)
                    if cell == GOAL:
                        # Show goal dot underneath the player
                        center = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)
                        pygame.draw.circle(
                            self.screen, COLOR_GOAL_DOT, center, TILE_SIZE // 8
                        )
                    # Draw the player as a smaller centered square
                    margin = TILE_SIZE // 6
                    player_rect = pygame.Rect(
                        x + margin, y + margin,
                        TILE_SIZE - 2 * margin, TILE_SIZE - 2 * margin,
                    )
                    pygame.draw.rect(self.screen, COLORS[PLAYER], player_rect)
                else:
                    # Normal cell
                    color = COLORS.get(cell, COLORS[FLOOR])
                    pygame.draw.rect(self.screen, color, rect)

                    # Draw a yellow dot on uncovered goal cells
                    if cell == GOAL:
                        center = (x + TILE_SIZE // 2, y + TILE_SIZE // 2)
                        pygame.draw.circle(
                            self.screen, COLOR_GOAL_DOT, center, TILE_SIZE // 6
                        )

                # Tile border for visual separation
                pygame.draw.rect(self.screen, COLOR_TILE_BORDER, rect, 1)

        # HUD — text below the grid
        hud_y = len(self.grid) * TILE_SIZE + 10
        moves_text = self.font.render(
            f"Moves: {self.move_count}", True, COLOR_TEXT
        )
        self.screen.blit(moves_text, (10, hud_y))

        controls_text = self.font.render(
            "Arrow keys / WASD to move | U undo | R reset | Q quit",
            True, COLOR_TEXT,
        )
        self.screen.blit(controls_text, (10, hud_y + 30))

    # ------------------------------------------------------------------
    # Grid helpers
    # ------------------------------------------------------------------

    def _get_cell(self, r, c):
        """Return the content of cell (r, c), or WALL if out of bounds.

        This is a safe accessor that treats anything outside the grid as
        a wall, preventing index-out-of-range errors during movement.

        Args:
            r: Row index.
            c: Column index.

        Returns:
            The character at grid[r][c], or WALL if (r, c) is outside
            the grid boundaries.
        """
        if 0 <= r < len(self.grid) and 0 <= c < len(self.grid[0]):
            return self.grid[r][c]
        return WALL

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def move(self, direction):
        """Attempt to move the player one step in the given direction.

        Movement rules:
            - Walls block the player.
            - Boxes can be pushed (delegated to push_box()).
            - If push_box() returns False, the move is cancelled.

        Args:
            direction: One of 'w', 'a', 's', 'd'.
        """
        if direction not in DIRECTIONS:
            return

        dr, dc = DIRECTIONS[direction]
        new_r = self.player_row + dr
        new_c = self.player_col + dc
        target = self._get_cell(new_r, new_c)

        # Walls always block movement
        if target == WALL:
            return

        # Preserve the grid state before attempting to push any boxes
        pre_move_grid = copy.deepcopy(self.grid)

        # If a box is in the way, try to push it
        if target in (BOX, BOX_ON_GOAL):
            if not self.push_box(new_r, new_c, dr, dc):
                return  # push failed — player stays put

        # --- The move is valid if we reach this point ---
        self.history.append((
            pre_move_grid,
            self.player_row,
            self.player_col,
            self.move_count,
        ))

        self.player_row = new_r
        self.player_col = new_c
        self.increment_move_count()

    # ------------------------------------------------------------------
    # Main game loop
    # ------------------------------------------------------------------

    def run(self):
        """Main game loop using pygame for rendering and input.

        Sets up the pygame display, then enters a loop that:
            1. Processes keyboard/window events.
            2. Renders the board.
            3. Checks the win condition.
            4. Caps the frame rate.

        Supported keys:
            Arrow keys / WASD — move up/left/down/right
            U                 — undo last move
            R                 — reset the level
            Q                 — quit the game
        """
        # Calculate window size from the grid dimensions
        num_rows = len(self.grid)
        num_cols = len(self.grid[0])
        window_width = num_cols * TILE_SIZE
        window_height = num_rows * TILE_SIZE + HUD_HEIGHT

        self.screen = pygame.display.set_mode((window_width, window_height))
        pygame.display.set_caption("Sokoban")
        self.font = pygame.font.SysFont(None, 28)
        clock = pygame.time.Clock()

        # Map pygame key constants to direction strings
        key_to_direction = {
            pygame.K_w: "w",    pygame.K_UP: "w",
            pygame.K_a: "a",    pygame.K_LEFT: "a",
            pygame.K_s: "s",    pygame.K_DOWN: "s",
            pygame.K_d: "d",    pygame.K_RIGHT: "d",
        }

        won = False

        while True:
            # --- Event handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        return

                    if event.key == pygame.K_r:
                        self.reset_level()
                        won = False

                    if not won:
                        if event.key in key_to_direction:
                            self.move(key_to_direction[event.key])
                        elif event.key == pygame.K_u:
                            self.undo()

            # --- Render ---
            self.render()

            # --- Win check ---
            if not won and self.check_win():
                won = True

            # --- Win overlay ---
            if won:
                overlay = pygame.Surface(
                    self.screen.get_size(), pygame.SRCALPHA
                )
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))

                win_text = self.font.render(
                    "Congratulations! You solved the puzzle!",
                    True, (255, 255, 100),
                )
                win_rect = win_text.get_rect(center=(
                    window_width // 2, window_height // 2
                ))
                self.screen.blit(win_text, win_rect)

                hint_text = self.font.render(
                    "Press R to reset or Q to quit", True, COLOR_TEXT
                )
                hint_rect = hint_text.get_rect(center=(
                    window_width // 2, window_height // 2 + 36
                ))
                self.screen.blit(hint_text, hint_rect)

            pygame.display.flip()
            clock.tick(FPS)

    # ==================================================================
    # TODO(peer): The five methods below are stubs.  Implement them to
    # complete the game.  Each has a docstring explaining what it should
    # do and hints on how to approach it.
    # ==================================================================

    def push_box(self, box_r, box_c, dr, dc):
        """Push the box at (box_r, box_c) one step in direction (dr, dc).

        A box can only be pushed if the cell behind it — that is, the cell
        at (box_r + dr, box_c + dc) — is FLOOR or GOAL.  It cannot be
        pushed into a wall or another box.

        If the push is valid:
            1. Find the destination cell: (box_r + dr, box_c + dc).
            2. Remove the box from its current cell:
                 - If the cell was BOX_ON_GOAL, set it back to GOAL.
                 - If the cell was BOX, set it back to FLOOR.
            3. Place the box at the destination:
                 - If the destination is GOAL, set it to BOX_ON_GOAL.
                 - If the destination is FLOOR, set it to BOX.
            4. Return True to signal that the push succeeded.

        If the push is invalid, return False without changing anything.

        Args:
            box_r: Row of the box to push.
            box_c: Column of the box to push.
            dr:    Row direction (-1, 0, or 1).
            dc:    Column direction (-1, 0, or 1).

        Returns:
            True if the box was successfully pushed, False otherwise.
        """
        if self._get_cell(box_r + dr, box_c + dc) not in (FLOOR, GOAL):
            return False

        if self._get_cell(box_r, box_c) == BOX:
            self.grid[box_r][box_c] = FLOOR
        elif self._get_cell(box_r, box_c) == BOX_ON_GOAL:
            self.grid[box_r][box_c] = GOAL

        if self._get_cell(box_r + dr, box_c + dc) == FLOOR:
            self.grid[box_r + dr][box_c + dc] = BOX
        elif self._get_cell(box_r + dr, box_c + dc) == GOAL:
            self.grid[box_r + dr][box_c + dc] = BOX_ON_GOAL

        return True

    def check_win(self):
        """Check whether all goals on the board are covered by boxes.

        The puzzle is solved when every goal has a box on it.  In grid
        terms, this means no cell contains GOAL — because a goal with a
        box on it is stored as BOX_ON_GOAL, not GOAL.

        Note: The player's position is tracked separately, so the grid
        cell under the player might be GOAL (player standing on an
        uncovered goal).  That does NOT count as covered.

        Returns:
            True if the puzzle is solved, False otherwise.
        """
        for row in self.grid:
            for cell in row:
                if cell == GOAL:
                    return False
        return True

    def undo(self):
        """Undo the last move by restoring the previous state.

        self.history is a list of snapshots, where each entry is a tuple:
            (grid_copy, player_row, player_col, move_count)

        To implement undo:
            1. If self.history is empty, print a message and return.
            2. Pop the last entry from self.history.
            3. Restore self.grid, self.player_row, self.player_col,
               and self.move_count from the popped values.

        IMPORTANT: For undo to work, you also need to add a line in
        the move() method (at the marked TODO comment) that saves a
        snapshot BEFORE the player position is updated.  Use
        copy.deepcopy(self.grid) when saving the grid to avoid
        aliasing issues.  The copy module is already imported.
        """
        if not self.history:
            print("No moves to undo.")
            return

        snapshot = self.history.pop()
        self.grid, self.player_row, self.player_col, self.move_count = snapshot

    def increment_move_count(self):
        """Increment the move counter by 1.

        Called automatically by move() after each successful move.
        The current count is already displayed by render().

        This is the simplest of the five stubs — just one line!
        """
        self.move_count += 1

    def reset_level(self):
        """Reset the current level to its initial state.

        Restores the grid, player position, move count, and history
        to their original values by re-parsing self.initial_level.
        """
        self.grid, self.player_row, self.player_col = (
            self._parse_level(self.initial_level)
        )
        self.move_count = 0
        self.history = []


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    """Initialize pygame, create a game from LEVEL_1, and run it."""
    pygame.init()
    game = SokobanGame(LEVEL_1)
    game.run()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
