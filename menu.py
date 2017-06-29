# Stores individual menu data.
try:
	from runtime import *
except ImportError as error:
	print("Runtime has fucking failed:", error)
	raise

menu_bg = AnimatedSprite(pygame.Surface(screen.get_size()))
menu_bg.image.fill(0x008080)

class SFH (object):
	"""
	SFH, or ScoreFileHandler is a class that is built to, as the name suggests, 
	handle score file data.

	It's a context manager inteded to be used with the built-in with statement 
	to handle saving and pulling of score data safely.

	To use this, do:
	with SFH(scorefilename) as sfh: 
		# Do scorefile operations...

	Do note that sfh is a reference to the context manager object itself, not the 
	file object. The file object is referenced under the sfile attribute.
	"""

	def __init__ (self, name = 'hiscore.dat'):
		name = os.path.join('data', name)
		# The backup file is there to ensure that the data is preserved in some cases of fucketry.
		# Note: Does not work if the backup file itself is fucked with.
		try:
			self.bckup = open(name[:-3] + 'bak', 'rb+')
			# Since the backup exists, check if the data exists too.
			try:
				self.sfile = open(name, 'rb+')
			except IOError:
				# If the scorefile data is missing, but the backup still exists, use the backup to restore it.
				self.sfile = open(name, 'wb+')
				self.load()
		except IOError:
			self.bckup = open(name[:-3] + 'bak', 'wb+')
			# If the backup is missing, check if the original score data exists.
			try:
				self.sfile = open(name, 'rb+')
				self.backup()
			except IOError:
				self.sfile = open(name, 'wb+')
				self.reset()
		finally:
			self.bckup.seek(0)
			self.sfile.seek(0)
		# If this flag is False, then the backup file is assumed to be valid when a reading exception is thrown.
		self.eflag = False

	def __repr__ (self):
		return "<Score file context manager with id "+str(id(self))+">"

	def backup (self):
		# Update the backup.
		self.sfile.seek(0)
		self.bckup.seek(0)
		self.bckup.truncate()
		self.bckup.write(self.sfile.read())

	def load (self):
		# Refresh the scorefile using the backup.
		self.sfile.seek(0)
		self.bckup.seek(0)
		self.sfile.truncate()
		self.sfile.write(self.bckup.read())

	def reset (self):
		# Resets the given scorefile to the default data.
		self.sfile.seek(0)
		self.sfile.truncate()
		for i in range(3):
			for j in range(10):
				# Alexey Leonidovich Pajitnov is the developer of the original Tetris.
				score = [c.encode() for c in 'Pajitnov'] + [0, 0, 0]
				self.sfile.write(struct.pack('>ccccccccQLL', *score))
		self.backup()

	def validate (self):
		# Load from the backup file or reset both files based on the error state.
		if not self.eflag:
			# The backup hasn't been verified to be invalid yet, load from backup.
			self.load()
			self.eflag = True
		else:
			# The backup is also invalid, reset both files.
			self.reset()
			self.eflag = False

	def decode (self, splitname = False):
		# Read the scorefile, and return 3 lists of top ten score lists.
		self.sfile.seek(0, 2)
		if self.sfile.tell() != 720:
			# If the number of bytes are wrong, then the score file is probably wrong.
			# Load from the backup, but if that fails, remake the score file.
			self.validate()
			print('Scorefile length is invalid!')
			return self.decode()
		self.sfile.seek(0)
		try:
			# Each score is a set of 24 bytes, the first eight of which stand for the name entered.
			scorelists = [struct.unpack('>ccccccccQLL', self.sfile.read(24)) for i in range(30)]
		except struct.error as e:
			# If an exception is thrown during reading, first attempt to load from the backup.
			# If that still fails, reset the scores (erasing score data, whoops).
			self.validate()
			# Echo exception details to the console.
			print(e)
			return self.decode()
		if not splitname:
			# The splitname argument is True when the data needs to be read raw, rather than formatted for easy display.
			scorelists = [[scorelists[i][j].decode() if j < 8 else scorelists[i][j] for j in range(11)] for i in range(30)]
			scorelists = [[''.join(scorelists[i][:8]), scorelists[i][8], scorelists[i][9], scorelists[i][10]] for i in range(30)]
		return [scorelists[:10], scorelists[10:20], scorelists[20:]]

	def encode (self, gtype, entry):
		# Add a new score to the high scores.
		g = 0 if gtype == 'arcade' else 1 if gtype == 'timed' else 2
		# Grab the score data.
		slists = self.decode(True)
		# Add the new entry.
		for i in range(8): entry[i] = bytes(entry[i])
		slists[g].append(entry)
		# Sort the entries.
		# Lines cleared third.
		slists[g].sort(key = lambda s: s[9])
		# Time second.
		slists[g].sort(key = lambda s: s[10])
		# Score first.
		slists[g].sort(key = lambda s: s[8], reverse = True)
		# Remove the old last entry and re-arrange the score lists into a single list.
		slists[g].pop()
		slists = slists[0] + slists[1] + slists[2]
		# Apply change to scorefile.
		self.sfile.seek(0)
		self.sfile.truncate()
		for score in slists: self.sfile.write(struct.pack('>ccccccccQLL', *score))
		# Backup the entered score.
		self.backup()

	def __enter__ (self):
		# The value that will be returned to the as statement.
		return self

	def __exit__ (self, etype, evalue, tback):
		# Cleanup both files.
		self.bckup.close()
		self.sfile.close()

