#!/usr/bin/env python

try:
	from engine import *
	print dir()
except ImportError, error:
	print "There has been a mistake: ", error

def main ():
	user = User()
	main_menu = MainMenu(user)
	play_menu = PlayMenu(user)
	pause_menu = PauseMenu(user)
	loss_menu = LossMenu(user)
	
	game = Tetris(user, pause_menu, loss_menu)
	pause_menu.game = game
	loss_menu.game = game

	while user.state != 'quit':
		clock.tick(60)
		if user.state == 'main_menu':
			main_menu.run()
		elif user.state == 'play_menu':
			play_menu.run()
		elif user.state == 'loser':
			loss_menu.run()
		elif user.state == 'paused':
			pause_menu.run()
		elif user.state == 'in_game':
			game.run()
	pygame.quit()
	sys.exit(1)
		
if __name__ == '__main__':
	main()
