# My personal environment upon which I base my pygame projects. Small changes will exist here from game to game, but it will all mostly look like this.
# The way I code things is for optimized reusability. So while it may not be the shortest or most code-efficient way of creating a game,
# I try to make it such that I could easily plug and edit blocks of code into similar applications.
# Also it's good for convenience's sake that I don't have to think so hard about what the hell I did when I wrote the older stuff.
# [ ] square bracket copy reference, { } curly braces reference
try:
	import os
	import sys
	import math
	import random
	import pygame as pg
except ImportError:
	print("A module must've shat itself:")
	raise

pg.init()
pg.mixer.init(buffer=1024)
screen = pg.display.set_mode((800, 600), pg.HWSURFACE | pg.DOUBLEBUF)
screct = screen.get_rect()
pg.display.set_caption('pyTetris')
clock = pg.time.Clock()

def sin (angle):
	# Degree sine alias.
	return math.sin(math.radians(angle))

def cos (angle):
	# Degree cosine alias.
	return math.cos(math.radians(angle))

def hyp_area (p1, p2):
	# The area of a square whose side is the length of the line segment bounded by p1 and p2.
	# Used for comparing distances without dealing with a square root operation.
	return sum([(p2[i]-p1[i]) ** 2 for i in range(2)]) # c^2 = a^2 + b^2

def get_ang (p1, p2):
	# Angle from p1 to p2.
	return math.degrees(math.atan2(p2[1] - p1[1], p2[0] - p1[0])) # Positive is usually clockwise.

def get_dist (p1, p2):
	# The absolute shortest distance between p1 and p2.
	return math.hypot(p2[0] - p1[0], p2[1] - p1[1]) # c = sqrt(c^2)

def get_sin (p1, p2):
	# Sine of angle from p1 to p2 by definition in a Cartesian plane.
	return (p2[1]-p1[1]) / get_dist(p1, p2) # Opposite over Hypotenuse

def get_cos (p1, p2):
	# Cosine of angle from p1 to p2 by definition in a Cartesian plane.
	return (p2[0]-p1[0]) / get_dist(p1, p2) # Adjacent over Hypotenuse

def load_image (name, alpha=None, colorkey=None):
	# Load an image file into memory. Try not to keep too many of these in memory.
	try:
		image = pg.image.load(os.path.join('textures', name))
	except pg.error:
		print("Image could not be loaded: ")
		raise
	if alpha is None:
		image = image.convert()
		if colorkey is not None:
			image.set_colorkey(colorkey)
	else:
		image = image.convert_alpha()
	return image

def render_text (obj, text, color, surf=screen, **anchors):
	# Takes an object with a font attribute, and creates a text surface that it blits to a given surface.
	# Can be added to any class as a method, provided that class instances have a font attribute.
	if obj is None: obj = type('_', (), {'font': pg.font.SysFont(None, 25)})()
	if color < 2 ** 24:
		# The output surface has 255 alpha by default, but it's possible to add an alpha channel to the color number.
		color = color*256 + 255
	tsurf = obj.font.render(text, 0, pg.Color(color))
	surf.blit(tsurf, tsurf.get_rect(**anchors))

def load_music(name):
	# Loads a music file into the stream.
	return pg.mixer.music.load(os.path.join('music', name))

def restart_music():
	# Restarts the current music in the stream in one statement.
	pg.mixer.music.rewind()
	pg.mixer.music.play()

def quit (exit=1):
	# Alias to cleanup functions.
	pg.quit()
	sys.exit(exit)

