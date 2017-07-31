"Contains class definitions for objects that handle pyTetris block logic."
try:
	import random
	import pygame as pg
	import environment as env
except ImportError:
	print("Are the blocks fucking made of soap?:")
	raise

class Block (env.FreeSprite):
	"""
	Blocks are the individual pieces that make up tetriminos and the matrix grid.

	The block object supports copying of its data to other blocks.
	"""
	block_src = env.load_image('tileset.png')

	def __init__(self, relpos, color, links=[], linkrule=True, ghost=False, fallen=False):
		super().__init__(self.block_src, (0, 0, 25, 25))
		self.relpos = relpos # Position of the block relative to a predefined point on the grid, or the "center" of the shape.
		self.color = color # Block color.
		self.links = links # Which direction a block is linked to. 0, 1, 2, 3, for L, U, R, D respectively.
		self.fallen = fallen # Used by the line clear function.
		self.update(color, linkrule, ghost)

	def __str__ (self):
		# Debug info that is easy to read.
		return "Tetris Block at" + str(self.relpos)

	def __repr__ (self):
		# eval() usable expression to create a block similar to this.
		return "Block("+repr(self.relpos)+", "+repr(self.color)+", "+repr(self.links)+")"

	def copy (self, linkrule=True, ghost=False):
		# Create new Block object that is the same as this one.
		return Block(self.relpos, self.color, self.links, linkrule, ghost)

	def update (self, color, linkrule=True, ghost=False):
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
		self.cliprect.topleft = (color, form * 25)
		# if ghost: self.image.set_alpha(191)

