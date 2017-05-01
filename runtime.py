# My personal environment upon which I base my pygame projects. Small changes will exist here from game to game, but it will all mostly look like this.
# The way I code things is for optimized reusability. So while it may not be the shortest or most code-efficient way of creating a game, 
# I try to make it such that I could easily plug and edit blocks of code into similar applications.
# Also it's good for convenience's sake that I don't have to think so hard about what the hell I did when I wrote the older stuff.
# [ ] square bracket copy reference, { } curly braces reference
try:
	import os, sys
	import math, random
	import pygame, pygame.mixer
	import struct
	import hashlib
except ImportError as error:
	print("Something screwey happened:", error)

pygame.init()
pygame.mixer.init(buffer = 1024)
screen = pygame.display.set_mode((800, 600), pygame.HWSURFACE | pygame.DOUBLEBUF)
s_rect = screen.get_rect()
pygame.display.set_caption('pyTetris')
clock = pygame.time.Clock()

def sin (angle):
	# Degree sine
	return math.sin(math.radians(angle))

def cos (angle):
	# Degree cosine
	return math.cos(math.radians(angle))

def hyp_area (p1, p2):
	# The area of a square whose side is the length of the line segment bounded by p1 and p2.
	# Used for comparing distances without dealing with a square root operation.
	return ((p1[0] - p2[0]) ** 2, (p1[1] - p2[1]) ** 2) # c^2 = a^2 + b^2

def get_ang (p1, p2):
	# Angle from p1 to p2.
	return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])) # Positive is usually clockwise.

def get_dist (p1, p2):
	# The absolute shortest distance between p1 and p2.
	return math.sqrt(hyp_area(p1, p2)) # c = sqrt(c^2)

def get_sin (p1, p2):
	# Sine of angle from p1 to p2 by definition in a Cartesian plane.
	return (p2[1] - p1[1]) / get_dist(p1, p2) # Opposite over Hypotenuse

def get_cos (p1, p2):
	# Cosine of angle from p1 to p2 by definition in a Cartesian plane.
	return (p2[0] - p1[0]) / get_dist(p1, p2) # Adjacent over Hypotenuse

def load_image (name, alpha = None, colorkey = None):
	# Load an image file into memory. Try not to keep too many of these in memory.
	try:
		image = pygame.image.load(os.path.join('textures', name))
	except pygame.error as err:
		print("Image could not be loaded: ")
		raise err
	if alpha is None:
		image = image.convert()
		if colorkey is not None:
			image.set_colorkey(colorkey)
	else:
		image = image.convert_alpha()
	return image

def load_music(name):
	# Loads a music file into the stream.
	return pygame.mixer.music.load(os.path.join('music', name))

def restart_music():
	# Restarts the current music in the stream in one statement.
	pygame.mixer.music.rewind()
	pygame.mixer.music.play()

class FreeSprite (pygame.sprite.Sprite):
	"""
	FreeSprite is the replacement for PositionedSurface; 
	it retains all of the functionality while including the convenience of being a 
	pygame.sprite.Sprite child class.
	"""
	def __init__ (self, image, rect = None, **initpos):
		super().__init__()
		self.image = image
		self.rect = self.image.get_rect() if rect is None else rect
		self.cliprect = pygame.Rect((0, 0), self.rect.size)
		self.set(**initpos)
		self.pos = float(self.rect.centerx), float(self.rect.centery) # Position needs to be float to evaluate movement more accurately.

	def set (self, **anchors):
		# Move the sprite's rect to a coordinate given a point to anchor it to.
		for point, coords in anchors.items():
			setattr(self.rect, point, coords)

	def move_rt (self, speed, angle):
		# Convert to rectangular coordinates and add the offset.
		self.pos = self.pos[0] + speed * cos(angle), self.pos[1] + speed * sin(angle)
		self.set(center = self.pos)

	def move_xy (self, x, y):
		# Add the offset.
		self.pos = self.pos[0] + x, self.pos[1] + y
		self.set(center = self.pos)

	def move_to (self, dest, speed, **anchor):
		# Moves pos attribute towards a target point at a certain speed.
		if hyp_area(self.pos, dest) > speed ** 2:
			self.pos = self.pos[0] + speed * get_cos(self.pos, dest), self.pos[1] + speed * get_sin(self.pos, dest)
		else:
			self.pos = dest
		self.set(**anchor)

	def animate (self):
		# So no exception is thrown when attempting to animate combinations of FreeSprites and AnimatedSprites.
		pass

	def draw (self, surf = screen):
		# Sprite draw method for convenience.
		surf.blit(self.image, self.rect, self.cliprect)

	def blit_to (self, surf = screen):
		# Alias for backwards compatibility.
		self.draw(surf)

