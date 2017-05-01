# Code for the tetris blocks, imported by the engine.
try:
	from runtime import *
except ImportError as error:
	print("Runtime has fucking failed:", error)

block_source = load_image('tileset.png')
grid_source = load_image('display.png', colorkey = (0, 0, 0))
grid_rect = grid_source.get_rect(midbottom = (s_rect.centerx, s_rect.bottom - 20))
game_bg = pygame.Surface(screen.get_size())
game_bg.fill((0, 0, 0))

class Block (FreeSprite):
	"""
	Blocks are the individual pieces that make up tetriminos and the matrix grid.

	The block object supports copying of its data to other blocks.
	"""

	def __init__(self, relpos, color, links = [ ], linkrule = True, ghost = False, fallen = False):
		self.relpos = relpos # Position of the block relative to a predefined point on the grid, or the "center" of the shape.
		self.color = color # Block color.
		self.links = links # Which direction a block is linked to. 0, 1, 2, 3, for L, U, R, D respectively.
		self.ghost = ghost # True if this is a ghost block, and will use a ghost texture.
		self.fallen = fallen # Used by the line clear function.
		self.update(color, linkrule, ghost)
		super().__init__(self.image)

	def __repr__ (self):
		return "Tetris Block at" + str(self.relpos)

	def copy (self, block = None, linkrule = True, ghost = False):
		# Create new Block object that is the same as this one.
		if block is None:
			newblock = Block(self.relpos, self.color, self.links, linkrule, ghost)
			return newblock
		else:
			block.color = self.color
			block.relpos = self.relpos
			block.links = self.links
			block.update(self.color, linkrule, ghost)

	def update (self, color, linkrule = True, ghost = False):
		# Evaluate the graphic to be used. Not much else to update in Block Sprites.
		color = (color * 50) + (25 * int(ghost))
		linknum = len(self.links)
		if linkrule:
			if linknum == 0: form = 0
			elif linknum == 1: form = self.links[0] + 1
			elif linknum == 2:
				if 0 in self.links:
					if 1 in self.links: form = 5
					elif 2 in self.links: form = 6
					elif 3 in self.links: form = 10
				elif 1 in self.links:
					if 2 in self.links: form = 7
					else: form = 8
				else: form = 9
			elif linknum == 3:
				if 0 in self.links:
					if 1 in self.links:
						if 2 in self.links: form = 11
						else: form = 14
					else: form = 13
				else: form = 12
			else: raise IndexError('Having more than three links on a block does not a tetrimino make.')
		else: form = 0
		self.image = block_source.subsurface(pygame.Rect(color, form * 25, 25, 25))
		if ghost: self.image.set_alpha(191)