class Shape (env.FreeGroup):
	"""
	Shape objects are groups of usually four blocks each, and is treated as one independent structure.
	During non-naive line clears, false temporary shapes are created to handle falling of the separate block domains.

	The position will always start at the left middle column, at the second invisible row from the top.
	This position is also the center of the shape's rotation if the shape is T, S, Z, J, or L.

	If I, the position represents the topleft center block of its bounding square. If O, the position
	represents the bottomleft corner.

	If this is a temporary aggregate of blocks during clears, the position is used as a reference point for translation.
	"""
	def __init__ (self, form=7, state=0, pos=[6, 1], linkrule=True, ghost=False):
		super().__init__()
		self.pos = pos # Center of rotation.
		self.form = form # Tetrimino shape.
		self.state = state # Current rotation relative to spawn rotation.
		self.ghost = ghost # Does this shape use ghost textures?
		if form == 0: # I
			self.add([
				Block([-1, 0], form, [2], linkrule),
				Block([ 0, 0], form, [0, 2], linkrule),
				Block([ 1, 0], form, [0, 2], linkrule),
				Block([ 2, 0], form, [0], linkrule)])
		elif form == 1: # O
			self.add([
				Block([ 0,-1], form, [2, 3], linkrule),
				Block([ 1,-1], form, [3, 0], linkrule),
				Block([ 1, 0], form, [0, 1], linkrule),
				Block([ 0, 0], form, [1, 2], linkrule)])
		elif form == 2: # T
			self.add([
				Block([-1, 0], form, [2], linkrule),
				Block([ 0,-1], form, [3], linkrule),
				Block([ 1, 0], form, [0], linkrule),
				Block([ 0, 0], form, [0, 1, 2], linkrule)])
		elif form == 3: # S
			self.add([
				Block([-1, 0], form, [2], linkrule),
				Block([ 0, 0], form, [0, 1], linkrule),
				Block([ 0,-1], form, [2, 3], linkrule),
				Block([ 1,-1], form, [0], linkrule)])
		elif form == 4: # Z
			self.add([
				Block([-1,-1], form, [2], linkrule),
				Block([ 0,-1], form, [0, 3], linkrule),
				Block([ 0, 0], form, [2, 1], linkrule),
				Block([ 1, 0], form, [0], linkrule)])
		elif form == 5: # J
			self.add([
				Block([-1,-1], form, [3], linkrule),
				Block([-1, 0], form, [1, 2], linkrule),
				Block([ 0, 0], form, [0, 2], linkrule),
				Block([ 1, 0], form, [0], linkrule)])
		elif form == 6: # L
			self.add([
				Block([-1, 0], form, [2], linkrule),
				Block([ 0, 0], form, [0, 2], linkrule),
				Block([ 1, 0], form, [0, 1], linkrule),
				Block([ 1,-1], form, [3], linkrule)])

	def __getattr__ (self, name):
		if name == 'blocks':
			# Explicit reference to the list of blocks contained in this group.
			return [block for block in self]
		elif name == 'poslist':
			# List of grid coordinates for the blocks' true positions.
			return [[self.pos[i] + block.relpos[i] for i in range(2)] for block in self]

	def __str__ (self):
		# Debug info that is easy to read.
		shapetext = 'IOTSZJL'[self.form] if self.form < 7 else 'Temporary Aggregate'
		return shapetext + " Tetrimino with blocks at: " + repr(self.poslist)

	def __repr__ (self):
		# eval() usable expression to create a similar object.
		return "Shape(form="+str(self.form)+", state="+str(self.state)+", pos="+str(self.pos)+", ghost="+str(self.ghost)+")"

	def __hash__ (self):
		# Prevent __hash__ from returning None, which will cause a number of problems.
		return object.__hash__(self)

	def __eq__ (self, other):
		# Rich comparison method for debugging purposes.
		if isinstance(other, Shape):
			if self.form < 7 and other.form < 7:
				return (self.form, self.shape, self.pos, self.blocks) == (other.form, other.shape, other.pos, other.blocks)
			else: raise ValueError('Ambiguous shapes cannot be compared!')
		else: raise TypeError(other.__class__.__name__+' cannot be compared to a Shape object!')

	def copy (self, linkrule=True, ghost=False):
		# Copy this shape, creating a new Shape object in the process.
		# Effectively a deep copy.
		dest = Shape(self.form, self.state, self.pos, ghost)
		dest.empty()
		for block in self: dest.add(block.copy(linkrule, ghost))
		return dest

	def rotate (self, clockwise, linkrule=True):
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
					block.links = [link + 1 if link < 3 else 0 for link in block.links]
				else:
					tmp = block.relpos[1], -1 * block.relpos[0]
					block.links = [link - 1 if link > 0 else 3 for link in block.links]
				block.update(block.color, linkrule, self.ghost)
				block.relpos = [int(tmp[i] + 0.5) if self.form < 1 else tmp[i] for i in range(2)]

	def translate (self, disp):
		# Move the tetrimino given a displacement.
		self.pos = [self.pos[i] + disp[i] for i in range(2)]

	def set (self, anchor=None, forced=False):
		# Similar to env.FreeSprite.set(), it fixes the rects of the component blocks in proper arrangement given an anchor.
		# The anchor is the coordinate of the topleft pixel of the tile represented in self.pos.
		if anchor is None:
			anchor = [225 + self.pos[0] * 25, 10 + self.pos[1] * 25]
		elif forced:
			if self.form < 1:
				anchor[1] -= 12
			elif self.form > 1:
				anchor[0] += 12
		for block in self: 
			block.set(topleft=(anchor[0] + block.relpos[0] * block.rect.w, anchor[1] + block.relpos[1] * block.rect.h))
			
	def draw (self, anchor=None, forced=False):
		# Draw the tetrimino to the screen.
		self.set(anchor, forced)
		for block in self:
			if self.pos[1] + block.relpos[1] > 1 or forced:
				block.draw(env.screen)

	def update (self, linkrule=True):
		# Update the textures of this tetrimino.
		for block in self: block.update(block.color, linkrule, self.ghost)

class ClearSprite (env.AnimatedSprite):
	"Sprite that performs the clearing animation."
	src = env.load_image('clear.png', colorkey=0xFF00FF)

	def __init__(self, **anchors):
		super().__init__(pg.Surface((250, 25)), cliprect=(0, 0, 25, 25), **anchors)
		self.image.set_colorkey(0xFF00FF)
		# Due to the way env.AnimatedSprite.animate() works, change frames when the total sheet frame count changes.
		self.frames = 6

	def draw (self, surf=env.screen):
		# Somewhat cheaty due to the rudimentary graphics, will probably fix later.
		self.image.fill(0xFF00FF)
		for i in range(10): self.image.blit(self.src, (i * 25, 0), self.cliprect)
		surf.blit(self.image, self.rect)

