# Stores individual menu data.
try:
	from runtime import *
except ImportError as error:
	print("Runtime has fucking failed:", error)

menu_bg = AnimatedSprite(pygame.Surface(screen.get_size()))
menu_bg.image.fill((0, 128, 128))

def gen_scorelists (name = 'hiscore.dat'):
	# Sets a new hiscore file. Should only be used when the hiscore.dat file is missing or corrupted somehow.
	name = os.path.join('data', name)
	with open(name, 'wb') as _scorefile:
		for i in range(3):
			for j in range(10):
				score = list('Pajitnov') + [
					(15000 + 5000 * (2 - i)) * (10 - j),
					10 * (10 - j),
					30000 if i == 1 else 2500 * (10 - j)]
				_scorefile.write(struct.pack('>ccccccccQLL', *score))

def decode_scores (splitname = False, name = 'hiscore.dat'):
	# Reads the high scores file as a set of score lists.
	name = os.path.join('data', name)
	if not os.path.isfile(name):
		# If the file is missing, make a new one.
		gen_scorelists()

	with open(name, 'rb') as _scorefile:
		if len(_scorefile.read()) != 24 * 30:
			err = True
		_scorefile.seek(0)
		scorelists = [struct.unpack('>ccccccccQLL', _scorefile.read(24)) for i in range(30)]
		scorelists = [[scorelists[i][j].decode() if j < 8 else scorelists[i][j] for j in range(11)] for i in range(30)]
		if not splitname: scorelists = [[''.join(scorelists[i][:8]), scorelists[i][8], scorelists[i][9], scorelists[i][10]] for i in range(30)]
		return [scorelists[:10], scorelists[10:20], scorelists[20:30]]
	if err:
		gen_scorelists()
		return decode_scores()

def encode_scores (gametype = 'arcade', scorelist = list('Pajitnov') + [4250000, 6400, 1000000], name = 'hiscore.dat'):
	# Writes a new score to the high scores file.
	if gametype == 'arcade': gametype = 0
	elif gametype == 'timed': gametype = 1
	elif gametype == 'free': gametype = 2

	_scorelists = decode_scores(True)
	name = os.path.join('data', name)
	with open(name, 'wb') as _scorefile:
		_scorelists[gametype].append(scorelist)
		# Arrange the scores.
		_scorelists[gametype].sort(key = lambda x: x[9])
		_scorelists[gametype].sort(key = lambda x: x[10])
		_scorelists[gametype].sort(key = lambda x: x[8], reverse = True)
		# Remove the eleventh score.
		_scorelists[gametype].pop()
		_scorelists = _scorelists[0] + _scorelists[1] + _scorelists[2]
		for score in _scorelists:
			_scorefile.write(struct.pack('>ccccccccQLL', *score))

