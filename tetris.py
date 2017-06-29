#!/usr/bin/env python

class TetrisGame (object):
	"""
	Attempt at an OOP approach to running the game instance.

	Probably not the most elegant way of doing it...
	"""
	def __init__ (self):
		# Initialize game environment.
		try:
			import engine
		except ImportError as error:
			print("The tetris grid got fucking clogged:")
			raise
		# Instantiate game instance data.
		self.__dict__.update(engine.init())
		print(self.__dict__)

	def run (self):
		# Run the program loop. 
		# User state system allows menu changing to be as simple as running an eval()
		# as long as the state name matches a menu variable name.
		while self.user.state != 'quit':
			self.clock.tick(60)
			eval('self.' + self.user.state).run()
		# Clean up when the program ends.
		self.quit()
		
if __name__ == '__main__':
	tetris = TetrisGame()
	tetris.run()
