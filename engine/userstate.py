"Contains class definitions for objects that track play state."

class User:
	"""
	The User class tracks global game state values, such as
	plot flags, difficulty, game internal state, etc.

	In this case, it tracks tetris difficulty values and handles score data.
	"""
	# Score data.
	drop_score = 1. # The base score added when a block lands.
	dist_factor = 0.6 # The multiplier per unit distance dropped by a piece in a soft or hard drop.
	line_score = 500. # The base score added when a line is cleared.
	line_factor = 0.8 # The added percentage for each line cleared in one drop.
	cascade_factor = 1.3 # The multiplier for each set of lines cleared successively. Exponential.
	twist_factor = 2.7 # The multiplier if the starting piece was twisted in.
	tspin_factor = 1.8 # The multiplier if it was a successful T-spin.
	combo_factor = 1.6 # The multiplier for subsequent drop clears.
	clear_factor = 2. # The multiplier if the entire matrix was cleared by this piece.

	def __init__ (self, argv):
		# Global state variables.
		self.state = 'main_menu'
		self.gametype = 'free'
		# Eventually will be modifiable in the Options Menu.
		# Default settings are good for Modern Tetris.
		# Retro Tetris would use cleartype 0, enablekicks, showghost, and linktiles False.
		self.cleartype = 2 # Determines line clear type, refer to Grid.clear_lines().
		self.enablekicks = True # Determines if wall kicks are allowed.
		self.showghost = True # Determines if the ghost tetrimino will be shown.
		self.linktiles = True # Determines if the blocks will use connected textures.

		self.hard_flag = False # True if the piece was hard-dropped.
		self.twist_flag = False # True if the tetrimino twisted into place.
		self.tspin_flag = False # True if a T-spin occured.
		self.resetgame = False # True if the game needs to be reset.
		# argv is an argparse.Namespace object that defines special behavior for testing purposes.
		if argv is not None:
			self.debug = argv.debug # Debug mode: cheats on!
		else:
			self.debug = False
		self.reset()

	def __str__ (self):
		return "<User instance running the '"+self.state+"' state.>"

	def __repr__ (self):
		return self.__str__()

	def reset (self):
		# Reset data when starting a new game.
		self.score = 0 # Score value for the current game.
		self.last_score = 0 # Score value for the last clear.
		self.line_list = [0] # Tracks how many lines are cleared in a single clearing chain.
		self.lines_cleared = 0 # Total number of lines cleared in the game.
		self.level = 1 # Current level in arcade mode.
		self.timer = 0 # How long the game has been playing.

		self.combo_ctr = 0 # Current combo number.
		self.current_combo = 1. # The current combo multiplier.

	def add_score (self, value):
		# Shortcut adder alias.
		self.score += int(value)

	def eval_drop_score (self, posdif=0):
		# Add score value when piece is dropped.
		if self.state != 'loss_menu':
			if self.hard_flag:
				self.add_score(self.drop_score + (self.dist_factor*posdif))
				self.hard_flag = False
			else:
				self.add_score(self.drop_score + (self.dist_factor*posdif/3.))

	def predict_score (self, clearflag):
		# Evaluate clear line combo score value, but don't add it yet.
		if len(self.line_list) > 1 and self.line_list[-1] == 0:
			self.line_list.pop()
		temp_score = 0
		# In arcade mode, level boosts score earned by line clears.
		linescore = self.line_score
		if self.gametype == 'arcade':
			linescore += self.level * 2.5
		# Calculate base score from number of cascades and number of lines cleared per cascade.
		for line in self.line_list:
			temp_score += linescore * line * (1 + (self.line_factor * (line-1)))
		temp_score *= (self.cascade_factor ** (len(self.line_list)-1)) * self.current_combo
		# Increase score for twists.
		if self.twist_flag:
			temp_score *= self.twist_factor
		# Increase score for T-spins.
		if self.tspin_flag:
			temp_score *= self.tspin_factor
		# Increase score for perfect clears.
		if clearflag:
			temp_score *= self.clear_factor
		# Increase score as timer goes down in timed mode.
		if self.gametype == 'timed':
			temp_score *= 1 + float(300 - (self.timer//1000))/100
		return int(round(temp_score / 50, 0) * 50)

	def eval_clear_score (self, clearflag):
		# Evaluates the score gain from the last line clear.
		if len(self.line_list) > 1 or self.line_list[0] > 0:
			# Add the clear line score.
			self.lines_cleared += sum(self.line_list)
			self.last_score = self.predict_score(clearflag)
			self.add_score(self.last_score)
			# Increment combo counter.
			self.combo_ctr += 1
			self.current_combo = self.combo_factor ** self.combo_ctr
		else:
			# If no lines were cleared, break combo.
			self.current_combo = 1.0
			self.combo_ctr = 0

	def eval_level (self):
		# Evaluate current arcade level.
		if self.lines_cleared <= 640: # Up to level 64, increment every 10 lines.
			self.level = self.lines_cleared // 10
		elif self.lines_cleared <= 1920: # Up to level 128, increment every 20 lines.
			self.level = 63 + ((self.lines_cleared - 640) // 20)
		elif self.lines_cleared <= 3840: # Up to level 192, increment every 30 lines.
			self.level = 127 + ((self.lines_cleared - 1920) // 30)
		elif self.lines_cleared <= 6400: # Up to level 256, increment every 40 lines.
			self.level = 191 + ((self.lines_cleared - 3840) // 40)
		else: self.level = 256
