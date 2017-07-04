# pyTetris
A project meant to serve as a way for me to learn how to make a game using the pygame module.
This is intended to be a Tetris clone.

### Controls:
LEFT and RIGHT arrow keys to shift tetrimino left and right.
DOWN arrow key to speed up falling tetrimino.
Z or LCTRL keys to rotate tetrimino counter-clockwise. 
X or UP keys to rotate tetrimino clockwise.
SPACE key to drop tetrimino, and LSHIFT to hold tetrimino.
ESCAPE key to pause.

### Feature Tracker:
- (Done) Grid collision detection and piece shifting.
- (Done) SRS implementation of rotation and spawn logic.
- (Done) Symmetric SRS implementation of wall kicks.
- (Done) A ghost to predict where the piece will fall.
- (Done) Both soft and hard drop methods to rush the piece falling.
- (Minor Issue) Delayed Auto Shifting, and a spawn delay.
- (Done) Line clear in naive, sticky, and cascade methods.
- (Minor Issue) Score tracking system and a way to save and view high scores.
- (Minor Issue) Arcade and Timed modes of play.
- (Incomplete) Keyboard controlled menus, including a pause menu.
- (Incomplete) Sound effects and background music.
- (Incomplete) Art for all game textures, menus, and the logo.
- (Unimplemented) Options menu that allows changing of gameplay, aesthetic, and sound volume.

### Issue Tracker:
- A bug occurs when the player holds either the shift left or shift right keys to "stick" the active piece against a wall or the grid blocks will cause it to fall slower.
- The score system has a weird bug that causes it to oversize certain cascade scores in arcade and free mode.

#### Current Version: 1.1.7

Let me know if there are any other problems!
