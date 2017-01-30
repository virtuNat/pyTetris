# Stores individual menu data.
try:
	from runtime import *
except ImportError, error:
	print "Runtime has fucking failed:", error

menu_bg = AnimatedSprite(pygame.Surface(screen.get_size()))
menu_bg.image.fill((0, 128, 128))

class MainMenu (Menu):
	""" 
		The MainMenu object represents the main menu of the game.

		The player is capable of starting the game selection, viewing the high score tables, and 
		changing the options.
	"""

	def __init__ (self, user):
		bg = pygame.Surface((210, 300))
		bg.fill((0, 255, 0))
		super(MainMenu, self).__init__(user, bg)
		self.set(midbottom = (screen.get_width() / 2, screen.get_rect().bottom - 25))

		hmargin = 15 # horizontal margin in pixels
		tmargin = 20 # top margin in pixels
		spacing = 5 # space between selections in pixels
		height = 60 # height of selections in pixels

		self.selections = [[MenuSelection(self, 'play', 'Start Game', (self.rect.left + hmargin, self.rect.top + tmargin), (self.rect.width - 2 * hmargin, height)), 
							MenuSelection(self, 'score', 'High Scores', (self.rect.left + hmargin, self.rect.top + tmargin + spacing + height), (self.rect.width - 2 * hmargin, height)), 
							MenuSelection(self, 'options', 'Options', (self.rect.left + hmargin, self.rect.top + tmargin + 2 * (spacing + height)), (self.rect.width - 2 * hmargin, height)), 
							MenuSelection(self, 'quit', 'Quit', (self.rect.left + hmargin, self.rect.top + tmargin + 3 * (spacing + height)), (self.rect.width - 2 * hmargin, height))]]
		self.set_range()

	def eval_input (self):
		event = super(MainMenu, self).eval_input()
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_z or event.key == pygame.K_RETURN:
				if self.get_selected(*self.selection).action == 'play':
					self.user.state = 'play_menu'
				elif self.get_selected(*self.selection).action == 'score':
					pass
				elif self.get_selected(*self.selection).action == 'options':
					pass
				elif self.get_selected(*self.selection).action == 'quit':
					self.user.state = 'quit'

	def run (self):
		menu_bg.blit_to(screen)
		self.blit_to(screen)
		super(MainMenu, self).run()
		pygame.display.flip()

class PlayMenu (Menu):
	""" 
		PlayMenu is the selection menu after "Start Game" is selected, it provides the player 
		with the available modes of play.

		Arcade Mode is standard Tetris, with increasing levels dependent on cleared lines. The 
		speed of the tetrominos dropping increase with the levels, up to a maximum. Score earned 
		per line cleared increases with level.

		Timed Mode is based on a timer that runs down. Clearing lines will freeze the timer for a 
		certain amount of time depending on the number of lines cleared and the clearing chain. 
		Score earned is based on total time taken in addition to lines cleared.
	"""

	def __init__(self, user):
		bg = pygame.Surface((480, 300))
		bg.fill((0, 255, 64))
		super(PlayMenu, self).__init__(user, bg)
		self.set(midbottom = (screen.get_width() / 2, screen.get_rect().bottom - 100))

		hmargin = 20
		spacing = 14
		tmargin = 20
		height = 80

		self.selections = [[MenuSelection(self, 'arcade', 'Arcade Mode', (self.rect.left + hmargin, self.rect.top + tmargin), ((self.rect.width - (2 * (spacing + hmargin))) / 3, height))], 
							[MenuSelection(self, 'time', 'Timed Mode', (self.rect.left + hmargin + spacing + (self.rect.width - (2 * (spacing + hmargin))) / 3, self.rect.top + tmargin), ((self.rect.width - (2 * (spacing + hmargin))) / 3, height))],
							[MenuSelection(self, 'free', 'Free Mode', (self.rect.left + hmargin + 2 * spacing + (2 * (self.rect.width - (2 * (spacing + hmargin))) / 3), self.rect.top + tmargin), ((self.rect.width - (2 * (spacing + hmargin))) / 3, height))]]
		self.set_range()

	def eval_input (self):
		event = super(PlayMenu, self).eval_input()
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_z or event.key == pygame.K_RETURN:
				if self.get_selected(*self.selection).action == 'arcade':
					self.user.state = 'in_game'
					self.user.gametype = 'arcade'
					self.game.set_data()
					self.reset()
				elif self.get_selected(*self.selection).action == 'time':
					self.user.state = 'in_game'
					self.user.gametype = 'time'
					self.game.set_data()
					self.reset()
				elif self.get_selected(*self.selection).action == 'free':
					self.user.state = 'in_game'
					self.user.gametype = 'free'
					self.game.set_data()
					self.reset()
			elif event.key == pygame.K_x or event.key == pygame.K_ESCAPE:
				self.user.state = 'main_menu'

	def run (self):
		menu_bg.blit_to(screen)
		self.blit_to(screen)
		super(PlayMenu, self).run()
		pygame.display.flip()

class PauseMenu (Menu):
	"""
		Pause the game.
	"""

	def __init__(self, user):
		self.pause_bg = pygame.Surface(screen.get_size())
		bg = pygame.Surface((250, 300))
		bg.fill((0, 255, 0))
		super(PauseMenu, self).__init__(user, bg)
		self.set(center = screen.get_rect().center)
		
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
					self.reset()
				if self.get_selected(*self.selection).action == 'restart':
					self.user.state = 'in_game'
					self.user.reset()
					self.game.set_data()
					self.reset()
				elif self.get_selected(*self.selection).action == 'quit':
					self.user.state = 'main_menu'
					self.user.reset()
					self.game.set_data()
					self.reset()
			elif event.key == pygame.K_x or event.key == pygame.K_ESCAPE:
				self.user.state = 'in_game'

	def run (self):
		screen.blit(self.pause_bg, (0, 0))
		self.blit_to(screen)
		super(PauseMenu, self).run()
		pygame.display.flip()

class LossMenu (Menu):
	"""
		When you lose the game, this menu pops up to show your score and let you try for a higher one.
	"""
	def __init__ (self, user):
		self.loss_bg = pygame.Surface(screen.get_size())
		bg = pygame.Surface((250, 300))
		bg.fill((127, 0, 0))
		super(LossMenu, self).__init__(user, bg)
		self.set(center = screen.get_rect().center)

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
					self.reset()
				elif self.get_selected(*self.selection).action == 'quit':
					self.user.state = 'main_menu'
					self.reset()
					self.game.set_data()
					self.reset()

	def run (self):
		screen.blit(self.loss_bg, (0, 0))
		self.blit_to(screen)
		self.render_text("Game Over!", (255, 255, 255), midtop = (self.rect.centerx, self.rect.top + 10))
		self.render_text("Your score was: " + str(self.loss_score), (255, 255, 255), midtop = (self.rect.centerx, self.rect.top + 30))
		super(LossMenu, self).run()
		pygame.display.flip()
