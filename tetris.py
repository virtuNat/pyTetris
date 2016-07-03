#!/usr/bin/env python

try:
	from engine import *
except ImportError, error:
	print "There has been a mistake: ", error

def main ():
	user = User()
	main_menu = MainMenu(user)
	play_menu = PlayMenu(user)
	pause_menu = PauseMenu(user)
	game = Tetris(user, pause_menu)
	pause_menu.game = game

	while user.state != 'quit':
		clock.tick(30)
		if user.state == 'main_menu':
			main_menu.run()
		elif user.state == 'play_menu':
			play_menu.run()
		elif user.state == 'paused':
			pause_menu.run()
		elif user.state == 'in_game':
			game.run()
	pygame.quit()
	sys.exit(2)
		
if __name__ == '__main__':
	main()
