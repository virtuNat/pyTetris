## pyTetris

###### pygame implementation of a Tetris clone.

#### Original Version Features:
- Working keyboard-operated menus.
- Basic grid implemented that uses invisible block padding to emulate wall collision, and a simply (although buggy) line clear system in either naive or sticky methods.
- Collision detection between blocks in the grid, and the blocks in the active tetrimino.
- Rotation and tetrimino generation work according to the SRS guideline.
- The active tetrimino can be held and swapped.
- The active tetrimino has a ghost to aid player move prediction.
- Both soft drop and hard drop can be used to make the active tetrimino fall faster.
- The game can be paused (though not during line clearing).
- The game data can be reset and replayed.

#### Repository starts here:

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
- Updated grid texture.
- Fixed bug where pausing would cause a falling block to not lock.
- Fixed bug where garbage lines would be subject to cascading gravity.

Alpha 1.1.0:
- Rebalanced score values and score calculation to avoid line clear score errors.
- Allowed no-kick T-spins to be rewarded with a bonus score multiplier.
- Rescaled levels in arcade mode to reduce the overall number of lines required to get to maximum level.
- Garbage lines now spawn periodically at level 128, and will spawn faster at level 256. (Previously, they only spawned at level 256)
- Wall kick and Arcade difficulty tables have been reworked for readability.
- Arcade difficulty now scales linearly with level up to its maximum.
- Enabled Left Control to rotate counter-clockwise.
- Optimized PositionedSurface and Grid code, laying groundwork for performance improvements.
- Game now automatically pauses when the window loses focus.
- Added a Tetris theme remix to be played in-game.
- Added a placeholder playing field texture to complement the rudimentary HUD design.

Alpha 1.1.1:
- Minor performance improvement with line-clearing, created an explicit Grid.paste_shape() function for ease.
- Fixed inconsistencies with level assignments in arcade mode.

Alpha 1.1.2:
- Moved to python 3.4 syntax.
- Optimized base class code, creating FreeSprite from PositionedSurface, making it easier to add new features and implement animation via the AnimatedSprite class.
- Fixed a bug arisen from the move that caused a graphical error to occur when clearing lines.

Alpha 1.1.3:
- Fixed a bug where the line clearing would cause an infinite loop on sticky but not cascade clearing.
- Enabled pausing during line clear, turning Grid.clear_lines() into a generator, and optimizing its code in relation to the User object.
- Updated several places where old syntax has become obsolete.