class FreeSprite (pg.sprite.Sprite):
	"""
	FreeSprite is the replacement for PositionedSurface;
	it retains all of the functionality while including the convenience of being a
	pg.sprite.Sprite child class.
	"""
	def __init__ (self, image, rect=None, cliprect=None, **initpos):
		super().__init__()
		self.image = image
		self.rect = self.image.get_rect() if rect is None else pg.Rect(rect)
		self.cliprect = pg.Rect((0, 0), self.rect.size) if cliprect is None else pg.Rect(cliprect)
		self.set(**initpos)
		self.pos = float(self.rect.centerx), float(self.rect.centery) # Position needs to be float to evaluate movement more accurately.

	def __str__ (self):
		return "<FreeSprite at "+str(list(self.rect))+", with clip "+str(list(self.cliprect))+">"

	def set (self, **anchors):
		# Move the sprite's rect to a coordinate given a point to anchor it to.
		# If 'pos' is specified as an anchor, use the sprite's current pos attribute as the anchor.
		for point, anchor in anchors.items():
			if anchor == 'pos':
				anchor = self.pos
			setattr(self.rect, point, anchor)

	def move_rt (self, speed, angle, **anchors):
		# Convert to rectangular coordinates and add the offset.
		self.pos = self.pos[0] + speed*cos(angle), self.pos[1] + speed*sin(angle)
		# Anchor to center of image rectangle by default.
		if len(anchors) == 0:
			anchors = dict(center=self.pos)
		self.set(**anchors)

	def move_xy (self, x, y, **anchors):
		# Add the offset.
		self.pos = self.pos[0] + x, self.pos[1] + y
		# Anchor to center of image rectangle by default.
		if len(anchors) == 0:
			anchors = dict(center=self.pos)
		self.set(**anchors)

	def move_to (self, dest, speed, **anchor):
		# Moves pos attribute towards a target point at a certain speed.
		if hyp_area(self.pos, dest) > speed ** 2:
			self.pos = self.pos[0] + speed*get_cos(self.pos, dest), self.pos[1] + speed*get_sin(self.pos, dest)
		else:
			self.pos = dest
		# Anchor to center of image rectangle by default.
		if len(anchor) == 0:
			anchor = dict(center=self.pos)
		self.set(**anchor)

	def draw (self, surf=screen):
		# Sprite draw method for convenience.
		surf.blit(self.image, self.rect, self.cliprect)

	def animate (self, *args, **kwargs):
		# So no exception is thrown when attempting to animate combinations of FreeSprites and AnimatedSprites.
		pass

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

	def __str__ (self):
		return "<Animated Sprite at frame "+str(self.frame)+">"

	def __iter__ (self):
		self.frame = self.frames - 1 if self.reverse else 0
		return self

	def __next__ (self):
		return self.animate()

	def set_clip (self, frame = -1):
		# Sets the cliprect to the proper frame.
		if frame >= 0: self.frame = frame

		if self.valign: self.cliprect.y = self.cliprect.h * self.frame
		else: self.cliprect.x = self.cliprect.w * self.frame

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

	def animate (self, loop=False):
		# Auto-iterates through a scrolling animation, allowing a simple loop call for a looping animation.
		# Does not call AnimatedSprite.draw(). Such a call should occur before animate() is called.
		if self.reverse:
			if self.frame == 0:
				if loop: self.frame = self.frames - 1
				else: raise StopIteration
			else: self.frame -= 1
		else:
			if self.frame == self.frames - 1:
				if loop: self.frame = 0
				else: raise StopIteration
			else: self.frame += 1
		self.set_clip()
		return self.frame

class FreeGroup (pg.sprite.Group):
	"""
	Custom extended Group class made to be used with FreeSprites or AnimatedSprites.
	It just replaces the draw function such that it uses the sprites'
	cliprects instead of drawing whole source images.
	"""
	def __str__ (self):
		return "<Free Group containing:"+str(list(sprite for sprite in self))+">"

	def animate(self, loop = False):
		for sprite in self: sprite.animate(loop)

	def draw (self, surf):
		for sprite in self: sprite.draw(surf)

class MenuOption (AnimatedSprite):
	"""
	Menu Options are sprites for the individual selectable options in a Menu object.
	To derive unique animated behavior other than alternating between a two-frame sprite,
	create a subclass.

	Improved version of the old MenuSelection class.
	"""
	def __init__(self, menu, action, text, pos=(0, 0), clip=(0, 0, 20, 20), src=None, relative=True):
		if len(clip) == 2:
			clip = (0, 0, clip[0], clip[1])

		if src is None:
			src = pg.Surface((clip[2] * 2, clip[3]))
			src.fill(0x3F3F3F)
			selbg = pg.Surface(clip[2:4])
			selbg.fill(0x7F7F7F)
			src.blit(selbg, (clip[2], 0))
			del selbg

		super().__init__(src, (pos, clip[2:4]), clip)
		self.menu = menu
		self.action = action

		if relative:
			self.set(topleft = (self.menu.rect.x + self.rect.x, self.menu.rect.y + self.rect.y))
		if text is not None:
			self.text = self.menu.font.render(text, 0, pg.Color(255, 255, 255))
			self.text_rect = self.text.get_rect(center = self.rect.center)
		else:
			self.text = None
		self.is_selected = False

	def __str__ (self):
		return "<MenuOption "+self.action+" for "+str(self.menu.__class__.__name__)+".>"

	def __repr__ (self):
		return self.__str__()

	def update (self, surf = screen):
		self.set_clip(self.is_selected)
		self.draw(surf)
		if self.text is not None: surf.blit(self.text, self.text_rect)