class MainMenu (Menu):
	""" 
	The MainMenu object represents the main menu of the game.

	The player is capable of starting the game selection, viewing the high score tables, and 
	changing the options.
	"""

	def __init__ (self, user, score_menu):
		bg = pygame.Surface((210, 300))
		bg.fill(0x00FF00)
		super().__init__(user, bg, midtop = (screen.get_width() / 2, 250))
		self.score_menu = score_menu

		hmargin = 15 # horizontal margin in pixels
		tmargin = 20 # top margin in pixels
		spacing = 5 # space between selections in pixels
		height = (self.rect.height - 2 * tmargin - 4 * spacing) / 5 # height of selections in pixels

		self.selections = [[MenuOption(self, 'play', 'Start Game', (hmargin, tmargin), (self.rect.width - 2 * hmargin, height)),
							MenuOption(self, 'help', 'How to Play', (hmargin, tmargin + (spacing + height)), (self.rect.width - 2 * hmargin, height)), 
							MenuOption(self, 'hiscore', 'High Scores', (hmargin, tmargin + 2 * (spacing + height)), (self.rect.width - 2 * hmargin, height)), 
							MenuOption(self, 'settings', 'Game Settings', (hmargin, tmargin + 3 * (spacing + height)), (self.rect.width - 2 * hmargin, height)),
							MenuOption(self, 'quit', 'Quit', (hmargin, tmargin + 4 * (spacing + height)), (self.rect.width - 2 * hmargin, height))]]
		self.set_range()

	def eval_input (self):
		event = super().eval_input()
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_z or event.key == pygame.K_RETURN:
				if self.selected.action == 'play':
					self.user.state = 'play_menu'
				elif self.selected.action == 'help':
					pass
				elif self.selected.action == 'hiscore':
					self.user.state = 'score_menu'
					# Load the scores into the score menu every time it is selected so the scores are up to date.
					with SFH() as sfh: self.score_menu.scorelist = sfh.decode()
				elif self.selected.action == 'options':
					pass
				elif self.selected.action == 'quit':
					self.user.state = 'quit'

	def run (self):
		menu_bg.draw(screen)
		self.draw(screen)
		super().run()
		pygame.display.flip()

