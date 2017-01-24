try:
	from runtime import *
except ImportError, error:
	print "Runtime has fucking failed:", error

block_source = load_image('block.png', colorkey = (0, 0, 0))
grid_source = load_image('grid.png', colorkey = (0, 0, 0))
game_bg = pygame.Surface(screen.get_size())
game_bg.fill((0, 0, 0))

class Block (AnimatedSprite):
	"""
		Blocks are the individual pieces shapes are made of, 
		with always four blocks in one standard tetromino.

		The block object supports copying of its data to other blocks,
		and primarily acts to store block texture and relative position 
		data.
	"""

	def __init__(self, relpos, color, links = [ ], ghost = False, fallen = False):
		self.color = color # Block color.
		self.ghost = ghost # Ghost state.
		self.links = links # Which direction a block is linked to. 0, 1, 2, 3, for L, U, R, D respectively.
		self.set_color(color, ghost)
		super(Block, self).__init__(self.image)
		self.relpos = relpos
		self.fallen = fallen

	def __repr__ (self):
		return "Tetris Block at" + str(self.relpos)

	def set_color (self, color, ghost = False):
		# Determines block graphic based on its links. Refer to block.png in the textures folder.
		# Links can be wrong due to bugs, which are usually safe unless non-naive line clears are used.
		color = (color * 50) + (25 * int(ghost))
		form = 0
		linknum = len(self.links)
		if linknum == 1:
			form += self.links[0] + 1
		elif linknum == 2:
			if 0 in self.links:
				if 1 in self.links:
					form = 5
				elif 2 in self.links:
					form = 6
				elif 3 in self.links:
					form = 10
			elif 1 in self.links:
				if 2 in self.links:
					form = 7
				else:
					form = 8
			else:
				form = 9
		elif linknum == 3:
			if 0 in self.links:
				if 1 in self.links:
					if 2 in self.links:
						form = 11
					else:
						form = 14
				else:
					form = 13
			else:
				form = 12
		self.image = block_source.subsurface(pygame.Rect(color, form * 25, 25, 25))

	def copy (self, block = None, ghost = False):
		# Copy block state onto another. If block to be copied to is empty, create new Block object.
		if block is None:
			newblock = Block(self.relpos, self.color, self.links, ghost)
			return newblock
		else:
			block.color = self.color
			block.relpos = self.relpos
			block.links = self.links
		
