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
	def __init__ (self, image, rect = None, cliprect = None, **initpos):
		super().__init__()
		self.image = image
		self.rect = self.image.get_rect() if rect is None else rect
		self.cliprect = pygame.Rect((0, 0), self.rect.size) if cliprect is None else cliprect
		self.set(**initpos)
		self.pos = float(self.rect.centerx), float(self.rect.centery) # Position needs to be float to evaluate movement more accurately.

	def set (self, **anchors):
		# Move the sprite's rect to a coordinate given a point to anchor it to.
		for point, coord in anchors.items():
			setattr(self.rect, point, coord)

	def move_rt (self, speed, angle, **anchors):
		# Convert to rectangular coordinates and add the offset.
		self.pos = self.pos[0] + speed * cos(angle), self.pos[1] + speed * sin(angle)
		self.set(**anchors)

	def move_xy (self, x, y, **anchors):
		# Add the offset.
		self.pos = self.pos[0] + x, self.pos[1] + y
		self.set(**anchors)

	def move_to (self, dest, speed, **anchor):
		# Moves pos attribute towards a target point at a certain speed.
		if hyp_area(self.pos, dest) > speed ** 2:
			self.pos = self.pos[0] + speed * get_cos(self.pos, dest), self.pos[1] + speed * get_sin(self.pos, dest)
		else:
			self.pos = dest
		self.set(**anchor)

	def animate (self, *args, **kwargs):
		# So no exception is thrown when attempting to animate combinations of FreeSprites and AnimatedSprites.
		pass

	def draw (self, surf = screen):
		# Sprite draw method for convenience.
		surf.blit(self.image, self.rect, self.cliprect)

class AnimatedSprite (FreeSprite):
	"""
	A custom Sprite child class that adds to FreeSprite functionality by adding an 
	easy way to animate using spritesheets as their source images.
	"""
	def __init__ (self, source, rect = None, cliprect = None, valign = False, **initpos):
		super().__init__(source, rect, cliprect, **initpos)

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
	
	def __next__ (self):
		if self.reverse:
			if self.frame == 0: self.frame = self.frames - 1
			else: self.frame -= 1
		else:
			if self.frame == self.frames - 1: self.frame = 0
			else: self.frame += 1
		return self.frame

	def animate (self):
		# Scrolls through the sprite sheet. Changing the animation row/col will be handled by the sprite itself.
		# Does not call AnimatedSprite.draw().
		next(self)
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

class MenuOption (AnimatedSprite):
	"""
	Menu Options are sprites for the individual selectable options in a Menu object.
	To derive unique animated behavior other than alternating between a two-frame sprite, 
	create a subclass.

	Improved version of the old MenuSelection class.
	"""
	def __init__(self, menu, action, text, pos = (0, 0), clip = (0, 0, 20, 20), src = None, relative = True):
		if type(clip) is tuple:
			if len(clip) == 2:
				clip = pygame.Rect((0, 0), clip)
			else:
				clip = pygame.Rect(clip)
		
		if src is None:
			src = pygame.Surface((clip.width * 2, clip.height))
			src.fill(0x3F3F3F)
			selbg = pygame.Surface(clip.size)
			selbg.fill(0x7F7F7F)
			src.blit(selbg, (clip.width, 0))
			del selbg

		super().__init__(src, pygame.Rect(pos, clip.size), clip)
		self.menu = menu
		self.action = action

		if relative: self.set(topleft = (self.menu.rect.left + self.rect.left, self.menu.rect.top + self.rect.top))

		if text is not None:
			self.text = self.menu.font.render(text, 0, pygame.Color(255, 255, 255))
			self.text_rect = self.text.get_rect()
		else: self.text = None

		self.selected = False

	def set_select (self, state):
		# Set selection state to True or False.
		self.selected = state

	def update (self, surf = screen):
		self.set_clip(self.selected)
		self.draw(surf)
		if self.text is not None:
			self.text_rect.center = self.rect.center
			surf.blit(self.text, self.text_rect)

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
		self.selections = [[MenuOption(self, 'Null', ' ')]]
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

		self.select(*self.selection).set_select(False)

	def set_range (self):
		# Initializes the range value of the menu selections. Safe to call more than once on one initialization.
		# Note that the menu selections are assumed to be rectangular in nature.
		self.range = [len(self.selections), len(self.selections[0])]

	def reset (self):
		# Resets the menu 'cursor' back to the default.
		self.select(*self.selection).set_select(False)
		self.selection = [0, 0]
		self.select(*self.selection).set_select(True)

	def select(self, i, j):
		# Easy way of getting the current selection.
		return self.selections[i][j]

	def render_text (self, text, color, surf = screen, **pos):
		# Render a message to the screen.
		tsurf = self.font.render(text, 0, color)
		surf.blit(tsurf, tsurf.get_rect(**pos))

	@staticmethod
	def render (method):
		"""
		Modifies a method written to display menu details relative to the background surface of the menu,
		blitting all of it to a colorkey-preset surface passed as the second argument to the original method.

		For this to work, the display method needs to have a second argument as the surface to be used,
		all constituent surface are blitted to that surface and don't need magenta (0xFF00FF).

		To call this decorator, use @Menu.render
		"""
		def wrapper(self, *args, **kwargs):
			rsurf = pygame.Surface(self.rect.size)
			rsurf.fill(0xFF00FF)
			rsurf.set_colorkey(0xFF00FF)

			method(self, rsurf, *args, **kwargs)

			screen.blit(rsurf, self.rect)
		return wrapper


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

	def run (self, surf = screen):
		# Update the movement values per frame.
		self.eval_input()
		# Move selection.
		self.select(*self.selection).set_select(False)
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
		self.select(*self.selection).set_select(True)
		for items in self.selections:
			for item in items:
				item.update(surf)
