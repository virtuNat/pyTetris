# pyTetris

pygame implementation of a Tetris clone.

# Pre-repository changelog:

InDev 0.0.0: Implemented basic Menu system.
InDev 0.0.1: Created Block and Shape classes.
InDev 0.0.2: Created Grid class and fixed alignment of the block squares.
InDev 0.0.3: Increased block size to 25x25px from 20x20px, and gave blocks the ability to fall down. Blocks settle improperly.
InDev 0.0.4: Created invisible wall of blocks in the grid to prevent the necessity of wall and floor collision checks.
InDev 0.0.5: Implemented working block collision detection between free shape and grid.
InDev 0.0.6: Implemented SRS random tetromino generation system.
InDev 0.0.7: Fixed tetromino evaluation, separating it into rotation, translation, and gravity components.
InDev 0.0.8: Implemented collision detection checks for translation and gravity, allowing proper settling of blocks.
InDev 0.1.0: Implemented Akira wall kick table for rotations, and padded the invisible block wall by one more so the I tetromino did not cause bugs. Now playable, but losing was guaranteed.
InDev 0.1.1: Implemented ghost tetrominos to view where the free tetromino will settle. Implemented hard drop and soft drop as well.
InDev 0.1.2: Implemented Pause Menu and let the game reset if the user returned to the main menu before playing again (without quitting the game).
InDev 0.1.3: Implemented naive line clear.
InDev 0.1.4: Implemented sticky line clear and added block textures.
InDev 0.1.5: Implemented cascade line clear, game is now functionally playable.
InDev 0.2.0: Optimized code for Grid class line clear methods.