class MainMenu (Menu):
	""" 
		The MainMenu object represents the main menu of the game.

		The player is capable of starting the game selection, viewing the high score tables, and 
		changing the options.
	"""

	def __init__ (self, user, score_menu):
		bg = pygame.Surface((210, 300))
		bg.fill((0, 255, 0))
		super(MainMenu, self).__init__(user, bg, midtop = (screen.get_width() / 2, 250))
		self.score_menu = score_menu

		hmargin = 15 # horizontal margin in pixels
		tmargin = 20 # top margin in pixels
		spacing = 5 # space between selections in pixels
		height = 60 # height of selections in pixels

		self.selections = [[MenuSelection(self, 'play', 'Start Game', (self.rect.left + hmargin, self.rect.top + tmargin), (self.rect.width - 2 * hmargin, height)), 
							MenuSelection(self, 'hiscore', 'High Scores', (self.rect.left + hmargin, self.rect.top + tmargin + spacing + height), (self.rect.width - 2 * hmargin, height)), 
							MenuSelection(self, 'options', 'Options', (self.rect.left + hmargin, self.rect.top + tmargin + 2 * (spacing + height)), (self.rect.width - 2 * hmargin, height)), 
							MenuSelection(self, 'quit', 'Quit', (self.rect.left + hmargin, self.rect.top + tmargin + 3 * (spacing + height)), (self.rect.width - 2 * hmargin, height))]]
		self.set_range()

	def eval_input (self):
		event = super(MainMenu, self).eval_input()
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_z or event.key == pygame.K_RETURN:
				if self.get_selected(*self.selection).action == 'play':
					self.user.state = 'play_menu'
				elif self.get_selected(*self.selection).action == 'hiscore':
					self.user.state = 'view_scores'
					self.score_menu.scorelist = decode_scores()
				elif self.get_selected(*self.selection).action == 'options':
					pass
				elif self.get_selected(*self.selection).action == 'quit':
					self.user.state = 'quit'

	def run (self):
		menu_bg.draw(screen)
		self.draw(screen)
		super(MainMenu, self).run()
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
		bg.fill((0, 255, 64))
		super(PlayMenu, self).__init__(user, bg, midtop = (screen.get_width() / 2, 250))

		hmargin = 20
		spacing = 14
		tmargin = 20
		height = 80

		self.selections = [[MenuSelection(self, 'arcade', 'Arcade Mode', (self.rect.left + hmargin, self.rect.top + tmargin), ((self.rect.width - (2 * (spacing + hmargin))) / 3, height))], 
							[MenuSelection(self, 'timed', 'Timed Mode', (self.rect.left + hmargin + spacing + (self.rect.width - (2 * (spacing + hmargin))) / 3, self.rect.top + tmargin), ((self.rect.width - (2 * (spacing + hmargin))) / 3, height))],
							[MenuSelection(self, 'free', 'Free Mode', (self.rect.left + hmargin + 2 * spacing + (2 * (self.rect.width - (2 * (spacing + hmargin))) / 3), self.rect.top + tmargin), ((self.rect.width - (2 * (spacing + hmargin))) / 3, height))]]
		self.set_range()

	def eval_input (self):
		event = super(PlayMenu, self).eval_input()
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_z or event.key == pygame.K_RETURN:
				if self.get_selected(*self.selection).action == 'arcade':
					self.user.gametype = 'arcade'
				elif self.get_selected(*self.selection).action == 'timed':
					self.user.gametype = 'timed'
				elif self.get_selected(*self.selection).action == 'free':
					self.user.gametype = 'free'

				self.user.state = 'in_game'
				self.game.set_data()
				pygame.mixer.music.play()
				self.reset()
			elif event.key == pygame.K_x or event.key == pygame.K_ESCAPE:
				self.user.state = 'main_menu'

	def run (self):
		menu_bg.draw(screen)
		self.draw(screen)
		super(PlayMenu, self).run()
		pygame.display.flip()

