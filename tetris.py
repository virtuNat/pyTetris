#!/usr/bin/env python

def main ():
	# Initialize objects.
	user = User()
	score_menu = HiScoreMenu(user)
	main_menu = MainMenu(user, score_menu)
	play_menu = PlayMenu(user)
	pause_menu = PauseMenu(user)
	save_menu = SaveMenu(user)
	loss_menu = LossMenu(user)
	game = Tetris(user, pause_menu, save_menu, loss_menu)
	# Some menus need to use game variables.
	play_menu.game = game
	pause_menu.game = game
	loss_menu.game = game
	# Run the program loop. 
	# User state system allows for easy changing between game states, but requires relevent menus be loaded at all times.
	# Probably ridiculously memory inefficient, but Python isn't very memory efficient anyway.
	while user.state != 'quit':
		clock.tick(60)
		if user.state == 'main_menu':
			main_menu.run()
		elif user.state == 'play_menu':
			play_menu.run()
		elif user.state == 'view_scores':
			score_menu.run()
		elif user.state == 'options':
			pass
		elif user.state == 'in_game':
			game.run()
		elif user.state == 'paused':
			pause_menu.run()
		elif user.state == 'save_scores':
			save_menu.run()
		elif user.state == 'loser':
			loss_menu.run()		
		
	# Clean up when the program ends.
	pygame.quit()
	sys.exit(1)
		
if __name__ == '__main__':
	try:
		from engine import *
	except ImportError as error:
		print("There has been a mistake: ", error)
	main()