class PlayMenu (Menu):
	""" 
	PlayMenu is the selection menu after "Start Game" is selected, it provides the player 
	with the available modes of play.

	Arcade Mode is standard Tetris, with increasing levels dependent on cleared lines. The 
	speed of the tetrominos dropping increase with the levels, up to a maximum. Score earned 
	per line cleared increases with level.

	Timed Mode is based on a timer that runs down. Dropping pieces and clearing lines cause 
	delays that are counted by the timer, so it's up to the player to find the most efficient 
	way to get the highest score in five minutes!

	Free Mode is a casual mode of play that doesn't stress the player. Good for newbies!
	"""

	def __init__(self, user):
		bg = pygame.Surface((620, 300))
		bg.fill(0x00FF40)
		super().__init__(user, bg, midtop = (screen.get_width() / 2, 250))

		hmargin = 20
		spacing = 14
		tmargin = 20
		height = 80

		self.selections = [[MenuOption(self, 'arcade', 'Arcade Mode', (hmargin, tmargin), ((self.rect.width - (2 * (spacing + hmargin))) / 3, height))], 
							[MenuOption(self, 'timed', 'Timed Mode', (hmargin + spacing + (self.rect.width - (2 * (spacing + hmargin))) / 3, tmargin), ((self.rect.width - (2 * (spacing + hmargin))) / 3, height))],
							[MenuOption(self, 'free', 'Free Mode', (hmargin + 2 * spacing + (2 * (self.rect.width - (2 * (spacing + hmargin))) / 3), tmargin), ((self.rect.width - (2 * (spacing + hmargin))) / 3, height))]]
		self.set_range()

	def eval_input (self):
		event = super().eval_input()
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_z or event.key == pygame.K_RETURN:
				if self.selected.action == 'arcade':
					self.user.gametype = 'arcade'
				elif self.selected.action == 'timed':
					self.user.gametype = 'timed'
				elif self.selected.action == 'free':
					self.user.gametype = 'free'

				self.user.state = 'game'
				self.game.set_data()
				mixer.music.play()
				self.reset()
			elif event.key == pygame.K_x or event.key == pygame.K_ESCAPE:
				self.user.state = 'main_menu'

	def run (self):
		menu_bg.draw(screen)
		self.draw(screen)
		super().run()
		pygame.display.flip()

class HelpMenu (Menu):
	"""
	LEFT and RIGHT arrow keys to shift tetrimino left and right.
	DOWN arrow key to speed up falling tetrimino.
	Z or LCTRL keys to rotate tetrimino counter-clockwise. 
	X or UP keys to rotate tetrimino clockwise.
	SPACE key to drop tetrimino, and LSHIFT to hold tetrimino.
	ESCAPE key to pause.
	"""
	def __init__(self, user):
		pass		