class AnimatedSprite (FreeSprite):
	"""
	A custom Sprite child class that adds to FreeSprite functionality by adding an 
	easy way to animate using spritesheets as their source images.
	"""
	def __init__ (self, source, rect = None, cliprect = None, valign = False, **initpos):
		super().__init__(source, rect, **initpos)
		if cliprect is not None: self.cliprect = cliprect

		self.frame = 0
		self.frames = 1 # Number of total frames in a single animation.
		self.valign = valign # If valign is true, the spritesheet is aligned downwards rather than rightwards.
		self.reverse = False

	def set_clip (self, frame = -1):
		# Sets the cliprect to the proper frame.
		if frame >= 0: self.frame = frame

		if self.valign: self.cliprect.top = self.cliprect.h * self.frame
		else: self.cliprect.left = self.cliprect.w * self.frame

	def create_framelist (self, framelist):
		# Creates a generator that animates the sprite through a sequence of frames described by framelist.
		# The generator object returns True when it's finished animating.
		self.frames = len(framelist)
		for frame in framelist:
			self.set_clip(frame)
			yield False
		# If you want the animation to loop indefinitely, use it inside a looped if statement that replaces 
		# the generator object with a new one if True.
		yield True

	def animate (self):
		# Scrolls through the sprite sheet. Changing the animation row/col will be handled by the sprite itself.
		# Does not call AnimatedSprite.draw().
		if self.reverse:
			if self.frame == 0: self.frame = self.frames - 1
			else: self.frame -= 1
		else:
			if self.frame == self.frames - 1: self.frame = 0
			else: self.frame += 1
		self.set_clip()

class FreeGroup (pygame.sprite.Group):
	"""
	Custom extended Group class made to be used with FreeSprites or AnimatedSprites.
	It just replaces the draw function such that it uses the sprites' 
	cliprects instead of drawing whole source images.
	"""
	def animate(self):
		for sprite in self: sprite.animate()

	def draw (self):
		for sprite in self: sprite.draw()

class MenuSelection (AnimatedSprite):
	"""
		Menu Selections store the data of a selection in a menu, such as the name, position, 
		and image associated with it. It will also handle simple manipulation of its 'selected' 
		state and display.
	"""

	def __init__ (self, menu, action, text, pos, size, unsel_bg = None, sel_bg = None):
		super().__init__(unsel_bg, pygame.Rect(pos, size))
		# Position is the coordinates of the topleft corner of the selection's rectangle.
		self.action = action
		self.menu = menu
		self.text = self.menu.font.render(text, 0, pygame.Color(255, 255, 255))
		self.text_rect = self.text.get_rect()

		if unsel_bg is None:
			unsel_bg = pygame.Surface(size)
			unsel_bg.fill((64, 64, 64))
			self.image = unsel_bg
		self.unsel_bg = unsel_bg
		if sel_bg is None:
			self.sel_bg = pygame.Surface(size)
			self.sel_bg.fill((128, 128, 128))
		else:
			self.sel_bg = sel_bg
		
		self.selected = False

	def set_select (self, state):
		# Set selection state to True or False.
		self.selected = state

	def update (self):
		# Update and display the image and text associated with this option.
		if self.selected:
			self.image = self.sel_bg
		else:
			self.image = self.unsel_bg
		self.draw(screen)
		screen.blit(self.text, (self.rect.left + (self.rect.width - self.text_rect.width) / 2, self.rect.top + (self.rect.height - self.text_rect.height) / 2))