class Shape (object):
	"""
		Shape objects are aggregates of four blocks each, and is treated as one independent structure.
		During non-naive line clears, false temporary shapes are created to handle falling of the separate block domains.

		The position will always start at the left middle column, at the second invisible row from the top.
		This position is also the center of the shape's rotation if the shape is T, S, Z, J, or L.

		If I, the position represents the topleft center block of its bounding square. If O, the position 
		represents the bottomleft corner.
	"""

	def __init__(self, form = 0):
		self.pos = [6, 1]
		self.form = form
		self.state = 0

		if form == 0: # I
			self.blocks = [Block([-1, 0], form, [2]), Block([0, 0], form, [0, 2]), Block([1, 0], form, [0, 2]), Block([2, 0], form, [0])]
		elif form == 1: # O
			self.blocks = [Block([0, -1], form, [2, 3]), Block([1, -1], form, [3, 0]), Block([1, 0], form, [0, 1]), Block([0, 0], form, [1, 2])]
		elif form == 2: # T
			self.blocks = [Block([-1, 0], form, [2]), Block([0, -1], form, [3]), Block([1, 0], form, [0]), Block([0, 0], form, [0, 1, 2])]
		elif form == 3: # S
			self.blocks = [Block([-1, 0], form, [2]), Block([0, 0], form, [0, 1]), Block([0, -1], form, [2, 3]), Block([1, -1], form, [0])]
		elif form == 4: # Z
			self.blocks = [Block([-1, -1], form, [2]), Block([0, -1], form, [0, 3]), Block([0, 0], form, [2, 1]), Block([1, 0], form, [0])]
		elif form == 5: # J
			self.blocks = [Block([-1, -1], form, [3]), Block([-1, 0], form, [1, 2]), Block([0, 0], form, [0, 2]), Block([1, 0], form, [0])]
		elif form == 6: # L
			self.blocks = [Block([-1, 0], form, [2]), Block([0, 0], form, [0, 2]), Block([1, 0], form, [0, 1]), Block([1, -1], form, [3])]
		elif form == 7: # Blank
			self.blocks = [ ]

	def __repr__ (self):
		if self.form == 0:
			shapetext = 'I'
		elif self.form == 1:
			shapetext = 'O'
		elif self.form == 2:
			shapetext = 'T'
		elif self.form == 3:
			shapetext = 'S'
		elif self.form == 4:
			shapetext = 'Z'
		elif self.form == 5:
			shapetext = 'J'
		elif self.form == 6:
			shapetext = 'L'
		else:
			shapetext = 'Temporary Aggregate'
		return shapetext + " Tetromino with blocks at: " + str(self.blocks)

	def copy (self, ghost = False):
		# Copy this shape, creating a new Shape object in the process.
		newshape = Shape(self.form)
		newshape.pos = self.pos
		newshape.state = self.state
		newshape.blocks = [ ] 
		for i in range(len(self.blocks)):
			newshape.blocks.append(self.blocks[i].copy(ghost = ghost))
			newshape.blocks[i].set_color(self.blocks[i].color, ghost)
		return newshape

	def copy_to (self, dest, ghost = False):
		# Copy this shape to another shape without creating a new Shape object.
		dest.pos = self.pos
		dest.state = self.state
		for i in range(len(self.blocks)):
			self.blocks[i].copy(dest.blocks[i], ghost)
			dest.blocks[i].set_color(self.blocks[i].color, ghost)

	def rotate (self, angle):
		# SRS implementation of Tetromino rotation. It is done relative to shape.pos unless it's an I.

		# Shape.state tracks current rotation for the wall kick implementation.
		if angle == 90:
			if self.state < 3: self.state += 1 
			else: self.state = 0
		elif angle == -90:
			if self.state > 0: self.state -= 1
			else: self.state = 3
		elif angle == 180 or angle == -180:
			if self.state < 2: self.state += 2
			else: self.state -= 2
		# Actually rotating the shape.
		if self.form != 1: # O shapes don't need to be rotated.
			for block in self.blocks:
				# Center of rotation is different for I shapes.
				block.relpos = [block.relpos[i] - 0.5 if self.form < 1 else block.relpos[i] for i in range(2)]

				# Apply transformation using precalculated rotation matrices.
				if angle == 90:
					tmp = -1 * block.relpos[1], block.relpos[0]
					block.links = [block.links[i] + 1 if block.links[i] < 3 else 0 for i in range(len(block.links))]
				elif angle == -90:
					tmp = block.relpos[1], -1 * block.relpos[0]
					block.links = [block.links[i] - 1 if block.links[i] > 0 else 3 for i in range(len(block.links))]
				elif angle == 180 or angle == -180:
					tmp = -1 * block.relpos[0], -1 * block.relpos[1]
					block.links = [block.links[i] + 2 if block.links[i] < 2 else block.links[i] - 2 for i in range(len(block.links))]
				else: # Just in case the programmer (me) is stupid.
					raise ValueError('Tetrominos can only rotate in increments of 90 degrees.')
				block.set_color(block.color, block.ghost)
				block.relpos = [tmp[i] if self.form > 1 else int(tmp[i] + 0.5) for i in range(2)]

	def translate (self, dpos = (0, 0)):
		# Move the shape relative to its current position.
		self.pos = [self.pos[i] + dpos[i] for i in range(2)]
			
	def display (self, ref = (225, 0), forced = False):
		# Display the shape on the screen relative to the topleft corner of the matrix.
		if forced:
			if self.form < 1:
				ref = (ref[0], ref[1] - 12)
			elif self.form > 1:
				ref = (ref[0] + 12, ref[1])
		for block in self.blocks:
			block.set(topleft = (ref[0] + (block.rect.width * (block.relpos[0] + self.pos[0])), ref[1] + (block.rect.height * (block.relpos[1] + self.pos[1]))))
			if self.pos[1] + block.relpos[1] > 1 or forced:
				block.blit_to(screen)