class Menu (AnimatedSprite):
	"""
	The Menu class is the superclass to all menu objects, and will handle basic menu operations,
	such as moving along selections, positioning, and committing.
	"""

	# def __new__ (cls): return type(cls, bases, attrs)()
	# While it may be tempting to use Menu as a metaclass, there is no need for such specific behavioral changes during construction.

	def __init__ (self, user, bg=None, rect=None, **pos):
		if bg is None:
			bg = pg.Surface((50, 50))
			bg.fill((255, 0, 0))
		if rect is None:
			rect = bg.get_rect()
		super().__init__(bg, rect, **pos)

		self.user = user
		self.font = pg.font.SysFont(None, 25)
		# Coordinates of currently selected selection.
		self.selection = [0, 0]
		# All menus will have their own selections set, effectively a 2d array, with the range length set at every instance.
		self.selections = [[MenuOption(self, 'Null', ' ')]]
		# Selection movement.
		self.up = False
		self.down = False
		self.left = False
		self.right = False
		self.moved = False
		self.basetime = 25
		self.shortime = 6
		self.movetime = self.basetime

	def __getattr__ (self, name):
		if name == 'selected':
			# Alias to currently selected item.
			return self.select()
		elif name == 'range':
			# Dimensions of the rectangular selection array.
			return [len(self.selections), len(self.selections[0])]

	def select (self, addrs=None):
		# Easy way of getting the current selection.
		if addrs is None: addrs = self.selection
		return self.selections[addrs[0]][addrs[1]]

	def set_select (self, state, addrs=None):
		# Set the indicated item's selected state.
		self.select(addrs).is_selected = state

	def reset (self):
		# Resets the menu 'cursor' back to the default.
		self.set_select(False)
		self.selection = [0, 0]
		self.set_select(True)

	# Refer to the function of the same name above.
	render_text = render_text

	@staticmethod
	def render (method):
		"""
		Modifies a method written to display menu details relative to the background surface of the menu,
		blitting all of it to a colorkey-preset surface passed as the second argument to the original method.

		For this to work, the display method needs to have a second argument as the surface to be used,
		all constituent surfaces are blitted to that surface and don't need magenta (0xFF00FF).

		To call this decorator, use @Menu.render or method = Menu.render(method)
		"""
		def wrapper (self, *args, **kwargs):
			rsurf = pg.Surface(self.rect.size)
			rsurf.fill(0xFF00FF)
			rsurf.set_colorkey(0xFF00FF)

			method(self, rsurf, *args, **kwargs)

			screen.blit(rsurf, self.rect)
		return wrapper

	def eval_input (self):
		# Evaluate user input. Handling of specific options is menu-specific.
		event = pg.event.poll()
		if event.type == pg.QUIT:
			self.user.state = 'quit'
		elif event.type == pg.KEYDOWN:
			if event.key == pg.K_LEFT or event.key == pg.K_UP or event.key == pg.K_RIGHT or event.key == pg.K_DOWN:
				# Reset the move attributes.
				self.up = False
				self.down = False
				self.left = False
				self.right = False
				self.moved = False
				self.movetime = self.basetime

				if event.key == pg.K_LEFT:
					self.left = True
				elif event.key == pg.K_UP:
					self.up = True
				elif event.key == pg.K_RIGHT:
					self.right = True
				elif event.key == pg.K_DOWN:
					self.down = True
		elif event.type == pg.KEYUP:
			if event.key == pg.K_LEFT or event.key == pg.K_UP or event.key == pg.K_RIGHT or event.key == pg.K_DOWN:
				self.up = False
				self.down = False
				self.left = False
				self.right = False
				self.moved = False
				self.movetime = self.basetime
		return event

	def run (self, surf=screen):
		# Update the movement values per frame.
		self.eval_input()
		# Move selection.
		self.set_select(False)
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
		self.set_select(True)
		for items in self.selections:
			for item in items:
				item.update(surf)
