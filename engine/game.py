"Runs the game logic for pyTetris."
try:
	import sys
	import random
	from traceback import print_exception
	import pygame as pg
	import engine.environment as env
	import engine.filehandler as fh
	import engine.menu as menu
	from engine.shapes import (Shape, Grid)
	from engine.sortedcollections import SortedCollection as SC
except ImportError:
	print("A tetrimino fell through the fucking floor:")
	raise

pg.display.set_caption('pyTetris')

class Core:
	"""
	The actual game logic.

	Clear rows of blocks when they fill up by using shapes of
	all different possible arrangements of four blocks!

	Game ends when the stack of blocks reaches the top!
	Grab the highest score!
	"""
	bg = pg.Surface(env.screct.size)
	bg.fill(0x000000)

	def __init__ (self, user, pause_menu, save_menu, loss_menu):
		self.user = user
		self.pause_menu = pause_menu
		self.save_menu = save_menu
		self.loss_menu = loss_menu

		self.font = pg.font.SysFont(None, 25)
		self.theme = env.load_music('tetris.ogg')

		self.grid = Grid(user)
		self.set_data()

	def __str__ (self):
		# Debug info dump.
		return (
			"Game State:\n"
			"Free Shape:\n"+str(self.freeshape)+"\n"
			"Test Shape:\n"+str(self.newshape)+"\n"
			"Ghost Shape:\n"+str(self.ghostshape)+"\n"
			"Held Shape:\n"+str(self.storedshape)+"\n"
			"Grid State:\n"+str(self.grid)+"\n"
		)

	def set_data (self):
		# Initializes the game data.
		self.grid.set_cells()
		self.nextshapes = self.gen_shapelist() # List of next shapes.
		self.freeshape = Shape() # The actual free tetrimino
		self.newshape = Shape() # Potential new position to be checked.
		self.ghostshape = Shape() # Ghost position for hard drop
		self.storedshape = Shape() # Tetrimino currently being held for later use.

		self.clearing = False # Puts the game on hold when clearing loops.
		self.paused = False # Alerts the game to pause.
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

		elif self.user.gametype == 'timed': # Timed mode is faster to get the player rolling.
			self.fall_delay = 10
			self.soft_delay = 1
			self.entry_delay = 10
			self.shift_delay = 8
			self.shift_fdelay = 1

			self.user.timer = 5 * 60 * 1000 # Remaining time in timed mode in milliseconds.
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
		s_list = [Shape(i) for i in range(7)]
		random.shuffle(s_list)
		return s_list

	def set_shape (self, shape):
		# Set the active shape and reset shape-associated flags.
		self.floor_kick = True
		self.hold_lock = False
		if isinstance(shape, Shape):
			self.freeshape = shape
		else:
			self.freeshape = Shape(shape)
		self.newshape = self.freeshape.copy()
		self.ghostshape = self.freeshape.copy(True)
		self.eval_ghost()
		# Test for obstructions. If they exist, the player lost.
		self.eval_block()

	def next_shape (self):
		# Increments the shape list.
		if self.entry_flag:
			self.set_shape(self.nextshapes.pop(0))
			if len(self.nextshapes) < 7:
				self.nextshapes.extend(self.gen_shapelist())

	def hold_shape (self):
		# Holds a tetrimino in storage until retrieved.
		if self.storedshape.form > 6:
			self.storedshape = Shape(
				self.newshape.form if self.entry_flag else self.nextshapes[0].form, 0)
			self.next_shape()
		else:
			# If storage already has a tetrimino, swap with current active one.
			if not self.hold_lock and self.storedshape.form != self.freeshape.form:
				self.hold_lock = True
				if self.entry_flag:
					# You can only swap once per piece and can't swap if it's the same shape as the active piece.
					self.freeshape, self.storedshape = Shape(self.storedshape.form), Shape(self.freeshape.form)
					self.newshape = self.freeshape.copy()
				else:
					# Allow pieces to be swapped during spawn delay.
					self.nextshapes[0], self.storedshape = self.storedshape, self.nextshapes[0]

	def check_collision (self, shape):
		# Check if the shape to be evaluated is intersecting with any other blocks on the grid.
		for pos in shape.poslist:
			if pos[1] < 0:
				# Ideally, it's impossible to get above the grid, but just in case...
				continue
			elif pos[0] < 0 or pos[0] >= len(self.grid[0]) or pos[1] >= len(self.grid):
				# If a block is outside the grid's bounding box, then a collision has occured.
				return True
			elif self.grid[pos[1]][pos[0]] is not None: 
				# If a block would move to an already occupied cell on the grid, then a collision has occured.
				return True
		else: return False

	def eval_input (self):
		# Evaluates player input.
		event = pg.event.poll()
		if ((event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE)
			or not pg.key.get_focused()):
			# Pause game when the user presses the pause key, or when the window loses focus.
			pg.mixer.music.pause()
			self.paused = True

		if event.type == pg.QUIT: # Exits the game.
			self.user.state = 'quit'
		elif event.type == pg.KEYDOWN:
			if event.key == pg.K_LEFT: # Shift left
				self.shift_dir = 'l'
				self.shift_frame = self.shift_delay
				if self.entry_flag:
					self.newshape.translate((-1, 0))
			elif event.key == pg.K_RIGHT: # Shift right
				self.shift_dir = 'r'
				self.shift_frame = self.shift_delay
				if self.entry_flag:
					self.newshape.translate(( 1, 0))
			elif event.key == pg.K_DOWN: # Toggle soft drop
				self.soft_drop = True
				self.soft_pos = self.newshape.pos[1]
			elif event.key == pg.K_LSHIFT: # Hold tetrimino to storage
				self.hold_shape()

			elif self.entry_flag:
				if event.key == pg.K_z or event.key == pg.K_LCTRL: # Rotate CCW
					self.newshape.rotate(False)
					self.wall_kick()
				elif event.key == pg.K_x or event.key == pg.K_UP: # Rotate CW
					self.newshape.rotate(True)
					self.wall_kick()

				elif event.key == pg.K_SPACE: # Hard drop
					self.user.hard_flag = True
					posdif = self.ghostshape.pos[1] - self.freeshape.pos[1]
					self.freeshape.pos = self.ghostshape.pos[:]
					self.eval_fallen(posdif)

			if self.user.debug:
				# Cheats for testing purposes.
				if self.user.gametype == 'arcade' and event.key == pg.K_8:
					self.user.lines_cleared += 50
				if event.key == pg.K_8:
					print("pyTetris has been terminated manually. Please refer to debug log.")
					env.quit(2)
				elif event.key == pg.K_9: # Add garbage line
					self.grid.add_garbage()
					# Prevent intersections.
					if self.check_collision(self.freeshape):
						self.freeshape.translate(( 0,-1))
						self.newshape.translate(( 0,-1))
					self.grid.update()
				elif event.key == pg.K_0: # Clear board
					self.grid.set_cells()

				elif self.entry_flag: # Render custom piece
					if event.key == pg.K_1:
						self.set_shape(0) # I
					elif event.key == pg.K_2:
						self.set_shape(1) # O
					elif event.key == pg.K_3:
						self.set_shape(2) # T
					elif event.key == pg.K_4:
						self.set_shape(3) # S
					elif event.key == pg.K_5:
						self.set_shape(4) # Z
					elif event.key == pg.K_6:
						self.set_shape(5) # J
					elif event.key == pg.K_7:
						self.set_shape(6) # L

		elif event.type == pg.KEYUP:
			if event.key == pg.K_DOWN:
				self.soft_drop = False
			elif ((event.key == pg.K_LEFT and self.shift_dir == 'l')
				or (event.key == pg.K_RIGHT and self.shift_dir == 'r')):
				self.shift_dir = '0'

	def eval_shift (self):
		# Evaluate Delayed Auto-Shifting.
		if self.shift_frame > 1:
			self.shift_frame -= 1
		elif (self.shift_dir == 'l' or self.shift_dir == 'r') and self.entry_flag:
			self.shift_frame = self.shift_fdelay
			if self.shift_dir == 'l':
				self.newshape.translate((-1, 0))
			elif self.shift_dir == 'r':
				self.newshape.translate(( 1, 0))
		# Prevent active tetrimino from sliding into gridblocks.
		if self.check_collision(self.newshape):
			self.newshape.pos = self.freeshape.pos[:]
		else:
			self.freeshape.pos = self.newshape.pos[:]

	def eval_ghost (self):
		# Evaluate the position of the ghost guide.
		self.ghostshape = self.freeshape.copy(True)
		while True:
			self.ghostshape.translate(( 0, 1))
			if self.check_collision(self.ghostshape):
				self.ghostshape.translate(( 0,-1))
				break

	def eval_tspin (self):
		# If a twist hasn't occured after a successful rotation,
		# and the piece is a T, check if it's in a position for a valid T-spin.
		if not self.user.twist_flag and self.freeshape.form == 2:
			cornercount = 0
			if (self.grid
					[self.freeshape.pos[1] - 1]
					[self.freeshape.pos[0] - 1] is not None):
				cornercount += 1
			if (self.grid
					[self.freeshape.pos[1] - 1]
					[self.freeshape.pos[0] + 1] is not None):
				cornercount += 1
			if (self.grid
					[self.freeshape.pos[1] + 1]
					[self.freeshape.pos[0] - 1] is not None):
				cornercount += 1
			if (self.grid
					[self.freeshape.pos[1] + 1]
					[self.freeshape.pos[0] + 1] is not None):
				cornercount += 1
			if cornercount == 3:
				self.user.tspin_flag = True

	def test_kicks (self, poslist):
		# Test four kick positions.
		for pos in poslist:
			# Test if a given relative position will cause a collision.
			if pos[1] >= 0 or (pos[1] < 0 and self.floor_kick):
				# Disable the floor kick flag if the position would make the piece go up.
				if pos[1] < 0: self.floor_kick = False
				# Set the test position to the original position before translating.
				self.newshape.pos = self.freeshape.pos[:]
				self.newshape.translate(pos)
				# Perform the collision check.
				if not self.check_collision(self.newshape):
					break
		else:
			# If none of the kick positions are valid, a twist didn't occur.
			self.user.twist_flag = False
			# Undo the rotation.
			self.newshape = self.freeshape.copy()

	def wall_kick (self):
		# Arika Implementation of wall kicks for I-symmetricity about the y-axis.
		# All else is SRS.
		# The O piece cannot rotate, and therefore cannot be kicked.
		if self.freeshape.form != 1:
			# Check if the inital rotation caused a collision.
			self.user.twist_flag = self.check_collision(self.newshape)
			# Assume a twist will occur, and check which position is valid.
			if self.user.enablekicks and self.user.twist_flag:
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
				if self.user.twist_flag:
					# Wall kicks reset the gravity timer.
					self.grav_frame = 0
				else:
					# If no wall kicks happened, check if this was a T-spin instead.
					self.eval_tspin()
			# Update the active piece.
			self.freeshape = self.newshape.copy()

	def eval_gravity (self):
		# Test if the next gravity tick will cause a collision.
		self.newshape.translate(( 0, 1))
		gravflag = self.check_collision(self.newshape)
		self.newshape.translate(( 0,-1))
		return gravflag

	def eval_fallen (self, posdif):
		# Evaluates what happens to a tetrimino when it has just fallen.
		# Reset DAS if the user has not let go of the key yet.
		if self.shift_frame == 0 and self.shift_dir != '0':
			self.shift_frame = self.shift_delay
		# Evaluate drop score and cut piece to the matrix.
		self.user.eval_drop_score(posdif)
		self.grid.paste_shape(self.freeshape)
		# Check if lines were cleared, and add the number of lines cleared to the total if any.
		self.clearing = True
		self.line_clearer = self.grid.clear_lines()
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
		if self.user.state == 'loss_menu':
			self.grav_frame = 30

	def eval_block (self):
		# If the shape spawns on top of placed blocks, it's game over.
		obstructed = self.check_collision(self.freeshape)
		# If the shape did not spawn on top of blocks, see if it can move.
		if not obstructed:
			trapped = True
			# Test if a line clear would be caused by the shape's initial position.
			# I: XXXX O: OXXO T: XXXO S: XXOO Z: OXXO J: XXXO L: XXXO
			f = self.freeshape.form
			# Horizontal length of second row of the block - 1
			rlen = 3 if f == 0 else 2 if f == 2 or f > 4 else 1
			# Leftmost block
			bcell = 6 if f == 1 or f == 4 else 5
			# If a line could be cleared by the shape's initial position, don't care if it's blocked.
			for i in range(2, 12):
				if (i < bcell or i > bcell + rlen) and self.grid[1][i] is None:
					break
			else: trapped = False
			if trapped: # Can it move down?
				self.newshape.translate(( 0, 1))
				trapped = self.check_collision(self.newshape)
			if trapped: # Can it move right?
				self.newshape.translate(( 1,-1))
				trapped = self.check_collision(self.newshape)
			if trapped: # Can it move left?
				self.newshape.translate((-2, 0))
				trapped = self.check_collision(self.newshape)
			self.newshape.pos = self.freeshape.pos[:]
			# If the shape is blocked and can't clear a line, game over.
			if trapped: self.user.state = 'loss_menu'	
		else: self.user.state = 'loss_menu'

	def eval_loss (self):
		# When a loss occurs, compare current score to scorefile list.
		if self.user.state == 'loss_menu':
			# Determine game type index.
			g = 0 if self.user.gametype == 'arcade' else 1 if self.user.gametype == 'timed' else 2
			with fh.SFH() as sfh:
				# Load scorelist only for that game type.
				scorelist = SC(sfh.decode()[g], key=lambda s: (-s[1], s[3], s[2]))
			# Initialize place pointer, then find out which place it belongs, if any.
			newscore = ['Pajitnov', self.user.score, self.user.lines_cleared, self.user.timer]
			scorelist.insert(newscore)
			i = scorelist.index(newscore)
			if i < 10:
				self.save_menu.render_place(i)
				self.user.state = 'save_menu'
			self.save_menu.loss_bg.blit(env.screen, (0, 0))
			self.loss_menu.render_loss(env.screen)
			pg.mixer.music.fadeout(2500)

	def ramp_arcade (self):
		# Manages the difficulty of arcade mode.
		# Increase the level based on the number of lines cleared, and check if there's a difference.
		self.user.eval_level()
		# Responsible for making the Arcade mode more faster-paced over time.
		self.fall_delay = 45 - (40*self.user.level//180) if self.user.level < 180 else 5
		self.soft_delay = 6 - (5*self.user.level//90) if self.user.level < 90 else 1
		self.entry_delay = 30 - (20*self.user.level//150) if self.user.level < 150 else 10
		self.shift_delay = 25 - (17*self.user.level//120) if self.user.level < 120 else 8
		self.shift_fdelay = 4 - (3*self.user.level//60) if self.user.level < 60 else 1
		# Start periodically spawning garbage lines at level 64.
		if self.user.level >= 64:
			if self.line_frame == 0:
				self.grid.add_garbage()
				# Prevent intersections.
				if self.check_collision(self.freeshape):
					self.freeshape.translate(( 0,-1))
					self.newshape.translate(( 0,-1))
				# Make them spawn faster every 64 levels.
				if self.user.level >= 256:
					self.line_frame = 120
				elif self.user.level >= 192:
					self.line_frame = 180
				elif self.user.level >= 128:
					self.line_frame = 240
				elif self.user.levl >= 64:
					self.line_frame = 300
			else: self.line_frame -= 1

	# Refer to env.render_text()
	render_text = env.render_text

	def display (self):
		# Display relevant stuff.
		lalign = 113
		ralign = 253
		talign = self.grid.rect.y + 177
		spacing = 30
		# Display current game mode.
		self.render_text(self.user.gametype.capitalize() + ' Mode', 0xFFFFFF, midtop=(env.screct.centerx, self.grid.rect.y + 15))
		# Display current score.
		self.render_text('Score:', 0xFFFFFF, topleft=(lalign, talign))
		self.render_text('{}'.format(self.user.score), 0xFFFFFF, topright=(ralign, talign + spacing))
		# Display score from last clear.
		self.render_text('Last Clear:', 0xFFFFFF, topleft=(lalign, talign + spacing * 2))
		if self.clearing:
			self.render_text('{}'.format(self.user.predict_score(False)), 0xFFFFFF, topright=(ralign, talign + spacing * 3))
		else:
			self.render_text('{}'.format(self.user.last_score), 0xFFFFFF, topright=(ralign, talign + spacing * 3))
		# Display total tiles cleared.
		self.render_text('Lines Cleared:', 0xFFFFFF, topleft=(lalign, talign + spacing * 4))
		self.render_text('{}'.format(self.user.lines_cleared), 0xFFFFFF, topright=(ralign, talign + spacing * 5))
		# Display game mode specific values.
		if self.user.gametype == 'arcade':
			self.render_text('Current Level:', 0xFFFFFF, topleft=(lalign, talign + spacing * 6))
			self.render_text('{}'.format(self.user.level), 0xFFFFFF, topright=(ralign, talign + spacing * 7))
		elif self.user.gametype == 'timed':
			self.render_text('Time Left:', 0xFFFFFF, topleft=(lalign, talign + spacing * 6))
			self.render_text(
				'{}:{:02d}:{:02d}'.format(self.user.timer // 60000, self.user.timer//1000 % 60, self.user.timer%1000 // 10),
				0xFFFFFF, topright=(ralign, talign + spacing*7)
			)

		# Display ghost piece.
		if self.user.showghost:
			self.ghostshape.draw()
		# Display active piece.
		if self.entry_flag and not self.clearing:
			self.freeshape.draw()
		# Display three next pieces.
		self.render_text('Up Next:', 0xFFFFFF, topleft=(584, self.grid.rect.y + 60))
		for i in range(3):
			self.nextshapes[i].draw([592, self.grid.rect.y + 126 + (i * 87)], True)
		# Display held piece.
		self.render_text('Held:', 0xFFFFFF, topleft=(162, self.grid.rect.y + 60))
		if self.storedshape is not None:
			self.storedshape.draw([158, self.grid.rect.y + 126], True)

		# Show current fps.
		self.render_text(str(int(round(env.clock.get_fps(), 0))), 0xFFFFFF, bottomright=(env.screct.w - 5, env.screct.h - 5))

	def eval_pause (self):
		# Pause game after evaluating frame.
		if self.paused:
			self.soft_drop = False
			self.shift_dir = '0'
			self.paused = False
			self.pause_menu.set_bg(env.screen)
			self.user.state = 'pause_menu'

	def run (self):
		# Runs the game loop.
		if self.user.resetgame:
			self.set_data()
			self.user.resetgame = False
		# Evaluate inputs and kick if necessary.
		self.eval_input()
		# Evaluate translation.
		self.eval_shift()
		# Skip majority of game code if the lineclearer object is active- aka the Grid.clear_lines() generator.
		if not self.clearing:
			# If the spawn delay isn't active:
			if self.entry_flag:
				# Evaluate ghost tetrimino and display it.
				self.eval_ghost()
				# Set the gravity delay to the appropriate value depending on whether soft drop is active or not.
				self.grav_delay = self.soft_delay if self.soft_drop else self.fall_delay

				# Evaluate gravity.
				if self.eval_gravity(): # If collision will occur due to gravity:
					if self.grav_frame < 29:
						# Use default timer instead of the soft drop timer.
						self.grav_frame += 1
					else:
						# Evaluate dropped piece.
						self.grav_frame = 0
						self.eval_fallen(self.ghostshape.pos[1] - self.soft_pos if self.soft_drop else 0)

				else: # If there won't be gravity collision:
					if self.grav_frame < self.grav_delay - 1:
						self.grav_frame += 1
					else: # Move shape down.
						self.grav_frame = 0
						self.freeshape.translate(( 0, 1))
						self.newshape.translate(( 0, 1))
			# If it is, count down the number of frames until it's time to deactivate it.
			elif self.entry_frame > 1:
				self.entry_frame -= 1
			else:
				self.entry_flag = True
				self.next_shape()
			
		# Evaluate arcade mode difficulty.
		if self.user.gametype == 'arcade':
			self.ramp_arcade()
		# Evaluate timer at the end of the frame.
		self.user.eval_timer(env.clock.get_time())
		# Evaluate special states.
		self.eval_loss()
		self.eval_pause()
		# Display the background.
		env.screen.blit(self.bg, (0, 0))
		# Display and manage the grid.
		self.grid.update()
		# Display everything else.
		self.display()
		# Perform clearing animation during line clears.
		if self.clearing:
			# Both the falling and the animation account for line clear delay.
			if len(self.grid.csprts):
				self.grid.animate_clears()
			else:
				self.clearing = next(self.line_clearer)
		# Refresh screen. There is not enough fast rendering to justify using update()
		pg.display.flip()

def init (argv):
	# Local class definition of the object that will run the game.
	class Game:
		"Runs an instance of pyTetris."
		__slots__ = ()
		# Initialize game objects.
		user = env.user
		# Evaluate command line parameters.
		user.eval_argv(argv)
		play_menu = menu.PlayMenu(user)
		score_menu = menu.HiScoreMenu(user)
		pause_menu = menu.PauseMenu(user)
		save_menu = menu.SaveMenu(user)
		loss_menu = menu.LossMenu(user)
		main_menu = menu.MainMenu(user, score_menu)
		game = Core(user, pause_menu, save_menu, loss_menu)

		def __str__(self):
			# Supposed to dump the game state at the time of calling, but not yet fully implemented.
			return (
				"The game has crashed due to the "+sys.exc_info()[0].__name__+" exception being thrown.\n"
				"Please consult the dump for details, and send it to the developer so that it may be fixed.\n"
				"Debug mode: "+('Active' if self.user.debug else 'Inactive')+".\n\n"
				"User State:\n"+str(self.user)+"\n"
				""+str(eval('self.'+self.user.state))
			)

		def run (self):
			# Run the program loop.
			# User state system allows menu changing to be as simple as running an eval()
			# as long as the state name matches a menu variable name.
			while self.user.state != 'quit':
				env.clock.tick(50)
				try:
					# Catch exceptions that occur during gameplay to make debugging easier.
					eval('self.'+self.user.state+'.run()')
				except:
					# Dump game state to a log, ideally using verbose __str__() methods.
					if self.user.debug:
						# Echo to command line if debug mode is on.
						print(self)
					with open('crashdump.log', 'w') as dump:
						dump.write(str(self))
						print_exception(*sys.exc_info(), file=dump)
					raise
			# Clean up when the program ends.
			env.quit()
	return Game()
