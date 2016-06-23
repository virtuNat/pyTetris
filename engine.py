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

class Tetris (object):
	""" 
		The actual game in itself.

		Clear rows of blocks when they fill up by using shapes of 
		all different possible arrangements of four blocks!

		Game ends when the stack of blocks reaches the top!
		Grab the highest score!
	"""

	def __init__(self, user, pause_menu):
		self.user = user
		self.pause_menu = pause_menu

		self.bg = pygame.Surface(screen.get_size())
		self.bg.fill((0, 0, 0))

		self.grid = Grid()
		self.set_data()

		print "LEFT and RIGHT arrow keys to shift tetromino left and right."
		print "DOWN arrow key to speed up falling tetromino."
		print "Z and X keys to rotate tetromino CW and CCW."
		print "SPACE key to drop tetromino, and SHIFT to hold tetromino."
		print "ESCAPE key to pause."

	def set_data (self):
		# Initializes the game data.
		self.grid.set_cells()
		self.nextshapes = self.generate_shapes() # List of next shapes.
		self.nextshapes.extend(self.generate_shapes())
		self.freeshape = self.nextshapes.pop(0) # The actual free tetromino
		self.newshape = self.freeshape.copy() # Potential new position from user command
		self.ghostshape = self.freeshape.copy(ghost = True) # Ghost position for hard drop
		self.storedshape = None # Tetromino currently being held for later use.

		self.paused = False # Alerts the game to pause.
		self.collision = False # Collision flag for wall kicks
		self.ghost_collide = False # Collision flag for ghost shape
		self.floor_kick = True # Can't floor kick if False
		self.soft_drop = False # Tetromino drops faster if True
		self.hold_lock = False # Can't swap Held pieces if True

		self.normdelay = 30 # Number of frames between the ones where the tetromino falls by one block.
		self.softdelay = self.normdelay // 15 # ^ during soft drop.

		self.frame = 0 # Frame counter
		self.delay = self.normdelay # Currently used delay

	def generate_shapes (self):
		# Generate a 'bag' of one of each tetromino shape in random order.
		shape_list = range(7)
		gen_list = [ ]
		for i in range(7):
			gen_list.append(Shape(shape_list.pop(random.randint(0, len(shape_list) - 1))))
		return gen_list

	def set_shape (self, form):
		# Gives the player a certain shape when debug mode is active.
		pass

	def next_shape (self):
		# Sets the next shape to be the active one, and resets all flags associated with the previous one.
		self.floor_kick = True
		self.hold_lock = False
		self.freeshape = self.nextshapes.pop(0)
		self.newshape = self.freeshape.copy()
		self.ghostshape = self.freeshape.copy(ghost = True)
		if len(self.nextshapes) < 7:
			self.nextshapes.extend(self.generate_shapes())

	def shape_to_grid (self):
		# Cut the free shape to the grid, then generate a new one.
		for oldblock in self.freeshape.blocks:
			self.grid.cells[oldblock.relpos[1] + self.freeshape.pos[1]][oldblock.relpos[0] + self.freeshape.pos[0]] = Block([oldblock.relpos[0] + self.freeshape.pos[0], oldblock.relpos[1] + self.freeshape.pos[1]], oldblock.color, oldblock.links)
		self.next_shape()

	def hold_shape (self):
		# Holds a tetromino in storage until retrieved.
		if self.storedshape is None:
			self.storedshape = Shape(self.newshape.form)
			self.next_shape()

		else:
		# If storage already has a tetromino, swap with current active one.
			if not self.hold_lock:
				self.hold_lock = True
				self.freeshape = Shape(self.storedshape.form)
				self.storedshape = Shape(self.newshape.form)
				self.newshape = self.freeshape.copy()

	def eval_input_rot (self):
		# Evaluates the rotational part of the player input, as well as the general events.
		event = pygame.event.poll()
		if event.type == pygame.QUIT:
			self.user.state = 'quit'
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_z: # Rotate CCW
				self.newshape.rotate(-90)
			elif event.key == pygame.K_x: # Rotate CW
				self.newshape.rotate(90)
			elif event.key == pygame.K_LSHIFT: # Hold tetromino to storage
				self.hold_shape()
			elif event.key == pygame.K_ESCAPE: # Pause game
				self.paused = True
		return event

	def eval_input_move (self, event):
		# Evaluates the translational part of the player input.
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_LEFT: # Shift left one block
				self.newshape.translate((-1, 0))
			elif event.key == pygame.K_RIGHT: # Shift right one block
				self.newshape.translate((1, 0))
			elif event.key == pygame.K_DOWN: # Toggle soft drop
				self.soft_drop = True
			elif event.key == pygame.K_SPACE: # Hard drop
				self.ghostshape.copy_to(self.freeshape)
				self.shape_to_grid()
			return event.key
		elif event.type == pygame.KEYUP:
			if event.key == pygame.K_DOWN:
				self.soft_drop = False
			return event.key
		else: return None

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
			if self.collision:
				self.freeshape.copy_to(self.newshape)
			else:
				self.newshape.copy_to(self.freeshape)
			self.frame = 1
	
	def slide_collision (self, key):
		# Prevents free tetromino from sliding into gridblocks.
		for block in self.newshape.blocks:
			if self.collision_test(block, self.newshape):
				if key == pygame.K_LEFT or key == pygame.K_RIGHT:
					self.freeshape.copy_to(self.newshape)
					break
		else:
			self.newshape.copy_to(self.freeshape)

	def gravity_collision (self):
		# Separate check during falling period.
		for block in self.newshape.blocks:
			# If collision occurs due to the gravity timer running out:
			if self.collision_test(block, self.newshape):
				# Copy shape to grid and clear lines that fill.
				self.shape_to_grid()
				self.grid.clear_lines(self.user.cleartype, self.storedshape, self.nextshapes)
				break
		else:
			self.newshape.copy_to(self.freeshape)

	def calculate_ghost (self):
		# Calculate position of ghost tetromino.
		self.ghost_collide = False
		while not self.ghost_collide:
			self.ghostshape.translate((0, 1))
			for block in self.ghostshape.blocks:
				if self.collision_test(block, self.ghostshape):
					self.ghost_collide = True
					break
		self.ghostshape.translate((0, -1))
		
	def run (self):
		# Runs the game.

		# Display the background.
		screen.blit(self.bg, (0, 0))
		# Display and manage the grid.
		self.grid.update()
		# Evaluate rotations and kick if necessary.
		event = self.eval_input_rot()
		self.wall_kick()
		# Evaluate ghost tetromino and display it.
		self.freeshape.copy_to(self.ghostshape, ghost = True)
		self.calculate_ghost()
		self.ghostshape.display()
		# Evaluate translations.
		self.slide_collision(self.eval_input_move(event))		

		if self.soft_drop:
			self.delay = self.softdelay
		else:
			self.delay = self.normdelay
		if self.frame < self.delay:
			self.frame += 1
		else:
			self.frame = 0
		if self.frame == 0:
			self.newshape.translate((0, 1))
		# Evaluate gravity and clear filled lines.
		self.gravity_collision()
		# Display relevant shapes
		self.freeshape.display()
		for i in range(3):
			self.nextshapes[i].display((-25, 80 + (i * 80)), True)
		if self.storedshape is not None:
			self.storedshape.display((475, 80), True)
		# Pause game after evaluating frame.
		if self.paused:
			self.paused = False
			self.pause_menu.set_bg(screen)
			self.user.state = 'paused'
		pygame.display.flip()
		