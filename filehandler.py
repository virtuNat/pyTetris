# File handling classes.

class SFH:
	"""
	SFH, or ScoreFileHandler is a class that is built to, as the name suggests, 
	handle score file data.

	It's a context manager inteded to be used with the built-in with statement 
	to handle saving and pulling of score data safely.

	To use this, do:
	with SFH(scorefilename) as sfh: 
		# Do scorefile operations...

	Do note that sfh is a reference to the context manager object itself, not the 
	file object. The file object is referenced under the sfile attribute.
	"""

	def __init__ (self, name = 'hiscore.dat'):
		name = os.path.join('data', name)
		# The backup file is there to ensure that the data is preserved in some cases of fucketry.
		# Note: Does not work if the backup file itself is fucked with.
		try:
			self.bckup = open(name[:-3] + 'bak', 'rb+')
			# Since the backup exists, check if the data exists too.
			try:
				self.sfile = open(name, 'rb+')
			except IOError:
				# If the scorefile data is missing, but the backup still exists, use the backup to restore it.
				self.sfile = open(name, 'wb+')
				self.load()
		except IOError:
			self.bckup = open(name[:-3] + 'bak', 'wb+')
			# If the backup is missing, check if the original score data exists.
			try:
				self.sfile = open(name, 'rb+')
				self.backup()
			except IOError:
				self.sfile = open(name, 'wb+')
				self.reset()
		finally:
			self.bckup.seek(0)
			self.sfile.seek(0)
		# If this flag is False, then the backup file is assumed to be valid when a reading exception is thrown.
		self.eflag = False

	def __repr__ (self):
		return "<Score file context manager with id "+str(id(self))+">"

	def backup (self):
		# Update the backup.
		self.sfile.seek(0)
		self.bckup.seek(0)
		self.bckup.truncate()
		self.bckup.write(self.sfile.read())

	def load (self):
		# Refresh the scorefile using the backup.
		self.sfile.seek(0)
		self.bckup.seek(0)
		self.sfile.truncate()
		self.sfile.write(self.bckup.read())

	def reset (self):
		# Resets the given scorefile to the default data.
		self.sfile.seek(0)
		self.sfile.truncate()
		for i in range(3):
			for j in range(10):
				# Alexey Leonidovich Pajitnov is the developer of the original Tetris.
				score = [c.encode() for c in 'Pajitnov'] + [0, 0, 0]
				self.sfile.write(struct.pack('>ccccccccQLL', *score))
		self.backup()

	def validate (self):
		# Load from the backup file or reset both files based on the error state.
		if not self.eflag:
			# The backup hasn't been verified to be invalid yet, load from backup.
			self.load()
			self.eflag = True
		else:
			# The backup is also invalid, reset both files.
			self.reset()
			self.eflag = False

	def decode (self, splitname = False):
		# Read the scorefile, and return 3 lists of top ten score lists.
		self.sfile.seek(0, 2)
		if self.sfile.tell() != 720:
			# If the number of bytes are wrong, then the score file is probably wrong.
			# Load from the backup, but if that fails, remake the score file.
			self.validate()
			print('Scorefile length is invalid!')
			return self.decode()
		self.sfile.seek(0)
		try:
			# Each score is a set of 24 bytes, the first eight of which stand for the name entered.
			scorelists = [struct.unpack('>ccccccccQLL', self.sfile.read(24)) for i in range(30)]
		except struct.error as e:
			# If an exception is thrown during reading, first attempt to load from the backup.
			# If that still fails, reset the scores (erasing score data, whoops).
			self.validate()
			# Echo exception details to the console.
			print(e)
			return self.decode()
		if not splitname:
			# The splitname argument is True when the data needs to be read raw, rather than formatted for easy display.
			scorelists = [[scorelists[i][j].decode() if j < 8 else scorelists[i][j] for j in range(11)] for i in range(30)]
			scorelists = [[''.join(scorelists[i][:8]), scorelists[i][8], scorelists[i][9], scorelists[i][10]] for i in range(30)]
		return [scorelists[:10], scorelists[10:20], scorelists[20:]]

	def encode (self, gtype, entry):
		# Add a new score to the high scores.
		g = 0 if gtype == 'arcade' else 1 if gtype == 'timed' else 2
		# Grab the score data.
		slists = self.decode(True)
		# Add the new entry.
		for i in range(8): entry[i] = bytes(entry[i])
		slists[g].append(entry)
		# Sort the entries.
		# Lines cleared third.
		slists[g].sort(key = lambda s: s[9])
		# Time second.
		slists[g].sort(key = lambda s: s[10])
		# Score first.
		slists[g].sort(key = lambda s: s[8], reverse = True)
		# Remove the old last entry and re-arrange the score lists into a single list.
		slists[g].pop()
		slists = slists[0] + slists[1] + slists[2]
		# Apply change to scorefile.
		self.sfile.seek(0)
		self.sfile.truncate()
		for score in slists: self.sfile.write(struct.pack('>ccccccccQLL', *score))
		# Backup the entered score.
		self.backup()

	def __enter__ (self):
		# The value that will be returned to the as statement.
		return self

	def __exit__ (self, etype, evalue, tback):
		# Cleanup both files.
		self.bckup.close()
		self.sfile.close()