class Shape (FreeGroup):
	"""
	Shape objects are groups of usually four blocks each, and is treated as one independent structure.
	During non-naive line clears, false temporary shapes are created to handle falling of the separate block domains.

	The position will always start at the left middle column, at the second invisible row from the top.
	This position is also the center of the shape's rotation if the shape is T, S, Z, J, or L.

	If I, the position represents the topleft center block of its bounding square. If O, the position 
	represents the bottomleft corner. 

	If this is a temporary aggregate of blocks during clears, the position is used as a reference point for translation.
	"""
	def __init__ (self, form = 7, linkrule = True):
		super().__init__()
		self.pos = [6, 1] # Center of rotation.
		self.form = form # Tetrimino shape.
		self.state = 0 # Current rotation relative to spawn rotation.

		if form == 0: # I
			self.add([Block([-1, 0], form, [2], linkrule), Block([0, 0], form, [0, 2], linkrule), Block([1, 0], form, [0, 2], linkrule), Block([2, 0], form, [0], linkrule)])
		elif form == 1: # O
			self.add([Block([0, -1], form, [2, 3], linkrule), Block([1, -1], form, [3, 0], linkrule), Block([1, 0], form, [0, 1], linkrule), Block([0, 0], form, [1, 2], linkrule)])
		elif form == 2: # T
			self.add([Block([-1, 0], form, [2], linkrule), Block([0, -1], form, [3], linkrule), Block([1, 0], form, [0], linkrule), Block([0, 0], form, [0, 1, 2], linkrule)])
		elif form == 3: # S
			self.add([Block([-1, 0], form, [2], linkrule), Block([0, 0], form, [0, 1], linkrule), Block([0, -1], form, [2, 3], linkrule), Block([1, -1], form, [0], linkrule)])
		elif form == 4: # Z
			self.add([Block([-1, -1], form, [2], linkrule), Block([0, -1], form, [0, 3], linkrule), Block([0, 0], form, [2, 1], linkrule), Block([1, 0], form, [0], linkrule)])
		elif form == 5: # J
			self.add([Block([-1, -1], form, [3], linkrule), Block([-1, 0], form, [1, 2], linkrule), Block([0, 0], form, [0, 2], linkrule), Block([1, 0], form, [0], linkrule)])
		elif form == 6: # L
			self.add([Block([-1, 0], form, [2], linkrule), Block([0, 0], form, [0, 2], linkrule), Block([1, 0], form, [0, 1], linkrule), Block([1, -1], form, [3], linkrule)])

	def __getattr__ (self, name):
		if name == 'blocks':
			# Explicit reference to the list of blocks contained in this group.
			return [block for block in self]
		elif name == 'poslist':
			# List of grid coordinates for the blocks' true positions.
			return [[self.pos[i] + block.relpos[i] for i in range(2)] for block in self]

	def __repr__ (self):
		if self.form == 0: shapetext = 'I'
		elif self.form == 1: shapetext = 'O'
		elif self.form == 2: shapetext = 'T'
		elif self.form == 3: shapetext = 'S'
		elif self.form == 4: shapetext = 'Z'
		elif self.form == 5: shapetext = 'J'
		elif self.form == 6: shapetext = 'L'
		else: shapetext = 'Temporary Aggregate'
		return shapetext + " Tetrimino with blocks at: " + repr(self.blocks)

	def copy (self, linkrule = True, ghost = False):
		# Copy this shape, creating a new Shape object in the process.
		dest = Shape()
		dest.form = self.form
		dest.pos = self.pos
		dest.state = self.state
		for block in self: dest.add(Block(block.relpos, self.form, block.links, linkrule, ghost))
		return dest

	def copy_to (self, dest, linkrule = True, ghost = False):
		# In-place version of Shape.copy().
		dest.form = self.form
		dest.pos = self.pos
		dest.state = self.state
		# The destination needs to match the number of Blocks on the source.
		if len(dest) != len(self): 
			print(len(dest), len(self))
			raise IndexError('A mistake in copying?')
		for i in range(len(self)): self.blocks[i].copy(dest.blocks[i], linkrule, ghost)

	def rotate (self, clockwise, linkrule = True):
		# SRS implementation of Tetrimino rotation. It is done relative to shape.pos unless it's an I.
		# If clockwise attribute is True, the rotation is as named. Otherwise it's counter-clockwise.
		# Shape.state tracks current orientation for the wall kick implementation.
		if clockwise:
			if self.state < 3: self.state += 1 
			else: self.state = 0
		else:
			if self.state > 0: self.state -= 1
			else: self.state = 3
		# Actually rotating the shape.
		if self.form != 1: # O shapes don't need to be rotated.
			for block in self:
				# Center of rotation is different for I shapes.
				block.relpos = [block.relpos[i] - 0.5 if self.form < 1 else block.relpos[i] for i in range(2)]
				# Apply transformation using precalculated rotation matrices.
				if clockwise:
					tmp = -1 * block.relpos[1], block.relpos[0]
					block.links = [block.links[i] + 1 if block.links[i] < 3 else 0 for i in range(len(block.links))]
				else:
					tmp = block.relpos[1], -1 * block.relpos[0]
					block.links = [block.links[i] - 1 if block.links[i] > 0 else 3 for i in range(len(block.links))]
				block.update(block.color, linkrule, block.ghost)
				block.relpos = [int(tmp[i] + 0.5) if self.form < 1 else tmp[i] for i in range(2)]

	def translate (self, disp):
		# Move the tetrimino given a displacement.
		self.pos = [self.pos[i] + disp[i] for i in range(2)]

	def set (self, anchor = None, forced = False):
		# Similar to FreeSprite.set(), it fixes the rects of the component blocks in proper arrangement given an anchor.
		# The anchor is the coordinate of the topleft pixel of the tile represented in self.pos.
		if anchor is None:
			anchor = [225 + self.pos[0] * 25, 10 + self.pos[1] * 25]
		elif forced:
			if self.form < 1:
				anchor[1] -= 12
			elif self.form > 1:
				anchor[0] += 12
		for block in self: block.set(topleft = (anchor[0] + block.relpos[0] * block.rect.width, anchor[1] + block.relpos[1] * block.rect.height))
			
	def draw (self, anchor = None, forced = False):
		# Draw the tetrimino to the screen.
		self.set(anchor, forced)
		for block in self:
			if self.pos[1] + block.relpos[1] > 1 or forced:
				block.draw(screen)

	def update (self, linkrule = True):
		# Update the textures of this tetrimino.
		for block in self: block.update(block.color, linkrule, block.ghost)