class Grid (PositionedSurface):
	"""
		The Matrix upon which the game is played. When shapes fall and can no longer be moved, 
		their blocks are stored here. Fallen block colors and links are kept.

		The Grid object extends beyond the visible playing field 2 blocks in every direction, 
		with empty space on the top to spawn new shapes in and invisible blocks on the walls and floor.

		Said invisible blocks mean that the only required checks per frame are collision detection checks.
	"""

	def __init__(self, user):
		super(Grid, self).__init__(grid_source, center = screen.get_rect().center)
		self.user = user
		self.font = pygame.font.SysFont(None, 25)
		self.set_cells()

	def set_cells (self):
		# Sets the Matrix to have nothing but its invisible blocks.
		self.cells = [[Block([i, j], 0, fallen = True) if i < 2 or i > 11 or j > 21 else None for i in range(15)] for j in range(24)]

	def add_garbage (self):
		# Adds a garbage row.
		hole = random.randint(2, 11)
		# Prevent the garbage blocks from clearing themselves.
		garbage = [Block([i, 22], 0, fallen = True) if i < 2 or i > 11 else None if i == hole else Block([i, 22], 7, fallen = True) for i in range(14)]
		for i in range(2, 12):
			links = [ ]
			if i != hole:
				if i != 2 and i != hole + 1:
					links.append(0)
				if i != 11 and i != hole - 1:
					links.append(2)
				garbage[i].links = links
				garbage[i].set_color(7)

		self.cells.insert(22, garbage)
		self.cells.pop(0)

	def flood_fill (self, block_list, index):
		# Recursive flood fill function.
		if self.cells[index[0]][index[1]] is not None and index[0] < 22 and index[1] > 1 and index[1] < 12:
			# Cut block from grid to temporary shape.
			block_list.append(Block([index[1] - 6, index[0] - 1], self.cells[index[0]][index[1]].color, self.cells[index[0]][index[1]].links))
			self.cells[index[0]][index[1]] = None
			# Look at every nearby cell and perform again if valid.
			self.flood_fill(block_list, (index[0], index[1] - 1)) # Left
			self.flood_fill(block_list, (index[0] - 1, index[1])) # Up
			self.flood_fill(block_list, (index[0], index[1] + 1)) # Right
			self.flood_fill(block_list, (index[0] + 1, index[1])) # Down

	def link_fill (self, block_list, index):
		# Recursive flood fill function using the links.
		if self.cells[index[0]][index[1]] is not None and index[0] < 22 and index[1] > 1 and index[1] < 12:
			# Cut block from grid to temporary shape.
			block_list.append(Block([index[1] - 6, index[0] - 1], self.cells[index[0]][index[1]].color, self.cells[index[0]][index[1]].links))
			# Save links to temporary variable before deleting the block.
			oldlinks = self.cells[index[0]][index[1]].links
			self.cells[index[0]][index[1]] = None
			# Check adjacent blocks as indicated by the links.
			if 0 in oldlinks: # Left
				self.link_fill(block_list, [index[0], index[1] - 1])
			if 1 in oldlinks: # Up
				self.link_fill(block_list, [index[0] - 1, index[1]])
			if 2 in oldlinks: # Right
				self.link_fill(block_list, [index[0], index[1] + 1])
			if 3 in oldlinks: # Down
				self.link_fill(block_list, [index[0] + 1, index[1]])

	def clear_lines (self, method, held, next):
		"""
			Clears lines when the free tetromino is cut to the grid.
			method describes the 3 different styles of clearing available:
			0 refers to naive clearing, where floating blocks are left alone.
			1 refers to sticky clearing, where the floating blocks are grouped by those that share sides.
			2 refers to cascade clearing, where the original block groupings are preserved.

			In both sticky and cascade clearing, the groups will fall as if they were free tetrominos, then 
			the lines will be re-evaluated to see if another clear happened.
		"""
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
				full_row = True
				for cell in self.cells[i]:
					if cell is None:
						full_row = False
						break
				# Once a row is detected to be full, clear it.
				if full_row:
					lines_cleared[-1] += 1
					# If a line is full below the indicated base_row, set base_row to that row.
					if i > base_row: base_row = i
					# Don't check for cleared lines and continue the loop if method is naive.
					if method > 0:
						cleared = True
					# Remove the links that point to blocks that will be cleared.
					for j in range(2, 12):
						# Remove upward links from blocks below.
						if self.cells[i + 1][j] is not None and 3 in self.cells[i][j].links:
							self.cells[i + 1][j].links.remove(1)
							self.cells[i + 1][j].set_color(self.cells[i + 1][j].color)
						# Remove downward links from blocks above.
						if self.cells[i - 1][j] is not None and 1 in self.cells[i][j].links:
							self.cells[i - 1][j].links.remove(3)
							self.cells[i - 1][j].set_color(self.cells[i - 1][j].color)
						# Just leave the row empty if the method is sticky or cascade.
						if method > 0:
							self.cells[i][j] = None
					# Splice the old row out and create a new blank row on top if method is naive.
					if method < 1:
						# Delete the old row.
						self.cells.pop(i)
						# Create new blank row at the top.
						self.cells.insert(0, [Block([i, 0], 0, fallen = True) if i < 2 or i > 11 else None for i in range(14)])

			# If the method is naive, then don't continue.
			if method > 0:
				# If a line has been cleared, let the floating blocks fall until they collide with other blocks.
				if cleared:
					tempgrid = [0]
					while len(tempgrid):
						# Tempgrid is the list of all shapes that have not fallen all the way down yet.
						tempgrid = [ ]
						# Set the fallen flag of all those blocks to False, which means they're 'floating'.
						for i in range(21, -1, -1):
							for j in range(2, 12):
								if self.cells[i][j] is not None: self.cells[i][j].fallen = False
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
										tempshape = Shape(7)
										locked = False
										# Cut connected blocks from grid to the shape.
										if method == 1:
											# Perform a blind flood fill if the method is sticky.
											self.flood_fill(tempshape.blocks, (i, j))
										elif method == 2:
											# Perform a flood fill considering which blocks are linked if the method is cascade.
											self.link_fill(tempshape.blocks, (i, j))
											for block in tempshape.blocks:
												# If the block being tested isn't connected to the block below it, then the shape it's a part of is blocked.
												if 3 not in block.links and self.cells[block.relpos[1] + tempshape.pos[1] + 1][block.relpos[0] + tempshape.pos[0]] is not None:
													locked = True
													locked_shapes = True
													# Cut the shape back to the matrix.
													for block in tempshape.blocks:
														self.cells[block.relpos[1] + tempshape.pos[1]][block.relpos[0] + tempshape.pos[0]] = block
													break
										# Add this temprary shape to the list if it's not blocked.
										if not locked:
											tempshapes.append(tempshape)

								# If there is at least one temporary shape created, move them all down one space.
								if len(tempshapes) > 0:
									for shape in tempshapes:
										collision = False
										shape.translate((0, 1))	
										# Test if moving down one space causes a collision.
										for block in shape.blocks:
											if self.cells[block.relpos[1] + shape.pos[1]][block.relpos[0] + shape.pos[0]] is not None:
												collision = True
												# If a collision has occured, test if it collided with a fallen block.
												if self.cells[block.relpos[1] + shape.pos[1]][block.relpos[0] + shape.pos[0]].fallen and not block.fallen:
													for oldblock in shape.blocks:
														oldblock.fallen = True
										if collision:
											# Move it back up one space when a collision has been detected.
											shape.translate((0, -1))
											# If it collided with a fallen block, then the shape has fallen. Copy it back to the matrix.
											if shape.blocks[0].fallen:
												# Uses similar code to Tetris.shape_to_grid()
												for oldblock in shape.blocks:
													self.cells[oldblock.relpos[1] + shape.pos[1]][oldblock.relpos[0] + shape.pos[0]] = Block([oldblock.relpos[0] + shape.pos[0], oldblock.relpos[1] + shape.pos[1]], oldblock.color, oldblock.links, fallen = True)
											# If it either did not collide, or collided with another floating shape, copy it to the tempgrid instead.
											else:
												tempgrid.append(shape.copy())
										else:
											tempgrid.append(shape.copy())

						# Copy all of the tempgrid's shapes back to the matrix.
						if len(tempgrid) > 0:
							for shape in tempgrid:
								# Uses similar code to Tetris.shape_to_grid()
								for oldblock in shape.blocks:
									self.cells[oldblock.relpos[1] + shape.pos[1]][oldblock.relpos[0] + shape.pos[0]] = Block([oldblock.relpos[0] + shape.pos[0], oldblock.relpos[1] + shape.pos[1]], oldblock.color, oldblock.links)
							
							# Display intermediate drops so the user can see the combo.
							pygame.event.pump()
							screen.blit(game_bg, (0, 0))
							for i in range(3):
								next[i].display((-25, 80 + (i * 80)), True)
							if held is not None:
								held.display((475, 80), True)
							self.update()

							score_text = self.font.render(str(int(self.user.score)), 0, (255, 255, 255))
							score_rect = score_text.get_rect(bottomright = (790, 590))
							screen.blit(score_text, score_rect)

							prescore = self.font.render(str(int(self.user.predict_score(lines_cleared))) + '!', 0, (255, 255, 255))
							prescore_rect = prescore.get_rect(bottomright = (790, 560))
							screen.blit(prescore, prescore_rect)

							pygame.display.flip()
							pygame.time.wait(100)

						# If the tempgrid list is empty, that means that all the blocks have fallen. Check if the fallen blocks caused another line clear.
					lines_cleared.append(0)
		if len(lines_cleared) > 1 or lines_cleared[0] > 0:
			self.user.evaluate_clear_score(lines_cleared)
			self.user.combo_ctr += 1
			self.user.current_combo = self.user.combo_factor ** self.user.combo_ctr
		else:
			self.user.current_combo = 1.0
			self.user.combo_ctr = 0

	def update (self):
		# Display the grid background and constituent blocks.
		self.blit_to(screen)
		for i in range(22):
			for j in range(2, 12):
				if self.cells[i][j] is not None:
					block = self.cells[i][j]
					block.relpos = [j, i]
					if i > 1:
						block.set(topleft = (225 + (block.rect.width * block.relpos[0]), (block.rect.height * block.relpos[1])))
						block.blit_to(screen)