class HiScoreMenu (Menu):
	"""
		The High Score Menu allows the player to view the recorded high scores in the file
		hiscore.dat, segregated by game time and arranged by score. Time played and number 
		of lines cleared are also displayed, along with the name of the score setter.

		Its selections are just switching between the scoreboards of the three different game modes.
	"""
	def __init__ (self, user):
		bg = pygame.Surface((700, 480))
		bg.fill((64, 192, 128))
		super(HiScoreMenu, self).__init__(user, bg, midbottom = (s_rect.centerx, s_rect.bottom - 25))
		self.font = pygame.font.SysFont(None, 30)

		self.selections = [[MenuSelection(self, 'arcade', ' ', s_rect.topright, (1, 1))],
							[MenuSelection(self, 'timed', ' ', s_rect.topright, (1, 1))],
							[MenuSelection(self, 'free', ' ', s_rect.topright, (1, 1))]]
		self.set_range()

	def eval_input (self):
		event = super(HiScoreMenu, self).eval_input()
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_x or event.key == pygame.K_ESCAPE:
				self.user.state = 'main_menu'

	def display_scores (self):
		self.render_text(self.get_selected(*self.selection).action.capitalize() + ' Mode', (0, 0, 0), midtop = (self.rect.centerx, self.rect.top + 30))
		self.render_text('Name:', (0, 0, 0), topleft = (self.rect.left + 25, self.rect.top + 70))
		self.render_text('Score:', (0, 0, 0), topleft = (self.rect.left + 185, self.rect.top + 70))
		self.render_text('Lines:', (0, 0, 0), topleft = (self.rect.left + 390, self.rect.top + 70))
		self.render_text('Time Taken:', (0, 0, 0), topleft = (self.rect.left + 560, self.rect.top + 70))
		d_scores = self.scorelist[self.selection[0]]
		for i in range(10):
			self.render_text('{}'.format(d_scores[i][0]), (0, 0, 0), topleft = (self.rect.left + 30, self.rect.top + 120 + i * 35))
			self.render_text('{}'.format(d_scores[i][1]), (0, 0, 0), topright = (self.rect.centerx - 30, self.rect.top + 120 + i * 35))
			self.render_text('{}'.format(d_scores[i][2]), (0, 0, 0), topright = (self.rect.right - 210, self.rect.top + 120 + i * 35))
			self.render_text('{}:{:02d}:{:02d}'.format(d_scores[i][3]//6000, d_scores[i][3]//100%60, d_scores[i][3]%100), (0, 0, 0), topright = (self.rect.right - 30, self.rect.top + 120 + i * 35))

	def run (self):
		menu_bg.draw(screen)
		self.draw(screen)
		super(HiScoreMenu, self).run()
		self.display_scores()
		pygame.display.flip()

class PauseMenu (Menu):
	"""
		Pauses the game.
		The timer doesn't run while paused.
	"""

	def __init__(self, user):
		self.pause_bg = pygame.Surface(screen.get_size())
		bg = pygame.Surface((250, 300))
		bg.fill((0, 255, 0))
		super(PauseMenu, self).__init__(user, bg, center = s_rect.center)
		
		tmargin = 20
		hmargin = 15
		spacing = 5
		height = 60

		self.selections = [[MenuSelection(self, 'resume', 'Resume Game', (self.rect.left + hmargin, self.rect.top + tmargin), (self.rect.width - 2 * hmargin, height)),
							MenuSelection(self, 'restart', 'Restart Game', (self.rect.left + hmargin, self.rect.top + tmargin + spacing + height), (self.rect.width - 2 * hmargin, height)),
							MenuSelection(self, 'options', 'Options', (self.rect.left + hmargin, self.rect.top + tmargin + 2 * (spacing + height)), (self.rect.width - 2 * hmargin, height)),
							MenuSelection(self, 'quit', 'Return to Menu', (self.rect.left + hmargin, self.rect.top + tmargin + 3 * (spacing + height)), (self.rect.width - 2 * hmargin, height))]]
		self.set_range()

	def set_bg (self, bg):
		self.pause_bg.blit(bg, (0, 0))

	def eval_input (self):
		event = super(PauseMenu, self).eval_input()
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_z or event.key == pygame.K_RETURN:
				if self.get_selected(*self.selection).action == 'resume':
					self.user.state = 'in_game'
					pygame.mixer.music.unpause()
					self.reset()
				if self.get_selected(*self.selection).action == 'restart':
					self.user.state = 'in_game'
					self.user.reset()
					self.game.set_data()
					restart_music()
					self.reset()
				elif self.get_selected(*self.selection).action == 'options':
					pass
				elif self.get_selected(*self.selection).action == 'quit':
					self.user.state = 'main_menu'
					self.user.reset()
					self.game.set_data()
					self.reset()
			elif event.key == pygame.K_x or event.key == pygame.K_ESCAPE:
				self.user.state = 'in_game'

	def run (self):
		screen.blit(self.pause_bg, (0, 0))
		self.draw(screen)
		super(PauseMenu, self).run()
		pygame.display.flip()

class SaveMenu (Menu):
	"""
		SaveMenu prompts the player to save a name to be attached to a high score, 
		if they would have a high score that beats one on the record.
	"""
	def __init__(self, user):
		bg = pygame.Surface((500, 150))
		bg.fill((12, 135, 205))
		super(SaveMenu, self).__init__(user, bg, center = s_rect.center)
		self.name = u''
		self.placestring = '10th'

	def render_place (self, _i):
		if _i == 0: self.placestring = '1st'
		elif _i == 1: self.placestring = '2nd'
		elif _i == 2: self.placestring = '3rd'
		else: self.placestring = str(_i + 1) + 'th'

	def eval_timer (self):
		return (300000 - self.user.timer) // 10 if self.user.gametype == 'timed' else self.user.timer // 10

	def eval_input (self):
		event = pygame.event.poll()
		if event.type == pygame.QUIT:
			self.user.state = 'quit'
		if event.type == pygame.KEYDOWN:
			if ((event.key >= pygame.K_a and event.key <= pygame.K_z) or (event.key == pygame.K_SPACE)) and len(self.name) < 8:
				self.name += event.unicode
			elif event.key == pygame.K_BACKSPACE:
				self.name = self.name[:-1]
			elif event.key == pygame.K_RETURN:
				if len(self.name) < 8: self.name += ' ' * (8 - len(self.name))
				encode_scores(self.user.gametype, list(str(self.name)) + [self.user.score, self.user.lines_cleared, self.eval_timer()])
				self.name = u''
				self.user.reset()
				self.user.state = 'loser'
			elif event.key == pygame.K_ESCAPE:
				self.name = u''
				self.user.reset()
				self.user.state = 'loser'

	def display_score (self):
		self.render_text('You got the '+self.placestring+' place high score!', (0, 0, 0), midtop = (self.rect.centerx, self.rect.top + 15))

		self.render_text('Enter Name:', (0, 0, 0), topleft = (self.rect.left + 15, self.rect.top + 40))
		self.render_text('Score:', (0, 0, 0), topright = (self.rect.centerx - 40, self.rect.top + 40))
		self.render_text('Lines:', (0, 0, 0), topleft = (self.rect.centerx + 40, self.rect.top + 40))
		self.render_text('Time Taken:', (0, 0, 0), topright = (self.rect.right - 25, self.rect.top + 40))

		self.render_text(self.name, (0, 0, 0), topleft = (self.rect.left + 20, self.rect.top + 65))
		self.render_text(str(self.user.score), (0, 0, 0), topright = (self.rect.centerx - 20, self.rect.top + 65))
		self.render_text(str(self.user.lines_cleared), (0, 0, 0), topleft = (self.rect.centerx + 100, self.rect.top + 65))
		_time = self.eval_timer()
		self.render_text('{}:{:02d}:{:02d}'.format(_time // 6000, _time // 100 % 60, _time % 100), (0, 0, 0), topright = (self.rect.right - 20, self.rect.top + 65))

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
		bg.fill((127, 127, 0))
		super(LossMenu, self).__init__(user, bg, center = s_rect.center)

		tmargin = 20
		hmargin = 15
		spacing = 5
		height = 60

		self.selections = [[MenuSelection(self, 'restart', 'Try Again?', (self.rect.left + hmargin, self.rect.top + tmargin + spacing + height), (self.rect.width - 2 * hmargin, height)),
							MenuSelection(self, 'options', 'Options', (self.rect.left + hmargin, self.rect.top + tmargin + 2 * (spacing + height)), (self.rect.width - 2 * hmargin, height)),
							MenuSelection(self, 'quit', 'Return to Menu', (self.rect.left + hmargin, self.rect.top + tmargin + 3 * (spacing + height)), (self.rect.width - 2 * hmargin, height))]]
		self.set_range()

	def set_bg (self, bg):
		self.loss_bg.blit(bg, (0, 0))

	def render_loss (self):
		self.loss_score = self.user.score

	def eval_input (self):
		event = super(LossMenu, self).eval_input()
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_z or event.key == pygame.K_RETURN:
				if self.get_selected(*self.selection).action == 'restart':
					self.user.state = 'in_game'
					self.user.reset()
					self.game.set_data()
					restart_music()
					self.reset()
				elif self.get_selected(*self.selection).action == 'options':
					pass
				elif self.get_selected(*self.selection).action == 'quit':
					self.user.state = 'main_menu'
					self.user.reset()
					self.game.set_data()
					self.reset()

	def run (self):
		screen.blit(self.loss_bg, (0, 0))
		self.draw(screen)
		self.render_text("Game Over!", (255, 255, 255), midtop = (self.rect.centerx, self.rect.top + 15))
		self.render_text("Your score was: " + str(self.loss_score), (255, 255, 255), midtop = (self.rect.centerx, self.rect.top + 40))
		super(LossMenu, self).run()
		pygame.display.flip()

class OptionMenu (Menu):
	"""
		The Options Menu allows the user to edit game settings for more convenient play.

		The selections of this menu are special, and change the states of global variables.
	"""
	def __init__(self, user):
		pass