class HiScoreMenu (Menu):
	"""
	The High Score Menu allows the player to view the recorded high scores in the file
	hiscore.dat, segregated by game time and arranged by score. Time played and number 
	of lines cleared are also displayed, along with the name of the score setter.

	Its selections are just switching between the scoreboards of the three different game modes.
	"""
	def __init__ (self, user):
		bg = pygame.Surface((700, 480))
		bg.fill(0x40C080)
		super().__init__(user, bg, midbottom = (s_rect.centerx, s_rect.bottom - 25))
		self.font = pygame.font.SysFont(None, 30)

		self.selections = [[MenuOption(self, 'arcade', None, s_rect.topright)],
							[MenuOption(self, 'timed', None, s_rect.topright)],
							[MenuOption(self, 'free', None, s_rect.topright)]]
		self.set_range()

	def eval_input (self):
		event = super().eval_input()
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_x or event.key == pygame.K_ESCAPE:
				self.user.state = 'main_menu'

	@Menu.render
	def display_scores (self, surf):
		self.render_text(self.selected.action.capitalize() + ' Mode', 0x000000, surf, midtop = (self.rect.width / 2, 30))
		self.render_text('Name:', 0x000000, surf, topleft = (25, 70))
		self.render_text('Score:', 0x000000, surf, topleft = (185, 70))
		self.render_text('Lines:', 0x000000, surf, topleft = (390, 70))
		self.render_text('Time Taken:', 0x000000, surf, topleft = (560, 70))
		d_scores = self.scorelist[self.selection[0]]
		for i in range(10):
			self.render_text('{}'.format(d_scores[i][0]), 0x000000, surf, topleft = (30, 120 + i * 35))
			self.render_text('{}'.format(d_scores[i][1]), 0x000000, surf, topright = (self.rect.width / 2 - 30, 120 + i * 35))
			self.render_text('{}'.format(d_scores[i][2]), 0x000000, surf, topright = (self.rect.width - 210, 120 + i * 35))
			self.render_text('{}:{:02d}:{:02d}'.format(d_scores[i][3]//6000, d_scores[i][3]//100%60, d_scores[i][3]%100), 0x000000, surf, topright = (self.rect.width - 30, 120 + i * 35))

	def run (self):
		menu_bg.draw(screen)
		self.draw(screen)
		super().run()
		self.display_scores()
		pygame.display.flip()

class SettingsMenu (Menu):
	"""
	The Settings Menu allows the user to edit game settings for more convenient play.

	The selections of this menu are special, and change the states of global variables.
	"""
	def __init__(self, user):
		pass

class PauseMenu (Menu):
	"""
	Pauses the game.
	The timer doesn't run while paused.
	"""

	def __init__(self, user):
		self.pause_bg = pygame.Surface(screen.get_size())
		bg = pygame.Surface((250, 300))
		bg.fill(0x00FF00)
		super().__init__(user, bg, center = s_rect.center)
		
		tmargin = 20
		hmargin = 15
		spacing = 5
		height = 60

		self.selections = [[MenuOption(self, 'resume', 'Resume Game', (hmargin, tmargin), (self.rect.width - 2 * hmargin, height)),
							MenuOption(self, 'restart', 'Restart Game', (hmargin, tmargin + spacing + height), (self.rect.width - 2 * hmargin, height)),
							MenuOption(self, 'options', 'Options', (hmargin, tmargin + 2 * (spacing + height)), (self.rect.width - 2 * hmargin, height)),
							MenuOption(self, 'quit', 'Return to Menu', (hmargin, tmargin + 3 * (spacing + height)), (self.rect.width - 2 * hmargin, height))]]
		self.set_range()

	def set_bg (self, bg):
		# Set the background of the Pause Menu to the state of the game when the user paused it.
		self.pause_bg.blit(bg, (0, 0))

	def eval_input (self):
		event = super().eval_input()
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_z or event.key == pygame.K_RETURN:
				if self.selected.action == 'resume':
					self.user.state = 'game'
					mixer.music.unpause()
					self.reset()
				if self.selected.action == 'restart':
					self.user.state = 'game'
					self.user.reset()
					self.game.set_data()
					restart_music()
					self.reset()
				elif self.selected.action == 'options':
					pass
				elif self.selected.action == 'quit':
					self.user.state = 'main_menu'
					self.user.reset()
					self.game.set_data()
					self.reset()
			elif event.key == pygame.K_x or event.key == pygame.K_ESCAPE:
				self.user.state = 'game'

	def run (self):
		screen.blit(self.pause_bg, (0, 0))
		self.draw(screen)
		super().run()
		pygame.display.flip()


class SaveMenu (Menu):
	"""
	SaveMenu prompts the player to save a name to be attached to a high score, 
	if they would have a high score that beats one on the record.
	"""
	def __init__(self, user):
		bg = pygame.Surface((500, 150))
		bg.fill(0x0C87CD)
		super().__init__(user, bg, center = s_rect.center)
		self.name = u''
		self.placestring = '10th'

	def render_place (self, _i):
		# Turns place number into a string.
		if _i == 0: self.placestring = '1st'
		elif _i == 1: self.placestring = '2nd'
		elif _i == 2: self.placestring = '3rd'
		else: self.placestring = str(_i + 1) + 'th'

	def eval_timer (self):
		# Evaluates timer value based on game type.
		return (300000 - self.user.timer) // 10 if self.user.gametype == 'timed' else self.user.timer // 10

	def eval_input (self):
		event = pygame.event.poll()
		if event.type == pygame.QUIT:
			self.user.state = 'quit'
		if event.type == pygame.KEYDOWN:
			if ((pygame.K_a <= event.key <= pygame.K_z) or (event.key == pygame.K_SPACE) or (pygame.K_0 <= event.key <= pygame.K_9)) and len(self.name) < 8:
				self.name += event.unicode
			elif event.key == pygame.K_BACKSPACE:
				self.name = self.name[:-1]
			elif event.key == pygame.K_RETURN:
				# When the name is entered:
				# If the name length is shorter than eight characters, pad it to eight.
				if len(self.name) < 8: self.name += ' ' * (8 - len(self.name))
				with SFH() as sfh:
					# Save the score to the score file.
					score = [c.encode() for c in str(self.name)] + [self.user.score, self.user.lines_cleared, self.eval_timer()]
					sfh.encode(self.user.gametype, score)
				# Reset the menu object and refer the user to the loss menu.
				self.name = u''
				self.user.reset()
				self.user.state = 'loss_menu'
			elif event.key == pygame.K_ESCAPE:
				self.name = u''
				self.user.reset()
				self.user.state = 'loss_menu'

	@Menu.render
	def display_score (self, surf):
		self.render_text('You got the '+self.placestring+' place high score!', 0x000000, surf, midtop = (self.rect.width / 2, 15))

		self.render_text('Enter Name:', 0x000000, surf, topleft = (15, 40))
		self.render_text('Score:', 0x000000, surf, topright = (self.rect.width / 2 - 40, 40))
		self.render_text('Lines:', 0x000000, surf, topleft = (self.rect.width / 2 + 40, 40))
		self.render_text('Time Taken:', 0x000000, surf, topright = (self.rect.width - 25, 40))

		self.render_text(self.name, 0x000000, surf, topleft = (20, 65))
		self.render_text(str(self.user.score), 0x000000, surf, topright = (self.rect.width / 2 - 20, 65))
		self.render_text(str(self.user.lines_cleared), 0x000000, surf, topleft = (self.rect.width / 2 + 100, 65))
		_time = self.eval_timer()
		self.render_text('{}:{:02d}:{:02d}'.format(_time // 6000, _time // 100 % 60, _time % 100), 0x000000, surf, topright = (self.rect.width - 20, 65))

	def run (self):
		self.draw(screen)
		self.eval_input()
		self.display_score()
		pygame.display.flip()

class LossMenu (Menu):
	"""
	When you lose the game, this menu pops up to show your score and let you try for a higher one.
	"""
	def __init__ (self, user):
		self.loss_bg = pygame.Surface(screen.get_size())
		bg = pygame.Surface((250, 300))
		bg.fill(0x7F7F00)
		super().__init__(user, bg, center = s_rect.center)

		tmargin = 20
		hmargin = 15
		spacing = 5
		height = 60

		self.selections = [[MenuOption(self, 'restart', 'Try Again?', (hmargin, tmargin + spacing + height), (self.rect.width - 2 * hmargin, height)),
							MenuOption(self, 'options', 'Options', (hmargin, tmargin + 2 * (spacing + height)), (self.rect.width - 2 * hmargin, height)),
							MenuOption(self, 'quit', 'Return to Menu', (hmargin, tmargin + 3 * (spacing + height)), (self.rect.width - 2 * hmargin, height))]]
		self.set_range()

	def render_loss (self, bg):
		# To be called inside the game engine, saving relevant game data to be used.
		self.loss_score = self.user.score
		self.loss_bg.blit(bg, (0, 0))

	def eval_input (self):
		event = super().eval_input()
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_z or event.key == pygame.K_RETURN:
				if self.selected.action == 'restart':
					self.user.state = 'game'
					self.user.reset()
					self.game.set_data()
					restart_music()
					self.reset()
				elif self.selected.action == 'options':
					pass
				elif self.selected.action == 'quit':
					self.user.state = 'main_menu'
					self.user.reset()
					self.game.set_data()
					self.reset()

	@Menu.render
	def rendered_text (self, surf):
		self.render_text("Game Over!", 0xFFFFFF, surf, midtop = (self.rect.width / 2, 15))
		self.render_text("Your score was: " + str(self.loss_score), 0xFFFFFF, surf, midtop = (self.rect.width / 2, 40))

	def run (self):
		screen.blit(self.loss_bg, (0, 0))
		self.draw(screen)
		self.rendered_text()
		super().run()
		pygame.display.flip()
