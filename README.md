# pyTetris

pygame implementation of a Tetris clone.

# Pre-repository changelog:

PreDev 0.0: 
- Implemented menu classes.
- Created basic runtime engine for python games.
- Created Block class, representing a struct of a single tetris tile.
- Created Shape class, representing a bunch of Blocks acting as one.
- Created Grid class, allowing blocks from tetriminos to exist in the grid after being dropped.

PreDev 0.1: 
- Fixed bug where the display would not align to the blocks properly.
- Increased block size to 25x25px from 20x20px.
- Implemented naive gravity.

PreDev 0.2: 
- Created invisible wall of blocks in the grid to prevent the necessity of wall and floor collision checks.
- Optimized gravity to only require block collision checks.
- Implemented rudimentary block collision detection between active tetrimino and grid.
- Implemented translation and rotation controls.
- Implemented SRS random tetromino generation system.

PreDev 0.3: 
- Reworked tetrimino evaluation, separating it into rotation, translation, and gravity components.
- Fixed bug where tetriminos moved by shifting or gravity would intersect with other blocks.

InDev 0.1.0: 
- Implemented Akira wall kick table for rotations.
- Implemented Hold function.
- Padded the invisible block wall by one more so the I tetromino did not cause bugs when rotated into wall.

InDev 0.1.1: 
- Implemented ghost tetrimino and hard drop.
- Implemented soft drop.

InDev 0.1.2: 
- Implemented Pause Menu.
- Optimized game code to allow game resets.

InDev 0.1.3: 
- Implemented naive line clear.
- Implemented sticky line clear and added block textures.

InDev 0.1.4:
- Implemented cascade line clear.
- Fixed bug in Menu system that caused the selections to reset every frame.

InDev 0.2.0: 
- Optimized code for Grid class line clear methods, uniting them under a single function.

# Post-repository changelog:

InDev 0.2.1: 
- Fixed bug in line clearing that caused block domains to fall "through" each other when they should not.

InDev 0.2.2: 
- Implemented rudimentary scoring system. 
- Fixed bug in cascade clearing where some block domains did not fall when they should.

InDev 0.2.3: 
- Expanded score system.

InDev 0.2.4: 
- Fixed bug where rotating a piece allowed players to suspend it indefinitely.
- Fixed bug where I piece still caused crashes when wall-kicked from the right side due to block iteration order by padding the right side by one more.
- Optimized code per frame, now Grid.clear_lines() isn't run every frame, and the game doesn't wait for the frame counter to roll over when a piece is dropped. 
- Fixed scoring system bugs.

InDev 0.2.5:
- Implemented proper handling of losing.
- Rebalanced the score values to more closely match standards.
- Implemented Delayed Auto-Shifting.
- Streamlined the running code, making it more readable and more efficient, undoing PreDev 0.3's separation.

InDev 0.2.6:
- Implemented tetrimino spawn delay.
- Allowed DAS to charge during spawn delay.
- Fixed bug that caused ghost piece to lag behind by one frame.

InDev 0.2.7:
- Allowed swapping held piece during spawn delay.
- Fixed bug where piece did not evaluate properly after spawn delay.
- Soft locking time increased to normal locking time.
- Rebalanced tetrises to be more point-worthy and chains less point-worthy.

InDev 0.2.8:
- Fixed bug where pressing hard dropping during spawn delay caused a premature loss.
- Fixed bug where soft drop lock delay did not work as intended.
- Implemented rudimentary Timed mode.
- Fixed a bug where DAS would not charge if the key was held before the old piece was dropped.

InDev 0.2.9:
- Fixed display error during line clear due to outdated code.
- Optimized code for readability (again), especially with regards to score tracking.
- Timed mode is now faster than Free mode in pacing.
- Added up key as quick clockwise rotate shortcut.

# pyTetris Alpha

Alpha 1.0.0:
- Implemented Arcade mode. Levels and rising difficulty rely on the number of lines cleared by the player.
- Implemented Timed mode. Fixed a bug where DAS would cause a piece to be suspended while in contact with another block in this mode.
- The older mode has been renamed Free mode and can be played for casual Tetris.
- Removed redundant display code at shapes.py and replaced it with an optimized display function.
- Updated textures for game.
- Fixed bug where pausing would cause a falling block to not lock.
- Fixed bug where garbage lines would be subject to cascading gravity.
