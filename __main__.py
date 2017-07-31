#!/usr/bin/env python
		
if __name__ == '__main__':
	try: 
		import engine
	except ImportError: 
		print("The tetris grid got fucking clogged:")
		raise
	tetris = engine.init()
	tetris.run()
