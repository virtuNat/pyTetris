# [ ] square bracket copy reference, { } curly braces reference
try:
	from menu import *
	from shapes import *
except ImportError, error:
	print "One of the modules fucked up:"
	raise error

class User (object):
	"""
		User object, tracks global game state values, such as
		plot flags, difficulty, game internal state, etc.
	"""

	def __init__ (self):
		self.state = 'main_menu'
		self.gametype = 'arcade'
		self.cleartype = 2

		self.debug = True

		self.drop_score = 1. # The base score added when a block lands.
		self.hard_factor = 1. # The multiplier if a block is hard-dropped.
		self.hard_flag = False # True if the hard_factor is to be used.
		self.line_score = 500. # The base score added when a line is cleared.
		self.line_factor = 0.75 # The added percentage for each line cleared in one drop.
		self.cascade_factor = 1.2 # The multiplier for each set of lines cleared successively. Exponential.
		self.twist_factor = 2.5 # The multiplier if the starting piece was twisted in.
		self.twist_flag = False # True if the tetrimino twisted into place.
		self.combo_ctr = 0 # Current combo number
		self.combo_factor = 1.25 # The multiplier for subsequent drop clears.

		self.current_combo = 1. # The current combo multiplier.

		self.score = 0
		self.last_score = 0

	def add_score (self, value):
		# Shortcut adder.
		self.score += int(value)

	def eval_drop_score (self, posdif = 0):
		# Add score value when piece is dropped.
		if self.state != 'loser':
			if self.hard_flag:
				self.add_score(self.drop_score + (self.hard_factor * posdif))
				self.hard_flag = False
			else:
				self.add_score(self.drop_score + (self.hard_factor * posdif / 2.))

	def predict_score (self, lines):
		# Evaluate clear line combo score value, but don't add it yet.
		if len(lines) > 1 and lines[-1] == 0:
			lines.pop()
		temp_score = 0
		for line in lines:
			temp_score += (self.line_score * line) * ((1 - self.line_factor) + (self.line_factor * line))
		temp_score *= (self.cascade_factor ** (len(lines) - 1))
		if self.twist_flag: return temp_score * self.current_combo * self.twist_factor
		else: return int(temp_score * self.current_combo)

	def evaluate_clear_score (self, lines):
		# Add the clear line score.
		temp_score = self.predict_score(lines)
		self.add_score(temp_score)
		self.last_score = temp_score

