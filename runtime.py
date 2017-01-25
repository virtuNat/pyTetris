# My personal environment upon which I base my pygame projects. Small changes will exist here from game to game, but it will all mostly look like this.
# [ ] square bracket copy reference, { } curly braces reference
try:
	import os, sys
	import math, random
	import pygame, pygame.mixer
	# import pygame._view; # For some reason, this doesn't fucking work.
except ImportError, error:
	print "Something screwey happened:", error

pygame.init()
pygame.mixer.init(buffer = 1024)
screen = pygame.display.set_mode((800, 600), pygame.HWSURFACE | pygame.DOUBLEBUF)
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
	return ((p1[0] - p2[0]) ** 2, (p1[1] - p2[1]) ** 2); # c^2 = a^2 + b^2

def get_ang (p1, p2):
	# Angle from p1 to p2.
	return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])) # Positive is usually clockwise.

def get_dist (p1, p2):
	# The absolute shortest distance between p1 and p2.
	return math.sqrt(hyp_area(p1, p2)); # c = sqrt(c^2)

def get_sin (p1, p2):
	# Sine of angle from p1 to p2 by definition in a Cartesian plane.
	return (p2[1] - p1[1]) / get_dist(p1, p2); # Opposite over Hypotenuse

def get_cos (p1, p2):
	# Cosine of angle from p1 to p2 by definition in a Cartesian plane.
	return (p2[0] - p1[0]) / get_dist(p1, p2); # Adjacent over Hypotenuse

def load_image (name, alpha = None, colorkey = None):
	# Load an image file into memory. Try not to keep too many of these in memory.
	try:
		image = pygame.image.load(os.path.join('textures', name))
	except pygame.error, err:
		print "Image could not be loaded:"
		raise err
	if alpha is None:
		image.convert()
		if colorkey is not None:
			image.set_colorkey(colorkey)
	else:
		image.convert_alpha()
	return image

class PositionedSurface (object):
	"""
		PositionedSurface is a custom class that packs pygame Surfaces and Rects together for 
		easy handling with custom methods.
	"""
	def __init__ (self, image, rect = None, **initpos):
		self.image = image
		if rect is None:
			self.rect = self.image.get_rect()
		else:
			self.rect = rect
		self.cliprect = pygame.Rect((0, 0), self.rect.size)
		self.pos = self.rect.center
		self.set(**initpos)

	def set (self, **pos):
		for key, value in pos.items():
			if key == 'center': 
				self.rect.center = value
			elif key == 'centerx':
				self.rect.centerx = value
			elif key == 'centery':
				self.rect.centery = value
			elif key == 'topleft':
				self.rect.topleft = value
			elif key == 'topright':
				self.rect.topleft = value
			elif key == 'bottomleft':
				self.rect.topleft = value
			elif key == 'bottomright':
				self.rect.topleft = value
			elif key == 'midleft':
				self.rect.midleft = value
			elif key == 'midright':
				self.rect.midright = value
			elif key == 'midtop':
				self.rect.midtop = value
			elif key == 'midbottom':
				self.rect.midbottom = value
			elif key == 'top': 
				self.rect.top = value
			elif key == 'left':
				self.rect.left = value
			elif key == 'right':
				self.rect.right = value
			elif key == 'bottom':
				self.rect.bottom = balue

	def move_rt (self, speed, angle):
		# Convert to rectangular coordinates and add the offset.
		self.pos = self.pos[0] + speed * cos(angle), self.pos[1] + speed * sin(angle)
		self.set(center = self.pos)

	def move_xy (self, x, y):
		# Add the offset.
		self.pos = self.pos[0] + x, self.pos[1] + y
		self.set(center = self.pos)

	def move_to (self, dest, speed):
		# Moves pos attribute towards a target point at a certain speed.
		# Remember to re-anchor the rectangle after calling this method. e.g. self.rect.center = self.pos
		if hyp_area(self.pos, dest) > speed ** 2:
			self.pos = self.pos[0] + speed * get_cos(self.pos, dest), self.pos[1] + speed * get_sin(self.pos, dest)
		else:
			self.pos = dest

	def blit_to (self, image):
		# So I just have to handle it via the self.cliprect attribute rather than some other bullshit.
		image.blit(self.image, self.rect.topleft, self.cliprect)

class AnimatedSprite (PositionedSurface):
	"""docstring for AnimatedSprite"""
	def __init__(self, source, rect = None, **initpos):
		super(AnimatedSprite, self).__init__(source, rect, **initpos)

class MenuSelection (AnimatedSprite):
	"""
		Menu Selections store the data of a selection in a menu, such as the name, position, 
		and image associated with it. It will also handle simple manipulation of its 'selected' 
		state and display.
	"""

	def __init__ (self, menu, action, text, pos, size, unsel_bg = None, sel_bg = None):
		super(MenuSelection, self).__init__(unsel_bg, pygame.Rect(pos, size))
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
		self.blit_to(screen)
		screen.blit(self.text, (self.rect.left + (self.rect.width - self.text_rect.width) / 2, self.rect.top + (self.rect.height - self.text_rect.height) / 2))

class Menu (AnimatedSprite):
	"""
		The Menu class is the superclass to all menu objects, and will handle basic menu operations, 
		such as moving along selections, positioning, and committing.
	"""

	def __init__ (self, user, bg = None, rect = None):
		if bg is None:
			bg = pygame.Surface((50, 50))
			bg.fill((255, 0, 0))
		if rect is None:
			rect = bg.get_rect()
		super(Menu, self).__init__(bg, rect)

		self.user = user
		self.font = pygame.font.SysFont(None, 25)
		# Coordinates of currently selected selection.
		self.selection = [0, 0]
		# All menus will have their own selections set, effectively a 2d array, with the range length set at every instance.
		self.selections = [[MenuSelection(self, 'Null', 'Null', (0, 0), (1, 1))]]
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

		self.selections[self.selection[0]][self.selection[1]].set_select(False)

	def set_range (self):
		# Initializes the range value of the menu selections. Safe to call more than once on one initialization.
		self.range = [len(self.selections), len(self.selections[0])]

	def reset (self):
		# Resets the menu 'cursor' back to the default.
		self.selections[self.selection[0]][self.selection[1]].set_select(False)
		self.selection = [0, 0]
		self.selections[0][0].set_select(True)

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
		self.selections[self.selection[0]][self.selection[1]].set_select(False)
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
		self.selections[self.selection[0]][self.selection[1]].set_select(True)
		for items in self.selections:
			for item in items:
				item.update()
		