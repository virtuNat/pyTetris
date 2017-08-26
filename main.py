#!/usr/bin/env python
"A PyGame-made Tetris Clone for learning purposes."
__url__ = "https://github.com/virtuNat/pyTetris"
__author__ = "virtuNat"
__license__ = "GPL"
__version__ = "1.1.9"

if __name__ == '__main__':
	import argparse
	import engine.game
	# Parse the optional arguments for the command line interface.
	parser = argparse.ArgumentParser(description="Tetris clone implemented using Pygame.")
	parser.add_argument('-d', '--debug', action='store_true', help="enables debug mode")
	# Run the game.
	tetris = engine.game.init(parser.parse_args())
	tetris.run()