class Grid (AnimatedSprite):
	"""
		The Matrix upon which the game is played. When shapes fall and can no longer be moved, 
		their blocks are stored here. Fallen block colors and links are kept.

		The Grid object extends beyond the visible playing field 2 blocks in every direction, 
		with empty space on the top to spawn new shapes in and invisible blocks on the walls and floor.

		Said invisible blocks mean that the only required checks per frame are collision detection checks.
	"""

	def __init__(self, user):
		super().__init__(grid_source, grid_rect)
		self.user = user
		self.set_cells()

	def set_cells (self):
		# Sets the Matrix to have nothing but the buffer blocks.
		self.cells = [[Block([i, j], 0, fallen = True) if i < 2 or i > 11 or j > 21 else None for i in range(15)] for j in range(24)]

	def add_garbage (self):
		# Adds a garbage row.
		hole = random.randint(2, 11)
		garbage = [Block([i, 22], 0, fallen = True) if i < 2 or i > 11 else None if i == hole else Block([i, 22], 7, fallen = True) for i in range(15)]
		# Link up the garbage blocks.
		for i in range(2, 12):
			links = [ ]
			if i != hole:
				if i != 2 and i != hole + 1:
					links.append(0)
				if i != 11 and i != hole - 1:
					links.append(2)
				garbage[i].links = links
				garbage[i].update(7, self.user.linktiles)

		self.cells.insert(22, garbage)
		self.cells.pop(0)
		self.update()

	def paste_shape (self, shape):
		# Paste a shape to this grid.
		for i in range(len(shape)):
			self.cells[shape.poslist[i][1]][shape.poslist[i][0]] = shape.blocks[i]

	def flood_fill (self, t_shape, index, linkrule):
		# Recursive blind flood fill function.
		if self.cells[index[0]][index[1]] is not None and index[0] < 22 and index[1] > 1 and index[1] < 12:
			# Cut block from grid to temporary shape.
			t_shape.add(Block([index[1] - 6, index[0] - 1], self.cells[index[0]][index[1]].color, self.cells[index[0]][index[1]].links, linkrule))
			self.cells[index[0]][index[1]] = None
			# Look at every nearby cell and perform again if valid.
			self.flood_fill(t_shape, (index[0], index[1] - 1), linkrule) # Left
			self.flood_fill(t_shape, (index[0] - 1, index[1]), linkrule) # Up
			self.flood_fill(t_shape, (index[0], index[1] + 1), linkrule) # Right
			self.flood_fill(t_shape, (index[0] + 1, index[1]), linkrule) # Down

	def link_fill (self, t_shape, index, linkrule):
		# Recursive flood fill function using the links.
		if self.cells[index[0]][index[1]] is not None and index[0] < 22 and index[1] > 1 and index[1] < 12:
			# Cut block from grid to temporary shape.
			t_shape.add(Block([index[1] - 6, index[0] - 1], self.cells[index[0]][index[1]].color, self.cells[index[0]][index[1]].links, linkrule))
			for block in t_shape: print(block.color)
			# Save links to temporary variable before deleting the block.
			oldlinks = self.cells[index[0]][index[1]].links
			self.cells[index[0]][index[1]] = None
			# Check adjacent blocks as indicated by the links.
			if 0 in oldlinks: # Left
				self.link_fill(t_shape, [index[0], index[1] - 1], linkrule)
			if 1 in oldlinks: # Up
				self.link_fill(t_shape, [index[0] - 1, index[1]], linkrule)
			if 2 in oldlinks: # Right
				self.link_fill(t_shape, [index[0], index[1] + 1], linkrule)
			if 3 in oldlinks: # Down
				self.link_fill(t_shape, [index[0] + 1, index[1]], linkrule)
			self.cells[index[0]][index[1]] = None

	def clear_lines (self, method):
		"""
			Clears lines when the free tetrimino is pasted to the grid.
			method describes the 3 different styles of clearing available:
			0 refers to naive clearing, where floating blocks are left alone. Used in old Tetris games.
			1 refers to sticky clearing, where the floating blocks are grouped by those that share sides.
			2 refers to cascade clearing, where the original block groupings are preserved.

			In both sticky and cascade clearing, the groups will fall as if they were still active, then 
			the lines will be re-evaluated to see if another clear happened.
		"""
		# Track how many lines are cleared per chain.
		lines_cleared = [0]

		# Initialize the cleared flag to enter the while loop.
		cleared = True
		while cleared:
			# Set the cleared flag to False to represent no lines being cleared yet.
			cleared = False	
			# Set base_row, which is the lowest row a line clear occurs in, to the top row.
			base_row = 0
			# Test if there is a full row, checking upwards, then clear all of them.
			for i in range(21, -1, -1):
				# There is a full row if and only if none of the cells are empty.
				for j in range(2, 12):
					if self.cells[i][j] is None:
						full_row = False
						break
				else: full_row = True
				# Once a row is detected to be full, clear it.
				if full_row:
					# Increment the cleared lines counter.
					lines_cleared[-1] += 1
					# A line was cleared.
					cleared = True
					# If a garbage row is being cleared, the method is always naive for that row only.
					for j in range(2, 4):
						if self.cells[i][j].color == 7:
							garbage = True
							break
					else: garbage = False
					# If a line is full below the indicated base_row, set base_row to that row.
					if i > base_row: base_row = i
					# Remove the links that point to blocks that will be cleared.
					for j in range(2, 12):
						# Remove upward links from blocks below.
						if self.cells[i + 1][j] is not None and 3 in self.cells[i][j].links:
							self.cells[i + 1][j].links.remove(1)
							self.cells[i + 1][j].update(self.cells[i + 1][j].color, self.user.linktiles)
						# Remove downward links from blocks above.
						if self.cells[i - 1][j] is not None and 1 in self.cells[i][j].links:
							self.cells[i - 1][j].links.remove(3)
							self.cells[i - 1][j].update(self.cells[i - 1][j].color, self.user.linktiles)
						# Just leave the row empty if the method is sticky or cascade.
						if method > 0:
							self.cells[i][j] = None
					# Splice the old row out and create a new blank row on top if method is naive or when clearing a garbage row.
					if method < 1 or garbage:
						# Delete the old row.
						self.cells.pop(i)
						# Create new blank row at the top.
						self.cells.insert(0, [Block([i, 0], 0, fallen = True) if i < 2 or i > 11 else None for i in range(15)])
						# Force the game to look through all the rows again to avoid skipping lines.
						break

			# If the method is naive, then don't continue.
			if method > 0:
				# If a line has been cleared, let the floating blocks fall until they collide with other blocks.
				if cleared:
					tempgrid = [0]
					while len(tempgrid):
						# Tempgrid is the list of all shapes that have not fallen all the way down yet.
						tempgrid = [ ]
						# Set the fallen flag of all blocks above and one row below to False, which means they're 'floating'.
						for i in range(base_row + 1, -1, -1):
							for j in range(2, 12):
								if self.cells[i][j] is not None and self.cells[i][j].color != 7: self.cells[i][j].fallen = False
						# For each row, cut a set of temporary shapes from it to allow to fall.
						locked_shapes = True
						while locked_shapes:
							for i in range(21, -1, -1):
								# locked_shapes is True when one of the shapes in the row is blocked from falling by another shape.
								locked_shapes = False
								tempshapes = [ ]
								for j in range(2, 12):
									if self.cells[i][j] is not None and not self.cells[i][j].fallen:
										# Create new blank temporary shape.
										tempshape = Shape()
										# Cut connected blocks from grid to the shape.
										if method == 1:
											# Perform a blind flood fill if the method is sticky.
											self.flood_fill(tempshape, (i, j), self.user.linktiles)
											# Add this temprary shape to the list.
											tempshapes.append(tempshape)
										elif method == 2:
											# Perform a flood fill considering which blocks are linked if the method is cascade.
											self.link_fill(tempshape, (i, j), self.user.linktiles)
											for block in tempshape:
												# If the block being tested isn't connected to the block below it, then the shape it's a part of is blocked.
												if 3 not in block.links and self.cells[block.relpos[1] + 2][block.relpos[0] + 6] is not None:
													locked_shapes = True
													# Cut the shape back to the matrix.
													self.paste_shape(tempshape)
													break
											# Add this temprary shape to the list if it's not blocked.
											else: tempshapes.append(tempshape)

								# If there is at least one temporary shape created, move them all down one space.
								if len(tempshapes) > 0:
									for shape in tempshapes:
										collision = False
										shape.translate((0, 1))	
										# Test if moving down one space causes a collision.
										for block in shape:
											if self.cells[block.relpos[1] + shape.pos[1]][block.relpos[0] + shape.pos[0]] is not None:
												collision = True
												# If a collision has occured, test if it collided with a fallen block.
												if self.cells[block.relpos[1] + shape.pos[1]][block.relpos[0] + shape.pos[0]].fallen and not block.fallen:
													for oldblock in shape:
														oldblock.fallen = True
										if collision:
											# Move it back up one space when a collision has been detected.
											shape.translate((0, -1))
											# If it collided with a fallen block, then the shape has fallen. Copy it back to the matrix.
											if shape.blocks[0].fallen:
												self.paste_shape(shape)
											# If it either did not collide, or collided with another floating shape, copy it to the tempgrid instead.
											else:
												tempgrid.append(shape.copy(self.user.linktiles))
										else:
											tempgrid.append(shape.copy(self.user.linktiles))

						# Copy all of the tempgrid's shapes back to the matrix.
						if len(tempgrid) > 0:
							for shape in tempgrid:
								self.paste_shape(shape)
							
							# Display intermediate drops so the user can see the combo.
							# Note: The game will not respond to input during this time.
							clock.tick(15)
							pygame.event.pump()
							screen.blit(game_bg, (0, 0))
							self.update()
							self.game.display(True)
							pygame.display.flip()

					# If the tempgrid list is empty, that means that all the blocks have fallen. Check if the fallen blocks caused another line clear.
					lines_cleared.append(0)

		if len(lines_cleared) > 1 or lines_cleared[0] > 0:
			# Determine if the board was cleared.
			for i in range(2, 12):
				if self.cells[21][i] is not None:
					clearflag = False
					break
			else: clearflag = True
			# Evaluate combo.
			self.user.eval_clear_score(lines_cleared, clearflag)
			self.user.combo_ctr += 1
			self.user.current_combo = self.user.combo_factor ** self.user.combo_ctr
		else: 
			# If no lines were cleared, break combo.
			self.user.current_combo = 1.0
			self.user.combo_ctr = 0
		return lines_cleared

	def update (self):
		# Display the grid background and constituent blocks.
		self.blit_to(screen)
		for i in range(22):
			for j in range(2, 12):
				if self.cells[i][j] is not None:
					block = self.cells[i][j]
					block.relpos = [j, i]
					if i > 1:
						block.set(bottomleft = (self.rect.centerx + block.rect.width * (block.relpos[0] - 7), self.rect.bottom - 20 + block.rect.height * (block.relpos[1] - 21)))
						block.blit_to(screen)
