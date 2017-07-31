#!/usr/bin/env python

if __name__ == '__main__':
	import argparse
	import engine.game
	# Parse the optional arguments for the command line interface.
	parser = argparse.ArgumentParser(description="Tetris clone implemented using Pygame.")
	parser.add_argument('-d', '--debug', action='store_true', help="enables debug mode")
	# Run the game.
	tetris = engine.game.init(parser.parse_args())
	tetris.run()
else: raise ImportError("This file is not meant to be used as a module!")