class Menu (AnimatedSprite):
	"""
	The Menu class is the superclass to all menu objects, and will handle basic menu operations, 
	such as moving along selections, positioning, and committing.
	"""

	def __init__ (self, user, bg = None, rect = None, **pos):
		if bg is None:
			bg = pygame.Surface((50, 50))
			bg.fill((255, 0, 0))
		if rect is None:
			rect = bg.get_rect()
		super().__init__(bg, rect, **pos)

		self.user = user
		self.font = pygame.font.SysFont(None, 25)
		# Coordinates of currently selected selection.
		self.selection = [0, 0]
		# All menus will have their own selections set, effectively a 2d array, with the range length set at every instance.
		self.selections = [[MenuSelection(self, 'Null', ' ', self.rect.topleft, (20, 20))]]
		self.set_range()
		# Selection movement.
		self.up = False
		self.down = False
		self.left = False
		self.right = False
		self.moved = False
		self.basetime = 25
		self.shortime = 6
		self.movetime = self.basetime

		self.get_selected(*self.selection).set_select(False)

	def set_range (self):
		# Initializes the range value of the menu selections. Safe to call more than once on one initialization.
		# Note that the menu selections are assumed to be rectangular in nature.
		self.range = [len(self.selections), len(self.selections[0])]

	def reset (self):
		# Resets the menu 'cursor' back to the default.
		self.get_selected(*self.selection).set_select(False)
		self.selection = [0, 0]
		self.get_selected(*self.selection).set_select(True)

	def get_selected(self, i, j):
		# Easy way of getting the current selection.
		return self.selections[i][j]

	def render_text (self, text, color, **pos):
		# Render a message to the screen.
		tsurf = self.font.render(text, 0, color)
		screen.blit(tsurf, tsurf.get_rect(**pos))

	def eval_input (self):
		# Evaluate user input. Handling of specific options is menu-specific.
		event = pygame.event.poll()
		if event.type == pygame.QUIT:
			self.user.state = 'quit'
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_LEFT or event.key == pygame.K_UP or event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
				# Reset the move attributes.
				self.up = False
				self.down = False
				self.left = False
				self.right = False
				self.moved = False
				self.movetime = self.basetime

				if event.key == pygame.K_LEFT:
					self.left = True
				elif event.key == pygame.K_UP:
					self.up = True
				elif event.key == pygame.K_RIGHT:
					self.right = True
				elif event.key == pygame.K_DOWN:
					self.down = True
		elif event.type == pygame.KEYUP:
			if event.key == pygame.K_LEFT or event.key == pygame.K_UP or event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
				self.up = False
				self.down = False
				self.left = False
				self.right = False
				self.moved = False
				self.movetime = self.basetime
		return event

	def run (self):
		# Update the movement values per frame.
		self.eval_input()
		# Move selection.
		self.get_selected(*self.selection).set_select(False)
		if self.left:
			if not self.moved:
				self.selection[0] -= 1
				self.moved = True
			else:
				self.movetime -= 1
				if self.movetime < 1:
					self.selection[0] -= 1
					self.movetime = self.shortime
		elif self.up:
			if not self.moved:
				self.selection[1] -= 1
				self.moved = True
			else:
				self.movetime -= 1
				if self.movetime < 1:
					self.selection[1] -= 1
					self.movetime = self.shortime
		elif self.right:
			if not self.moved:
				self.selection[0] += 1
				self.moved = True
			else:
				self.movetime -= 1
				if self.movetime < 1:
					self.selection[0] += 1
					self.movetime = self.shortime
		elif self.down:
			if not self.moved:
				self.selection[1] += 1
				self.moved = True
			else:
				self.movetime -= 1
				if self.movetime < 1:
					self.selection[1] += 1
					self.movetime = self.shortime
		# Wrap around.
		for i in range(2):
			if self.selection[i] > self.range[i] - 1:
				self.selection[i] = 0
			elif self.selection[i] < 0:
				self.selection[i] = self.range[i] - 1
		# print self.selection
		self.get_selected(*self.selection).set_select(True)
		for items in self.selections:
			for item in items:
				item.update()