class Tetris (object):
	""" 
		The actual game in itself.

		Clear rows of blocks when they fill up by using shapes of 
		all different possible arrangements of four blocks!

		Game ends when the stack of blocks reaches the top!
		Grab the highest score!
	"""

	def __init__(self, user, pause_menu, loss_menu):
		self.user = user
		self.pause_menu = pause_menu
		self.loss_menu = loss_menu

		self.bg = game_bg
		self.font = pygame.font.SysFont(None, 25)

		self.grid = Grid(user)
		self.set_data()

		print "LEFT and RIGHT arrow keys to shift tetrimino left and right."
		print "DOWN arrow key to speed up falling tetrimino."
		print "Z and X keys to rotate tetrimino CW and CCW."
		print "SPACE key to drop tetrimino, and SHIFT to hold tetrimino."
		print "ESCAPE key to pause."

	def set_data (self):
		# Initializes the game data.
		self.grid.set_cells()
		self.nextshapes = self.gen_shapelist() # List of next shapes.
		self.nextshapes.extend(self.gen_shapelist())
		self.freeshape = self.nextshapes.pop(0) # The actual free tetrimino
		self.newshape = self.freeshape.copy() # Potential new position from user command
		self.ghostshape = self.freeshape.copy(ghost = True) # Ghost position for hard drop
		self.storedshape = None # Tetromino currently being held for later use.

		self.paused = False # Alerts the game to pause.
		self.collision = False # Collision flag for wall kicks
		self.ghost_collide = False # Collision flag for ghost shape
		self.floor_kick = True # Can't floor kick if False
		self.soft_drop = False # Tetromino drops faster if True
		self.soft_pos = 21 # The height at which a piece began soft dropping.
		self.hold_lock = False # Can't swap Held pieces if True

		self.normdelay = 30 # Number of frames between the ones where the tetrimino falls by one block.
		self.softdelay = 2 # ^ during soft drop.
		self.entrydelay = 10 # Delay between dropping a piece and spawning a new one.
		self.entryframe = 0 # Frame counter for the above delay.
		self.entryflag = True # True if a piece is currently in play, false if the player is waiting for a new one.

		self.shift_dir = '0' # The current direction the tetrimino is shifting.
		self.shift_delay = 20 # The frame delay between holding the button and auto-shifting.
		self.shift_fdelay = 2 # The frame delay between shifts when auto-shifting.
		self.shift_frame = 0 # The frame counter for auto-shifting.

		self.frame = 0 # Frame counter
		self.delay = self.normdelay # Currently used delay

		self.level = 0 # Current level in arcade mode.
		self.timer = 10 * 3600 # Current timer in timed mode.

	def gen_shapelist (self):
		# Generate a 'bag' of one of each tetrimino shape in random order.
		return random.sample([Shape(i) for i in range(7)], 7)

	def set_shape (self, shape):
		# Set the active shape.
		self.frame = 1
		self.floor_kick = True
		self.hold_lock = False
		if isinstance(shape, Shape):
			self.freeshape = shape
		else:
			self.freeshape = Shape(shape)
		self.newshape = self.freeshape.copy()
		self.ghostshape = self.freeshape.copy(ghost = True)
		# Test for obstructions. If they exist, the player lost.
		self.eval_loss()

	def next_shape (self):
		# Sets the next shape to be the active one, and resets all flags associated with the previous one.
		self.set_shape(self.nextshapes.pop(0))
		if len(self.nextshapes) < 7:
			self.nextshapes.extend(self.gen_shapelist())

	def shape_to_grid (self):
		# Cut the active shape to the grid.
		for oldblock in self.freeshape.blocks:
			self.grid.cells[oldblock.relpos[1] + self.freeshape.pos[1]][oldblock.relpos[0] + self.freeshape.pos[0]] = Block([oldblock.relpos[0] + self.freeshape.pos[0], oldblock.relpos[1] + self.freeshape.pos[1]], oldblock.color, oldblock.links, fallen = True)

	def hold_shape (self):
		# Holds a tetrimino in storage until retrieved.
		if self.entryflag:
			if self.storedshape is None:
				self.storedshape = Shape(self.newshape.form)
				self.next_shape()
			# If storage already has a tetrimino, swap with current active one.
			else:
				# You can only swap once per piece and can't swap if it's the same shape as the active piece.
				if not self.hold_lock and self.storedshape.form != self.freeshape.form:
					self.hold_lock = True
					self.freeshape = Shape(self.storedshape.form)
					self.storedshape = Shape(self.newshape.form)
					self.newshape = self.freeshape.copy()
		else:
			if self.storedshape is None:
				self.storedshape = Shape(self.nextshapes[0].form)
				self.nextshapes.pop(0)
				if len(self.nextshapes) < 7:
					self.nextshapes.extend(self.gen_shapelist())
			else:
				holdform = self.storedshape.form
				self.storedshape = Shape(self.nextshapes[0].form)
				self.nextshapes[0] = Shape(holdform)

	def eval_input (self):
		# Evaluates player input.
		event = pygame.event.poll()
		if event.type == pygame.QUIT:
			self.user.state = 'quit'
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE: # Pause game
				self.paused = True

			elif event.key == pygame.K_LEFT: # Shift left one block
				self.shift_dir = 'l'
				self.shift_frame = self.shift_delay
				if self.entryflag:
					self.newshape.translate((-1, 0))
			elif event.key == pygame.K_RIGHT: # Shift right one block
				self.shift_dir = 'r'
				self.shift_frame = self.shift_delay
				if self.entryflag:
					self.newshape.translate((1, 0))

			elif event.key == pygame.K_LSHIFT: # Hold tetrimino to storage
				self.hold_shape()

			elif self.entryflag:
				if event.key == pygame.K_UP: # Rotate
					self.newshape.rotate(90)
					self.wall_kick()

				elif event.key == pygame.K_DOWN: # Toggle soft drop
					self.soft_drop = True
					self.soft_pos = self.newshape.pos[1]
				elif event.key == pygame.K_SPACE: # Hard drop
					self.user.hard_flag = True
					self.ghostshape.copy_to(self.freeshape)
					self.user.eval_drop_score(self.ghostshape.pos[1] - self.newshape.pos[1]) 
					self.shape_to_grid()
					self.eval_clear()

			if self.user.debug:
				if event.key == pygame.K_9: # Add garbage line
					self.grid.add_garbage()
					self.grid.update()
				elif event.key == pygame.K_0: # Clear board
					self.grid.set_cells()
				
				elif self.entryflag: # Render custom piece
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
		# Evaluate Delayed auto-shifting.
		if self.shift_frame > 0:
			self.shift_frame -= 1
		elif (self.shift_dir == 'l' or self.shift_dir == 'r') and self.entryflag:
			self.shift_frame = self.shift_fdelay
			if self.shift_dir == 'l':
				self.newshape.translate((-1, 0))
			if self.shift_dir == 'r':
				self.newshape.translate((1, 0))

		if self.entryflag:
			# Prevent active tetrimino from sliding into gridblocks.
			for block in self.newshape.blocks:
				if self.collision_test(block, self.newshape):
					self.freeshape.copy_to(self.newshape)
					break
			else:
				self.newshape.copy_to(self.freeshape)

	def eval_ghost (self):
		# Evaluate and display the position of the ghost tetrimino.
		self.freeshape.copy_to(self.ghostshape, ghost = True)
		self.ghost_collide = False
		while not self.ghost_collide:
			self.ghostshape.translate((0, 1))
			for block in self.ghostshape.blocks:
				if self.collision_test(block, self.ghostshape):
					self.ghost_collide = True
					break
		self.ghostshape.translate((0, -1))
		self.ghostshape.display()

	def collision_test (self, block, shape):
		# Shortcut if statement.
		return self.grid.cells[block.relpos[1] + shape.pos[1]][block.relpos[0] + shape.pos[0]] is not None

	def collision_test_kick (self, pos):
		# Test if a given relative position will cause a collision.
		self.collision = False
		self.newshape.pos = self.freeshape.pos
		self.newshape.translate(pos)
		for block in self.newshape.blocks:
			if self.collision_test(block, self.newshape):
				self.collision = True
				break
	
	def wall_kick (self):
		# Akira Implementation of wall kicks for I-symmetricity about the y-axis.
		# All else is SRS.
		self.collision = False
		if self.freeshape.state != self.newshape.state and self.freeshape.form != 1:
			# If the rotation would put the piece in an invalid position:
			for block in self.newshape.blocks:
				if self.collision_test(block, self.newshape):
					self.collision = True
					break
			if self.collision:
				self.user.twist_flag = True
				# If collision occurs on basic rotation, test 4 kick positions.
				if self.freeshape.state == 0:
					if self.newshape.state == 3: # Rotation from spawn to CCW
						if self.newshape.form > 1: # J, L, S, T, Z
							self.collision_test_kick((1, 0))
							if self.collision:
								if self.floor_kick:
									self.floor_kick = False
									self.collision_test_kick((1, -1))
								if self.collision:
									self.collision_test_kick((0, 2))
									if self.collision:
										self.collision_test_kick((1, 2))
						else: # I
							self.collision_test_kick((2, 0))
							if self.collision:
								self.collision_test_kick((-1, 0))
								if self.collision:
									if self.floor_kick:
										self.floor_kick = False
										self.collision_test_kick((-1, -2))
									if self.collision:
										self.collision_test_kick((2, 1))
					elif self.newshape.state == 1: # Rotation from spawn to CW
						if self.newshape.form > 1: # J, L, S, T, Z
							self.collision_test_kick((-1, 0))
							if self.collision:
								if self.floor_kick:
									self.floor_kick = False
									self.collision_test_kick((-1, -1))
								if self.collision:
									self.collision_test_kick((0, 2))
									if self.collision:
										self.collision_test_kick((-1, 2))
						else: # I
							self.collision_test_kick((-2, 0))
							if self.collision:
								self.collision_test_kick((1, 0))
								if self.collision:
									if self.floor_kick:
										self.floor_kick = False
										self.collision_test_kick((1, -2))
									if self.collision:
										self.collision_test_kick((-2, 1))
				elif self.freeshape.state == 1:
					if self.newshape.state == 0: # Rotation from CW to spawn
						if self.newshape.form > 1: # J, L, S, T, Z
							self.collision_test_kick((1, 0))
							if self.collision:
								self.collision_test_kick((1, 1))
								if self.collision:
									if self.floor_kick:
										self.floor_kick = False
										self.collision_test_kick((0, -2))
									if self.collision:
										if self.floor_kick:
											self.floor_kick = False
											self.collision_test_kick((1, -2))
						else: # I
							self.collision_test_kick((2, 0))
							if self.collision:
								self.collision_test_kick((-1, 0))
								if self.collision:
									if self.floor_kick:
										self.floor_kick = False
										self.collision_test_kick((2, -1))
									if self.collision:
										self.collision_test_kick((-1, 2))
					elif self.newshape.state == 2: # Rotation from CW to 180
						if self.newshape.form > 1: # J, L, S, T, Z
							self.collision_test_kick((1, 0))
							if self.collision:
								self.collision_test_kick((1, 1))
								if self.collision:
									if self.floor_kick:
										self.floor_kick = False
										self.collision_test_kick((0, -2))
									if self.collision:
										if self.floor_kick:
											self.floor_kick = False
											self.collision_test_kick((1, -2))
						else: # I
							self.collision_test_kick((-1, 0))
							if self.collision:
								self.collision_test_kick((2, 0))
								if self.collision:
									if self.floor_kick:
										self.floor_kick = False
										self.collision_test_kick((-1, -2))
									if self.collision:
										self.collision_test_kick((2, 1))
				elif self.freeshape.state == 2:
					if self.newshape.state == 1: # Rotation from 180 to CW
						if self.newshape.form > 1: # J, L, S, T, Z
							self.collision_test_kick((-1, 0))
							if self.collision:
								if self.floor_kick:
									self.floor_kick = False
									self.collision_test_kick((-1, -1))
								if self.collision:
									self.collision_test_kick((0, 2))
									if self.collision:
										self.collision_test_kick((-1, 2))
						else: # I
							self.collision_test_kick((-2, 0))
							if self.collision:
								self.collision_test_kick((1, 0))
								if self.collision:
									if self.floor_kick:
										self.floor_kick = False
										self.collision_test_kick((-2, -1))
									if self.collision:
										self.collision_test_kick((1, 1))
					elif self.newshape.state == 3: # Rotation from 180 to CCW
						if self.newshape.form > 1: # J, L, S, T, Z
							self.collision_test_kick((1, 0))
							if self.collision:
								if self.floor_kick:
									self.floor_kick = False
									self.collision_test_kick((1, -1))
								if self.collision:
									self.collision_test_kick((0, 2))
									if self.collision:
										self.collision_test_kick((1, 2))
						else: # I
							self.collision_test_kick((2, 0))
							if self.collision:
								self.collision_test_kick((-1, 0))
								if self.collision:
									if self.floor_kick:
										self.floor_kick = False
										self.collision_test_kick((2, -1))
									if self.collision:
										self.collision_test_kick((-1, 1))
				elif self.freeshape.state == 3:
					if self.newshape.state == 2: # Rotation from CCW to 180
						if self.newshape.form > 1: # J, L, S, T, Z
							self.collision_test_kick((-1, 0))
							if self.collision:
								self.collision_test_kick((-1, 1))
								if self.collision:
									if self.floor_kick:
										self.floor_kick = False
										self.collision_test_kick((0, -2))
									if self.collision:
										if self.floor_kick:
											self.floor_kick = False
											self.collision_test_kick((-1, -2))
						else: # I
							self.collision_test_kick((1, 0))
							if self.collision:
								self.collision_test_kick((-2, 0))
								if self.collision:
									if self.floor_kick:
										self.floor_kick = False
										self.collision_test_kick((1, -2))
									if self.collision:
										self.collision_test_kick((-2, 1))
					elif self.newshape.state == 0: # Rotation from CCW to spawn
						if self.newshape.form > 1: # J, L, S, T, Z
							self.collision_test_kick((-1, 0))
							if self.collision:
								self.collision_test_kick((-1, 1))
								if self.collision:
									if self.floor_kick:
										self.floor_kick = False
										self.collision_test_kick((0, -2))
									if self.collision:
										if self.floor_kick:
											self.floor_kick = False
											self.collision_test_kick((-1, -2))
						else: # I
							self.collision_test_kick((-2, 0))
							if self.collision:
								self.collision_test_kick((1, 0))
								if self.collision:
									if self.floor_kick:
										self.floor_kick = False
										self.collision_test_kick((-2, -1))
									if self.collision:
										self.collision_test_kick((1, 2))
			else: self.user.twist_flag = False
			if self.user.twist_flag: 
				self.frame = 1

			if self.collision: self.freeshape.copy_to(self.newshape)
			else: self.newshape.copy_to(self.freeshape)

	def eval_gravity (self):
		for block in self.newshape.blocks:
			# If collision occurs due to the gravity timer running out:
			if self.collision_test(block, self.newshape):
				# Copy shape to grid.
				self.user.eval_drop_score(self.ghostshape.pos[1] - self.soft_pos if self.soft_drop else 0)
				self.shape_to_grid()
				self.eval_clear()

				if self.soft_drop and self.frame == self.softdelay:
					self.frame = self.normdelay
		else:
			self.newshape.copy_to(self.freeshape)

	def eval_clear (self):
		# Clear lines if a piece dropped.
		self.grid.clear_lines(self.user.cleartype, self.storedshape, self.nextshapes)
		self.grid.update()
		# Reset flags pertaining to dropped state of the tetrimino.
		self.user.twist_flag = False
		self.entryflag = False
		self.entryframe = self.entrydelay

		self.freeshape = Shape(7)
		self.newshape = Shape(7)
		self.ghostshape = Shape(7)

		self.frame = 0
		if self.user.state == 'loser':
			self.frame = 30

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
				self.newshape.translate((0, 1))
				for block in self.newshape.blocks:
					if self.collision_test(block, self.newshape):
						break
				else: trapped = False
				if trapped:
					# Can it move right?
					self.newshape.translate((1, -1))
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
			self.freeshape.copy_to(self.newshape)
		else:
			self.user.state = 'loser'

	def render_text (self, text, color, **pos):
		tsurf = self.font.render(text, 0, color)
		screen.blit(tsurf, tsurf.get_rect(**pos))

	def run (self):
		# Runs the game.

		# Display the background.
		screen.blit(self.bg, (0, 0))
		# Display and manage the grid.
		self.grid.update()

		if not self.entryflag:
			self.entryflag = True
			self.next_shape()

		# Evaluate inputs and kick if necessary.
		self.eval_input()
		# Evaluate translation.
		self.eval_shift()

		if self.entryflag:
			# Evaluate ghost tetrimino and display it.
			self.eval_ghost()

			if self.soft_drop: self.delay = self.softdelay
			else: self.delay = self.normdelay

			if self.frame < self.delay: self.frame += 1
			else: self.frame = 0
			# Evaluate gravity.
			if self.frame == 0:
				self.newshape.translate((0, 1))
				self.eval_gravity()
		elif self.entryframe > 0:
			self.entryframe -= 1

		# Display current score.
		self.render_text(str(self.user.score), (255, 255, 255), bottomright = (790, 590))
		# Display score from last clear.
		self.render_text(str(self.user.last_score) + '!' * self.user.combo_ctr, (255, 255, 255), bottomright = (790, 560))
		# Display relevant shapes.
		if self.entryflag:
			self.freeshape.display()
		for i in range(3):
			self.nextshapes[i].display((475, 80 + (i * 80)), True)
		if self.storedshape is not None:
			self.storedshape.display((-25, 80), True)

		if self.user.state == 'loser':
			self.loss_menu.render_loss()
			self.loss_menu.set_bg(screen)
		# Pause game after evaluating frame.
		if self.paused:
			self.paused = False
			self.pause_menu.set_bg(screen)
			self.user.state = 'paused'

		pygame.display.flip()
