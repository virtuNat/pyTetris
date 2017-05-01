# [ ] square bracket copy reference, { } curly braces reference
try:
	from menu import *
	from shapes import *
except ImportError as error:
	print("One of the modules fucked up:")
	raise error

class User (object):
	"""
	The User class tracks global game state values, such as
	plot flags, difficulty, game internal state, etc.

	In this case, it tracks tetris difficulty values and handles score data.
	"""

	def __init__ (self):
		# Global state variables.
		self.state = 'main_menu'
		self.gametype = 'free'
		# Eventually will be modifiable in the Options Menu.
		# Default settings are good for Modern Tetris.
		# Retro Tetris would use cleartype 0, enablekicks, showghost, and linktiles False.
		self.cleartype = 2 # Determines line clear type, refer to Grid.clear_lines(). 
		self.enablekicks = True # Determines if wall kicks are allowed.
		self.showghost = True # Determines if the ghost tetrimino will be shown.
		self.linktiles = True # Determines if the blocks will use connected textures.

		self.debug = True
		# Score data.
		self.clear_factor = 2. # The multiplier if the entire matrix was cleared by this piece.

		self.drop_score = 1. # The base score added when a block lands.
		self.dist_factor = 0.6 # The multiplier for every unit distance dropped by a piece in a soft or hard drop.
		self.hard_flag = False # True if the piece was hard-dropped.

		self.line_score = 500. # The base score added when a line is cleared.
		self.line_factor = 0.8 # The added percentage for each line cleared in one drop.
		self.cascade_factor = 1.5 # The multiplier for each set of lines cleared successively. Exponential.

		self.twist_factor = 2.4 # The multiplier if the starting piece was twisted in.
		self.twist_flag = False # True if the tetrimino twisted into place.

		self.tspin_factor = 1.8 # The multiplier if it was a successful T-spin.
		self.tspin_flag = False # True if a T-spin occured.

		self.combo_ctr = 0 # Current combo number
		self.combo_factor = 1.2 # The multiplier for subsequent drop clears.
		self.current_combo = 1. # The current combo multiplier.

		self.reset()

	def reset (self):
		# Reset data when starting a new game.
		self.score = 0 # Score value for the current game.
		self.last_score = 0 # Score value for the last clear.

		self.lines_cleared = 0 # Total number of lines cleared in the game.
		self.level = 1 # Current level in arcade mode.
		self.timer = 0 # How long the game has been playing.

	def add_score (self, value):
		# Shortcut adder.
		self.score += int(value)

	def eval_drop_score (self, posdif = 0):
		# Add score value when piece is dropped.
		if self.state != 'loser':
			if self.hard_flag:
				self.add_score(self.drop_score + (self.dist_factor * posdif))
				self.hard_flag = False
			else:
				self.add_score(self.drop_score + (self.dist_factor * posdif / 3.))

	def predict_score (self, lines, clearflag):
		# Evaluate clear line combo score value, but don't add it yet.
		if len(lines) > 1 and lines[-1] == 0:
			lines.pop()
		temp_score = 0
		# In arcade mode, level boosts score earned by successive line clears.
		_lscore = self.line_score
		if self.gametype == 'arcade': _lscore += self.level * 2.5
		# Calculate base score from number of cascades and number of lines cleared per cascade.
		for line in lines: temp_score += (_lscore * line) * (1 + (self.line_factor * (line - 1)))
		temp_score *= (self.cascade_factor ** (len(lines) - 1)) * self.current_combo
		# Increase score for twists.
		if self.twist_flag: temp_score *= self.twist_factor
		# Increase score for T-spins.
		if self.tspin_flag: temp_score *= self.tspin_factor
		# Increase score for perfect clears.
		if clearflag: temp_score *= self.clear_factor
		if self.gametype == 'timed': temp_score *= float(30 - (self.timer // 10000)) / 10
		return int(temp_score)

	def eval_clear_score (self, lines, clearflag):
		# Add the clear line score.
		self.last_score = self.predict_score(lines, clearflag)
		self.add_score(self.last_score)

	def eval_level (self):
		# Evaluate current arcade level.
		if self.lines_cleared <= 640: # Up to level 64, increment every 10 lines.
			self.level = self.lines_cleared // 10
		elif self.lines_cleared <= 1920: # Up to level 128, increment every 20 lines.
			self.level = 63 + ((self.lines_cleared - 640) // 20)
		elif self.lines_cleared <= 3840: # Up to level 192, increment every 30 lines.
			self.level = 127 + ((self.lines_cleared - 1920) // 30)
		elif self.lines_cleared <= 6400: # Up to level 256, increment every 40 lines.
			self.level = 191 + ((self.lines_cleared - 3840) // 40)
		else: self.level = 256

class Tetris (object):
	""" 
	The actual game in itself.

	Clear rows of blocks when they fill up by using shapes of 
	all different possible arrangements of four blocks!

	Game ends when the stack of blocks reaches the top!
	Grab the highest score!
	"""

	def __init__ (self, user, pause_menu, save_menu, loss_menu):
		self.user = user
		self.pause_menu = pause_menu
		self.save_menu = save_menu
		self.loss_menu = loss_menu

		self.bg = game_bg
		self.font = pygame.font.SysFont(None, 25)
		self.theme = load_music('tetris.ogg')

		self.grid = Grid(user)
		self.grid.game = self
		self.set_data()

		print("LEFT and RIGHT arrow keys to shift tetrimino left and right.")
		print("DOWN arrow key to speed up falling tetrimino.")
		print("Z or LCTRL keys to rotate tetrimino counter-clockwise. ")
		print("X or UP keys to rotate tetrimino clockwise.")
		print("SPACE key to drop tetrimino, and LSHIFT to hold tetrimino.")
		print("ESCAPE key to pause.")

	def set_data (self):
		# Initializes the game data.
		self.grid.set_cells()
		self.nextshapes = self.gen_shapelist() # List of next shapes.
		self.freeshape = self.nextshapes.pop(0) # The actual free tetrimino
		self.newshape = self.freeshape.copy(self.user.linktiles) # Potential new position from user command
		self.ghostshape = self.freeshape.copy(self.user.linktiles, True) # Ghost position for hard drop
		self.storedshape = None # Tetromino currently being held for later use.

		self.paused = False # Alerts the game to pause.
		self.collision = False # Collision flag for wall kicks.
		self.floor_kick = True # Can't floor kick if False.
		self.soft_drop = False # Tetromino drops faster if True.
		self.soft_pos = 21 # The height at which a piece began soft dropping.
		self.hold_lock = False # Can't swap Held pieces if True.

		if self.user.gametype == 'arcade': # Arcade mode starts out rather slow.
			self.fall_delay = 45
			self.soft_delay = 6
			self.entry_delay = 30
			self.shift_delay = 25
			self.shift_fdelay = 4
			self.line_frame = 300 # Frame counter for the number of frames between garbage line additions.

		elif self.user.gametype == 'timed': # Timed mode is faster to induce stress.
			self.fall_delay = 10
			self.soft_delay = 1
			self.entry_delay = 10
			self.shift_delay = 8
			self.shift_fdelay = 1

			self.user.timer = 5 * 60 * 1000 # Remaining time in timed mode.
		else: # Free mode stays at a comfortable pace.
			self.fall_delay = 30 # Number of frames between gravity ticks.
			self.soft_delay = 3 # ^ during soft drop.
			self.entry_delay = 20 # Delay between dropping a piece and spawning a new one.
			self.shift_delay = 20 # The frame delay between holding the button and auto-shifting.
			self.shift_fdelay = 2 # The frame delay between shifts when auto-shifting.

		self.entry_frame = self.entry_delay # Frame counter for the entry delay.
		self.entry_flag = False # True if a piece is currently in play, False if the player is waiting for a new one.

		self.shift_dir = '0' # The current direction the tetrimino is shifting.
		self.shift_frame = 0 # The frame counter for auto-shifting.

		self.grav_frame = 0 # The gravity frame counter.
		self.grav_delay = self.fall_delay # Currently used gravity delay.

	def gen_shapelist (self):
		# Generate a 'bag' of one of each tetrimino shape in random order.
		s_list = [Shape(i, self.user.linktiles) for i in range(7)]
		random.shuffle(s_list)
		return s_list

	def set_shape (self, shape):
		# Set the active shape.
		self.floor_kick = True
		self.hold_lock = False
		if isinstance(shape, Shape):
			self.freeshape = shape
		else:
			self.freeshape = Shape(shape, self.user.linktiles)
		self.newshape = self.freeshape.copy(self.user.linktiles)
		self.ghostshape = self.freeshape.copy(self.user.linktiles, True)
		self.eval_ghost(False)
		# Test for obstructions. If they exist, the player lost.
		self.eval_loss()

	def next_shape (self):
		# Sets the next shape to be the active one, and resets all flags associated with the previous one.
		self.set_shape(self.nextshapes.pop(0))
		if len(self.nextshapes) < 7:
			self.nextshapes.extend(self.gen_shapelist())

	def hold_shape (self):
		# Holds a tetrimino in storage until retrieved.
		if self.entry_flag:
			if self.storedshape is None:
				self.storedshape = Shape(self.newshape.form, self.user.linktiles)
				self.next_shape()
			# If storage already has a tetrimino, swap with current active one.
			else:
				# You can only swap once per piece and can't swap if it's the same shape as the active piece.
				if not self.hold_lock and self.storedshape.form != self.freeshape.form:
					self.hold_lock = True
					self.freeshape = Shape(self.storedshape.form, self.user.linktiles)
					self.storedshape = Shape(self.newshape.form, self.user.linktiles)
					self.newshape = self.freeshape.copy(self.user.linktiles)
		else:
			# Allow pieces to be swapped during spawn delay.
			if self.storedshape is None:
				self.storedshape = Shape(self.nextshapes[0].form, self.user.linktiles)
				self.nextshapes.pop(0)
				if len(self.nextshapes) < 7:
					self.nextshapes.extend(self.gen_shapelist())
			else:
				holdform = self.storedshape.form
				self.storedshape = Shape(self.nextshapes[0].form, self.user.linktiles)
				self.nextshapes[0] = Shape(holdform, self.user.linktiles)

	def eval_input (self):
		# Evaluates player input.
		event = pygame.event.poll()
		if (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE) or not pygame.key.get_focused():
			# Pause game when the user presses the pause key, or when the window loses focus.
			pygame.mixer.music.pause()
			self.paused = True

		if event.type == pygame.QUIT: # Exits the game.
			self.user.state = 'quit'
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_LEFT: # Shift left
				self.shift_dir = 'l'
				self.shift_frame = self.shift_delay
				if self.entry_flag: self.newshape.translate((-1, 0))
			elif event.key == pygame.K_RIGHT: # Shift right
				self.shift_dir = 'r'
				self.shift_frame = self.shift_delay
				if self.entry_flag: self.newshape.translate((1, 0))
			elif event.key == pygame.K_DOWN: # Toggle soft drop
				self.soft_drop = True
				self.soft_pos = self.newshape.pos[1]

			elif event.key == pygame.K_LSHIFT: # Hold tetrimino to storage
				self.hold_shape()

			elif self.entry_flag:
				if event.key == pygame.K_z or event.key == pygame.K_LCTRL: # Rotate CCW
					self.newshape.rotate(False, self.user.linktiles)
					self.wall_kick()
				elif event.key == pygame.K_x or event.key == pygame.K_UP: # Rotate CW
					self.newshape.rotate(True, self.user.linktiles)
					self.wall_kick()
				
				elif event.key == pygame.K_SPACE: # Hard drop
					self.user.hard_flag = True
					self.eval_fallen(self.ghostshape.pos[1] - self.freeshape.pos[1])
				
			if self.user.debug:
				if self.user.gametype == 'arcade' and event.key == pygame.K_8:
					self.user.lines_cleared += 50
				if event.key == pygame.K_9: # Add garbage line
					self.grid.add_garbage()
					self.grid.update()
				elif event.key == pygame.K_0: # Clear board
					self.grid.set_cells()
				
				elif self.entry_flag: # Render custom piece
					if event.key == pygame.K_1:
						self.set_shape(0) # I
					elif event.key == pygame.K_2:
						self.set_shape(1) # O
					elif event.key == pygame.K_3:
						self.set_shape(2) # T
					elif event.key == pygame.K_4:
						self.set_shape(3) # S
					elif event.key == pygame.K_5:
						self.set_shape(4) # Z
					elif event.key == pygame.K_6:
						self.set_shape(5) # J
					elif event.key == pygame.K_7:
						self.set_shape(6) # L
			
		elif event.type == pygame.KEYUP:
			if event.key == pygame.K_DOWN:
				self.soft_drop = False
			elif (event.key == pygame.K_LEFT and self.shift_dir == 'l') or (event.key == pygame.K_RIGHT and self.shift_dir == 'r'):
				self.shift_dir = '0'

	def eval_shift (self):
		# Evaluate Delayed Auto-Shifting.
		if self.shift_frame > 0:
			self.shift_frame -= 1
		elif (self.shift_dir == 'l' or self.shift_dir == 'r') and self.entry_flag:
			self.shift_frame = self.shift_fdelay
			if self.shift_dir == 'l':
				self.newshape.translate((-1, 0))
			if self.shift_dir == 'r':
				self.newshape.translate((1, 0))

		if self.entry_flag:
			# Prevent active tetrimino from sliding into gridblocks.
			for block in self.newshape.blocks:
				if self.collision_test(block, self.newshape):
					self.freeshape.copy_to(self.newshape, self.user.linktiles)
					break
			else:
				self.newshape.copy_to(self.freeshape, self.user.linktiles)

	def eval_ghost (self, show = True):
		# Evaluate and display the position of the ghost tetrimino.
		self.freeshape.copy_to(self.ghostshape, self.user.linktiles, True)
		ghost_collide = False
		while not ghost_collide:
			self.ghostshape.translate((0, 1))
			for block in self.ghostshape.blocks:
				if self.collision_test(block, self.ghostshape):
					ghost_collide = True
					break
		self.ghostshape.translate((0, -1))
		if show and self.user.showghost: self.ghostshape.draw()

	def eval_tspin (self):
		# If a twist hasn't occured after a successful rotation,
		# and the piece is a T, check if it's in a position for a valid T-spin.
		if not self.user.twist_flag and self.freeshape.form == 2:
			cornercount = 0
			if self.grid.cells[self.freeshape.pos[1] - 1][self.freeshape.pos[0] - 1] is not None: cornercount += 1
			if self.grid.cells[self.freeshape.pos[1] - 1][self.freeshape.pos[0] + 1] is not None: cornercount += 1
			if self.grid.cells[self.freeshape.pos[1] + 1][self.freeshape.pos[0] - 1] is not None: cornercount += 1
			if self.grid.cells[self.freeshape.pos[1] + 1][self.freeshape.pos[0] + 1] is not None: cornercount += 1
			if cornercount == 3: self.user.tspin_flag = True

	def collision_test (self, block, shape):
		# Shortcut if statement for collision test loop.
		return self.grid.cells[block.relpos[1] + shape.pos[1]][block.relpos[0] + shape.pos[0]] is not None

	def test_kicks (self, poslist):
		# Test four kick positions.
		for pos in poslist:
			# Test if a given relative position will cause a collision.
			if self.collision and (pos[1] >= 0 or (pos[1] < 0 and self.floor_kick)):
				# Disable the floor kick flag if the position would make the piece go up.
				if pos[1] < 0: self.floor_kick = False
				# Set the test position to the original position before translating.
				self.newshape.pos = self.freeshape.pos
				self.newshape.translate(pos)
				# Collision test.
				for block in self.newshape.blocks:
					if self.collision_test(block, self.newshape):
						self.collision = True
						break
				else:
					self.collision = False
					break
	
	def wall_kick (self):
		# Arika Implementation of wall kicks for I-symmetricity about the y-axis.
		# All else is SRS.
		self.collision = False
		# If there is a state discrepancy between the new position and the actual shape, we've rotated.
		# The O piece cannot rotate, and therefore cannot be kicked.
		if self.freeshape.state != self.newshape.state and self.freeshape.form != 1:
			# If the rotation would put the piece in an invalid position:
			for block in self.newshape.blocks:
				if self.collision_test(block, self.newshape):
					self.collision = True
					break
			if self.user.enablekicks:
				if self.collision:
					self.user.twist_flag = True
					# If collision occurs on basic rotation, test 4 kick positions.
					if self.freeshape.state == 0:
						if self.newshape.state == 3: # Rotation from spawn to CCW
							if self.newshape.form > 1: # J, L, S, T, Z
								self.test_kicks([( 1, 0), ( 1,-1), ( 0, 2), ( 1, 2)])
							else: # I
								self.test_kicks([( 2, 0), (-1, 0), (-1,-2), ( 2, 1)])
						elif self.newshape.state == 1: # Rotation from spawn to CW
							if self.newshape.form > 1: # J, L, S, T, Z
								self.test_kicks([(-1, 0), (-1,-1), ( 0, 2), (-1, 2)])
							else: # I
								self.test_kicks([(-2, 0), ( 1, 0), ( 1,-2), (-2, 1)])
					elif self.freeshape.state == 1:
						if self.newshape.state == 0: # Rotation from CW to spawn
							if self.newshape.form > 1: # J, L, S, T, Z
								self.test_kicks([( 1, 0), ( 1, 1), ( 0,-2), ( 1,-2)])
							else: # I
								self.test_kicks([( 2, 0), (-1, 0), ( 2,-1), (-1, 2)])
						elif self.newshape.state == 2: # Rotation from CW to 180
							if self.newshape.form > 1: # J, L, S, T, Z
								self.test_kicks([( 1, 0), ( 1, 1), ( 0,-2), ( 1,-2)])
							else: # I
								self.test_kicks([(-1, 0), ( 2, 0), (-1,-2), ( 2, 1)])
					elif self.freeshape.state == 2:
						if self.newshape.state == 1: # Rotation from 180 to CW
							if self.newshape.form > 1: # J, L, S, T, Z
								self.test_kicks([(-1, 0), (-1,-1), ( 0, 2), (-1, 2)])
							else: # I
								self.test_kicks([(-2, 0), ( 1, 0), (-2,-1), ( 1, 1)])
						elif self.newshape.state == 3: # Rotation from 180 to CCW
							if self.newshape.form > 1: # J, L, S, T, Z
								self.test_kicks([( 1, 0), ( 1,-1), ( 0, 2), ( 1, 2)])
							else: # I
								self.test_kicks([( 2, 0), (-1, 0), ( 2,-1), (-1, 1)])
					elif self.freeshape.state == 3:
						if self.newshape.state == 2: # Rotation from CCW to 180
							if self.newshape.form > 1: # J, L, S, T, Z
								self.test_kicks([(-1, 0), (-1, 1), ( 0,-2), (-1,-2)])
							else: # I
								self.test_kicks([( 1, 0), (-2, 0), ( 1,-2), (-2, 1)])
						elif self.newshape.state == 0: # Rotation from CCW to spawn
							if self.newshape.form > 1: # J, L, S, T, Z
								self.test_kicks([(-1, 0), (-1, 1), ( 0,-2), (-1,-2)])
							else: # I
								self.test_kicks([(-2, 0), ( 1, 0), (-2,-1), ( 1, 2)])
				else: self.user.twist_flag = False
				if self.user.twist_flag: self.grav_frame = 1

			if self.collision: self.freeshape.copy_to(self.newshape, self.user.linktiles)
			else: 
				self.newshape.copy_to(self.freeshape, self.user.linktiles)
				self.eval_tspin()

	def eval_gravity (self):
		self.newshape.translate((0, 1))
		for block in self.newshape.blocks:
			# If collision occurs due to the gravity timer running out:
			if self.collision_test(block, self.newshape):
				gravflag = True
				break
		else: gravflag = False
		self.newshape.translate((0, -1))
		return gravflag

	def eval_fallen (self, posdif):
		# Evaluates what happens to a tetrimino when it has just fallen.
		if self.user.hard_flag: self.ghostshape.copy_to(self.freeshape, self.user.linktiles)
		# Reset DAS if the user has not let go of the key yet.
		if self.shift_frame == 0 and self.shift_dir != '0':
			self.shift_frame = self.shift_delay
		# Evaluate drop score and cut piece to the matrix.
		self.user.eval_drop_score(posdif)
		self.grid.paste_shape(self.freeshape)
		# Check if lines were cleared, and add the number of lines cleared to the total if any.
		self.user.lines_cleared += sum(self.grid.clear_lines(self.user.cleartype))
		self.grid.update()
		# Reset flags pertaining to dropped state of the tetrimino.
		self.user.twist_flag = False
		self.user.tspin_flag = False
		self.entry_flag = False
		self.entry_frame = self.entry_delay
		# Unset active piece.
		self.freeshape = Shape()
		self.newshape = Shape()
		self.ghostshape = Shape()
		# Prevent a bug where losing would force pieces to spawn.
		self.grav_frame = 0
		if self.user.state == 'loser':
			self.grav_frame = 30

	def eval_loss (self):
		# If the shape spawns on top of placed blocks, it's game over.
		obstructed = False
		for block in self.freeshape.blocks:
			if self.collision_test(block, self.freeshape):
				obstructed = True
				break
		# If the shape did not spawn on top of blocks, see if it can move.
		if not obstructed:
			trapped = True
			# Test if a line clear would be caused by the shape's initial position.
			if self.freeshape.form == 0:
				rlen = 3 # Horizontal length of second row of the block - 1
				bcell = 5 # Leftmost block
			elif self.freeshape.form == 1 or self.freeshape.form == 4:
				rlen = 2
				bcell = 5
			elif self.freeshape.form == 3:
				rlen = 1
				bcell = 5
			else: 
				rlen = 1
				bcell = 6
			# If a line could be cleared by the shape's initial position, don't care if it's blocked.
			for i in range(2, 12):
				if (i < bcell or i > bcell + rlen) and self.grid.cells[1][i] is None:
					break
			else: trapped = False
			if trapped:
				# Can it move down?
				self.newshape.translate(( 0, 1))
				for block in self.newshape.blocks:
					if self.collision_test(block, self.newshape):
						break
				else: trapped = False
			if trapped:
				# Can it move right?
				self.newshape.translate(( 1,-1))
				for block in self.newshape.blocks:
					if self.collision_test(block, self.newshape):
						break
				else: trapped = False
			if trapped:
				# Can it move left?
				self.newshape.translate((-2, 0))
				for block in self.newshape.blocks:
					if self.collision_test(block, self.newshape):
						break
				else: trapped = False
			# If the shape is blocked and can't clear a line, game over.
			if trapped: self.user.state = 'loser'
			self.freeshape.copy_to(self.newshape, self.user.linktiles)
		else:
			self.user.state = 'loser'

	def ramp_arcade (self, oldlevel):
		# Manages the difficulty of arcade mode.

		# Increase the level based on the number of lines cleared, and check if there's a difference.
		self.user.eval_level()
		# Responsible for making the Arcade mode more faster-paced over time.
		if oldlevel < self.user.level:
			# Add garbage on a level up.
			for i in range((self.user.level + 1) // 25): self.grid.add_garbage()
			# Increase game speed based on level.
			self.fall_delay = 45 - (40 * self.user.level // 180) if self.user.level < 180 else 5
			self.soft_delay = 6 - (6 * self.user.level // 90) if self.user.level < 90 else 0
			self.entry_delay = 30 - (20 * self.user.level // 150) if self.user.level < 150 else 10
			self.shift_delay = 25 - (17 * self.user.level // 120) if self.user.level < 120 else 8
			self.shift_fdelay = 4 - (3 * self.user.level // 60) if self.user.level < 60 else 1

		# At half level, periodically spawn garbage lines.
		if self.user.level >= 64:
			if self.line_frame == 0:
				self.grid.add_garbage()
				# Make sure that the piece doesn't go IN the matrix when a garbage line pops up.
				for block in self.freeshape.blocks:
					if self.collision_test(block, self.freeshape): self.freeshape.translate(( 0,-1))
				# At max level, make them spawn faster.
				if self.user.level >= 256: self.line_frame = 120
				elif self.user.level >= 192: self.line_frame = 180
				elif self.user.level >= 128: self.line_frame = 240
				elif self.user.levl >= 64: self.line_frame = 300
			else: self.line_frame -= 1

	def render_text (self, text, color, **pos):
		# Render a message to the screen.
		tsurf = self.font.render(text, 0, color)
		screen.blit(tsurf, tsurf.get_rect(**pos))

	def display (self, clearing = False):
		# Display relevant stuff.
		lalign = 113
		ralign = 253
		talign = self.grid.rect.top + 177
		spacing = 30
		# Display current game mode.
		self.render_text(self.user.gametype.capitalize() + ' Mode', (255, 255, 255), midtop = (s_rect.centerx, self.grid.rect.top + 15))
		# Display current score.
		self.render_text('Score:', (255, 255, 255), topleft = (lalign, talign))
		self.render_text('{}'.format(self.user.score), (255, 255, 255), topright = (ralign, talign + spacing))
		# Display score from last clear.
		self.render_text('Last Clear:', (255, 255, 255), topleft = (lalign, talign + spacing * 2))
		self.render_text('{}'.format(self.user.last_score), (255, 255, 255), topright = (ralign, talign + spacing * 3))
		# Display total tiles cleared.
		self.render_text('Lines Cleared:', (255, 255, 255), topleft = (lalign, talign + spacing * 4))
		self.render_text('{}'.format(self.user.lines_cleared), (255, 255, 255), topright = (ralign, talign + spacing * 5))
		# Display game mode specific values.
		if self.user.gametype == 'arcade':
			self.render_text('Current Level:', (255, 255, 255), topleft = (lalign, talign + spacing * 6))
			self.render_text('{}'.format(self.user.level), (255, 255, 255), topright = (ralign, talign + spacing * 7))
		elif self.user.gametype == 'timed':
			self.render_text('Time Left:', (255, 255, 255), topleft = (lalign, talign + spacing * 6))
			self.render_text('{}:{:02d}:{:02d}'.format(self.user.timer // 60000, self.user.timer // 1000 % 60, self.user.timer % 1000 // 10), (255, 255, 255), topright = (ralign, talign + spacing * 7))
		
		# Display active piece.
		if self.entry_flag and not clearing: self.freeshape.draw()
		# Display three next pieces.
		self.render_text('Up Next:', (255, 255, 255), topleft = (584, self.grid.rect.top + 60))
		for i in range(3):
			self.nextshapes[i].draw([592, self.grid.rect.top + 126 + (i * 87)], True)
		# Display held piece.
		self.render_text('Held:', (255, 255, 255), topleft = (162, self.grid.rect.top + 60))
		if self.storedshape is not None:
			self.storedshape.draw([158, self.grid.rect.top + 126], True)

	def run (self):
		# Runs the game loop.

		# Evaluate arcade mode difficulty before any calculations with the active piece are done to avoid bugs.
		if self.user.gametype == 'arcade':
			# Evaluate current arcade level.
			self.ramp_arcade(self.user.level)
		
		# Display the background.
		screen.blit(self.bg, (0, 0))
		# Display and manage the grid.
		self.grid.update()

		# Evaluate inputs and kick if necessary.
		self.eval_input()
		# Evaluate translation.
		self.eval_shift()
		# If the spawn delay isn't active:
		if self.entry_flag:
			# Evaluate ghost tetrimino and display it.
			self.eval_ghost()
			# Set the gravity delay to the appropriate value depending on whether soft drop is active or not.
			if self.soft_drop: self.grav_delay = self.soft_delay
			else: self.grav_delay = self.fall_delay

			# Evaluate gravity.
			if self.eval_gravity(): # If collision will occur due to gravity:
				if self.grav_frame < self.fall_delay: self.grav_frame += 1 # Use default timer instead of the soft drop timer.
				else: # Evaluate dropped piece.
					self.grav_frame = 0
					self.eval_fallen(self.ghostshape.pos[1] - self.soft_pos if self.soft_drop else 0)

			else: # If there won't be gravity collision:
				if self.grav_frame < self.grav_delay: self.grav_frame += 1
				else: # Move shape down.
					self.grav_frame = 0
					self.newshape.translate((0, 1))
		# If it is, count down the number of frames until it's time to deactivate it.
		elif self.entry_frame > 0:
			self.entry_frame -= 1
		else:
			self.entry_flag = True
			self.next_shape()

		# Evaluate timer at the end of the frame.
		if self.user.gametype == 'timed':
			# Evaluate the timer in timed mode.
			if self.user.timer > 0:
				self.user.timer -= clock.get_time()
			else:
				self.user.timer = 0
				self.user.state = 'loser'
		else:
			# Increment timer for non-timed modes so it could be appended to the high score.
			self.user.timer += clock.get_time()
		# Display heads-up information.
		self.display()

		if self.user.state == 'loser':
			if self.user.gametype == 'arcade': g = 0
			elif self.user.gametype == 'timed': g = 1
			elif self.user.gametype == 'free': g = 2

			_scorelist = decode_scores()[g]
			_i = 10
			for i in range(9, -1, -1):
				if _scorelist[i][1] < self.user.score:
					_i = i
				elif _scorelist[i][1] == self.user.score and _scorelist[i][2] >= self.user.lines_cleared:
					_i = i
					if _scorelist[i][2] == self.user.lines_cleared and _scorelist[i][3] >= self.user.timer:
						_i = i
			if _i < 10:
				self.save_menu.render_place(_i)
				self.user.state = 'save_scores'

			self.loss_menu.render_loss()
			self.loss_menu.set_bg(screen)
			pygame.mixer.music.fadeout(2500)
		# Pause game after evaluating frame.
		if self.paused:
			self.soft_drop = False
			self.shift_dir = '0'
			self.paused = False
			self.pause_menu.set_bg(screen)
			self.user.state = 'paused'
		# Refresh screen.
		pygame.display.flip()