class Grid (env.AnimatedSprite):
	"""
	The Matrix upon which the game is played. When shapes fall and can no longer be moved,
	their blocks are stored here. Fallen block colors and links are kept.

	The Grid object extends beyond the visible playing field 2 blocks in every direction,
	with empty space on the top to spawn new shapes in and invisible blocks on the walls and floor.

	Said invisible blocks mean that the only required checks per frame are collision detection checks.
	"""
	image = env.load_image('display.png', colorkey=0x000000)
	rect = image.get_rect(midbottom=(env.screct.centerx, env.screct.bottom - 20))

	def __init__(self, user):
		super().__init__(self.image, self.rect)
		self.user = user
		self.csprts = [ ]
		self.set_cells()

	def __repr__ (self):
		return "<Grid sprite with "+str(sum([sum([self[row][col] is not None for col in range(2, 12)]) for row in range(21)]))+" occupied cells.>"

	def __getitem__ (self, key):
		# Alias to the __getitem__ method of this object's 2d list.
		return self.cells.__getitem__(key)

	def set_cells (self):
		# Sets the Matrix to have nothing but the buffer blocks.
		self.cells = [[None if 2 <= i <= 11 and j <= 21 else Block([i, j], 7, fallen=True) for i in range(15)] for j in range(24)]

	def add_garbage (self):
		# Adds a garbage row.
		hole = random.randint(2, 11)
		garbage = [None if i == hole else Block([i, 22], 7, fallen=True) for i in range(15)]
		# Link up the garbage blocks.
		for i, block in enumerate(garbage):
			# For some reason this will not work with a list comprehension.
			links = [ ]
			if 2 <= i <= 11 and i != hole:
				if i != 2 and i != hole + 1:
					links.append(0)
				if i != 11 and i != hole - 1:
					links.append(2)
				block.links = links
				block.update(7, self.user.linktiles)
		self.cells.insert(22, garbage)
		self.cells.pop(0)
		self.update()

	def paste_shape (self, shape):
		# Paste a shape to this grid.
		for pos, block in zip(shape.poslist, shape.blocks):
			self[pos[1]][pos[0]] = block

	def is_full_row (self, row):
		# Returns True if a given row is full of blocks.
		# There is a full row if and only if none of the cells are empty.
		for col in range(2, 12):
			if self[row][col] is None:
				return False
		else: return True

	def is_garbage_row (self, row):
		# Returns True if a (presumably full) row contains garbage blocks.
		# Only the first two need to be checked as there can only be one non-garbage block in the row at any time.
		for col in range(2, 4):
			if self[row][col].color == 7:
				return True
		else: return False

	def is_cleared (self):
		# Returns True if the bottom-most row, at the end of a clearing chain, is void of blocks.
		for col in range(2, 12):
			if self[21][col] is not None:
				return False
		else: return True

	def flood_fill (self, t_shape, index, linkrule):
		# Recursive blind flood fill function.
		if self[index[0]][index[1]] is not None and index[0] < 22 and 1 < index[1] < 12:
			# Reset the block's position.
			self[index[0]][index[1]].relpos = [index[1] - 6, index[0] - 1]
			# Add the block to the temporary shape.
			t_shape.add(self[index[0]][index[1]])
			# Remove the block from the grid.
			self[index[0]][index[1]] = None
			# Look at every nearby cell and perform again if valid.
			self.flood_fill(t_shape, (index[0], index[1] - 1), linkrule) # Left
			self.flood_fill(t_shape, (index[0] - 1, index[1]), linkrule) # Up
			self.flood_fill(t_shape, (index[0], index[1] + 1), linkrule) # Right
			self.flood_fill(t_shape, (index[0] + 1, index[1]), linkrule) # Down

	def link_fill (self, t_shape, index, linkrule):
		# Recursive flood fill function using the links.
		if self[index[0]][index[1]] is not None and index[0] < 22 and 1 < index[1] < 12:
			# Reset the block's position.
			self[index[0]][index[1]].relpos = [index[1] - 6, index[0] - 1]
			# Add the block to the temporary shape.
			t_shape.add(self[index[0]][index[1]])
			# Save links to temporary variable before deleting the block.
			oldlinks = self[index[0]][index[1]].links
			# Remove the block from the grid.
			self[index[0]][index[1]] = None
			# Check adjacent blocks as indicated by the links.
			if 0 in oldlinks: # Left
				self.link_fill(t_shape, (index[0], index[1] - 1), linkrule)
			if 1 in oldlinks: # Up
				self.link_fill(t_shape, (index[0] - 1, index[1]), linkrule)
			if 2 in oldlinks: # Right
				self.link_fill(t_shape, (index[0], index[1] + 1), linkrule)
			if 3 in oldlinks: # Down
				self.link_fill(t_shape, (index[0] + 1, index[1]), linkrule)

	def cascade (self, tempgrid, base_row):
		# Drop floating blocks during non-naive line clear methods.
		# Set the fallen flag of all blocks above and one row below to False, which means they're 'floating'.
		for i in range(base_row + 1, -1, -1):
			for j in range(2, 12):
				if self[i][j] is not None and self[i][j].color != 7:
					self[i][j].fallen = False
		# For each row, cut a set of temporary shapes from it to allow to fall.
		locked_shapes = True
		while locked_shapes:
			for i in range(21, -1, -1):
				# locked_shapes is True when one of the shapes in the row is blocked from falling by another shape.
				locked_shapes = False
				tempshapes = [ ]
				for j in range(2, 12):
					# Add blocks that both exist and have not fallen yet.
					if self[i][j] is None or self[i][j].fallen:
						continue
					# Create new blank temporary shape.
					tempshape = Shape()
					# Cut connected blocks from grid to the shape.
					if self.user.cleartype == 1:
						# Perform a blind flood fill if the method is sticky.
						self.flood_fill(tempshape, (i, j), self.user.linktiles)
					elif self.user.cleartype == 2:
						# Perform a flood fill considering which blocks are linked if the method is cascade.
						self.link_fill(tempshape, (i, j), self.user.linktiles)
					for block in tempshape:
						# If the block being tested isn't connected to the block below it, then the shape it's a part of is blocked.
						if (self.user.cleartype == 1
							or (3 not in block.links and self[block.relpos[1] + 2][block.relpos[0] + 6] is not None)):
							locked_shapes = True
							# Cut the shape back to the matrix.
							self.paste_shape(tempshape)
							break
					# Add this temprary shape to the list if it's not blocked.
					else: tempshapes.append(tempshape)
				# If there is at least one temporary shape created, move them all down one space.
				if not len(tempshapes):
					continue
				for shape in tempshapes:
					collision = False
					shape.translate((0, 1))	
					# Test if moving down one space causes a collision.
					for block in shape:
						if self[block.relpos[1] + shape.pos[1]][block.relpos[0] + shape.pos[0]] is None:
							continue
						collision = True
						# If a collision has occured, test if it collided with a fallen block.
						if self[block.relpos[1] + shape.pos[1]][block.relpos[0] + shape.pos[0]].fallen and not block.fallen:
							for oldblock in shape: oldblock.fallen = True
						break
					if collision:
						# Move it back up one space when a collision has been detected.
						shape.translate((0, -1))
						# If it collided with a fallen block, then the shape has fallen. Copy it back to the matrix.
						if shape.blocks[0].fallen: self.paste_shape(shape)
						# If it either did not collide, or collided with another floating shape, copy it to the tempgrid instead.
						else: tempgrid.append(shape)
					else: tempgrid.append(shape)
			

	def clear_lines (self):
		"""
		Clears lines when the free tetrimino is pasted to the grid.
		self.user.cleartype describes the 3 different styles of clearing available:
		0 refers to naive clearing, where floating blocks are left alone. Used in old Tetris games.
		1 refers to sticky clearing, where the floating blocks are grouped by those that share sides.
		2 refers to cascade clearing, where the original block groupings are preserved.

		In both sticky and cascade clearing, the groups will fall as if they were still active, then
		the lines will be re-evaluated to see if another clear happened.
		"""
		# Track how many lines are cleared per chain.
		self.user.line_list = [0]
		cleared = True
		while cleared:
			# Set the cleared flag to False to represent no lines being cleared yet.
			cleared = False	
			# Set base_row, which is the lowest row a line clear occurs in, to the top row.
			base_row = 0
			# Test if there is a full row, checking upwards, then clear all of them.
			for i in range(21, -1, -1):
				# Once a row is detected to be full, clear it.
				if self.is_full_row(i):
					# Add a ClearSprite to show the row being cleared.
					self.csprts.append(ClearSprite(bottomleft=(self.rect.centerx - 125, self.rect.bottom - 20 + 25*(i-21))))
					# Test if the cleared row is a garbage row before handling links.
					garbagerow = self.is_garbage_row(i)
					# Increment the cleared lines counter.
					self.user.line_list[-1] += 1
					cleared = True
					# If a line is full below the indicated base_row, set base_row to that row.
					if i > base_row: base_row = i
					# Remove the links that point to blocks that are to be cleared.
					for j in range(2, 12):
						# Remove upward links from blocks below.
						if self[i + 1][j] is not None and 3 in self[i][j].links:
							self[i + 1][j].links.remove(1)
							self[i + 1][j].update(self[i + 1][j].color, self.user.linktiles)
						# Remove downward links from blocks above.
						if self[i - 1][j] is not None and 1 in self[i][j].links:
							self[i - 1][j].links.remove(3)
							self[i - 1][j].update(self[i - 1][j].color, self.user.linktiles)
						# Just leave the row empty if the method is sticky or cascade.
						if self.user.cleartype > 0: self[i][j] = None
					# Splice the old row out and create a new blank row on top if method is naive or when clearing a garbage row.
					if self.user.cleartype < 1 or garbagerow:
						# Delete the old row.
						self.cells.pop(i)
						# Create new blank row at the top.
						self.cells.insert(0, [Block([i, 0], 7, fallen=True) if i < 2 or i > 11 else None for i in range(15)])
						# Force the game to look through all the rows again to avoid skipping lines.
						break
			# If a line has been cleared, let the floating blocks fall until they collide with other blocks.
			if not cleared:
				continue
			# Insert line clearing animation here.
			yield True
			# If the method is naive, then don't proceed.
			if self.user.cleartype < 1:
				continue
			while True:
				# Tempgrid is the list of all shapes that have not fallen all the way down yet.
				tempgrid = [ ]
				# Drop all floating pieces via the tempgrid.
				self.cascade(tempgrid, base_row)
				# Copy all of the tempgrid's shapes back to the matrix.
				if len(tempgrid) > 0:
					for shape in tempgrid:
						self.paste_shape(shape)
					# Display intermediate drops so the user can see the combo, via doing this as a coroutine.
					yield True
				else: break
			self.user.line_list.append(0)
			# If the tempgrid list is empty, that means that all the blocks have fallen. Check if the fallen blocks caused another line clear.
		# Evaluate score from the last clear.
		self.user.eval_clear_score(self.is_cleared())
		# Once done clearing lines, set the clearing flag to False to avoid the StopIteration exception from being raised.
		yield False

	def animate_clears (self):
		# Animate and draw the ClearSprite objects.
		for sprite in self.csprts:
			sprite.draw()
			try:
				sprite.animate()
			except StopIteration:
				self.csprts = [ ]
				break

	def update (self):
		# Display the grid background and constituent blocks.
		self.draw(env.screen)
		for i in range(22):
			for j in range(2, 12):
				if self[i][j] is None:
					continue
				block = self[i][j]
				block.relpos = [j, i]
				block.set(bottomleft=(self.rect.centerx + block.rect.w*(j-7), self.rect.bottom - 20 + block.rect.h*(i-21)))
				if i > 1: block.draw(env.screen)
