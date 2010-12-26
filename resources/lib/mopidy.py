import rmpd,select,threading,traceback,mpd,time,Queue

# polling MPD Client - combatible with mopidy
class MopidyMPDClient(object):
	def __init__(self,poll_time=False):
		self.client = rmpd.RMPDClient()
		self.poller = rmpd.RMPDClient()
		self.time_poller = rmpd.RMPDClient()
		self.callback = None
		self.thread = threading.Thread(target=self._poll)
		self.thread.setDaemon(True)
		self.event = threading.Event()
		self.executed_commands= Queue.Queue()
		self.rec = False
		self.recored = []
		self.time_callback = None
		self._permitted_commands = []
		self.time_thread = None
		self.time_event = None
		if poll_time:
			self.time_thread = threading.Thread(target=self._poll_time)
			self.time_thread.setDaemon(True)
			self.time_event = threading.Event()
		
	def register_callback(self,callback):
		self.callback = callback
	def register_time_callback(self,callback):
		self.time_callback=callback;
	# need to call try_command before passing any commands to list!	
	def command_list_ok_begin(self):
		self.rec = True
		self.recorded = []
		self.client.command_list_ok_begin()
	
	def command_list_end(self):
		self.rec = False
		records = list(set(self.recorded))
		for record in records:
			self._simulate_idle(record)
		return self.client.command_list_end()

	def try_command(self,command):
		if not command in self._permitted_commands:
			raise mpd.CommandError('No Permission for :'+command)
	def __getattr__(self,attr):
		if not attr in self._permitted_commands:
			raise mpd.CommandError('No Permission for :'+attr)
		if self.rec:
			self.recorded.append(attr)
		else:
			self._simulate_idle(attr)
		return self.client.__getattr__(attr)

	def _simulate_idle(self,command):
		if command in ['play','stop','seekid','next','previous','pause']:
			self.executed_commands.put('player')
		elif command in ['consume','repeat','random']:
			self.executed_commands.put('options')
		elif command in ['setvol']:
			self.executed_commands.put('mixer')
		elif command in ['clear','add','load','deleteid']:
			self.executed_commands.put('playlist')
		elif command in ['rm','save']:
			self.executed_commands.put('stored_playlist')
		
	def connect(self,host,port,password=None):
		self.client.connect(host,port)		
		self.poller.connect(host,port)
		if not password==None:
			self.client.password(password)
		self._permitted_commands = self.client.commands()
		self.thread.start()
		if not self.time_thread == None:
			self.time_poller.connect(host,port)
			self.time_thread.start()
		
	def disconnect(self):
		print 'disconnecting'
		self.callback = None
		try:
			self.client.close()
		except:
			pass
		try:
			self.client.disconnect()
		except:
			pass
		try:
			self.poller.close()
		except:
			pass
		try:
			self.poller.disconnect()
		except:
			pass
		try:
			print 'waiting for poller thread'
			if self.thread.isAlive():
				self.event.set()
				self.executed_commands.put('exit')
				self.thread.join(3)
				self.event=None
			print 'done'
		except:
			traceback.print_exc()				

		if not self.time_thread == None:
			print 'disconnecting time poller'
			try:
				self.time_poller.close()
			except:
				pass
			try:
				self.time_poller.disconnect()
			except:
				pass
			try:
				print 'waiting for time poller thread'
				if self.time_thread.isAlive():
					self.time_event.set()
					self.time_thread.join(3)
					self.time_event=None
				print 'done'
			except:
				traceback.print_exc()
		print 'client disconnected'
		
	def _poll_time(self):
		print 'Starting time poller thread'
		while 1:
			try:
				status = self.time_poller.status()
				if not status['state'] == 'play':
					self.time_event.wait(5)
				else:
					self.time_callback(self.time_poller,status)
					self.time_event.wait(0.9)
				if self.time_event.isSet():
#					print 'poller exited on event'
					break;
			except:
#				print "time poller error"
#				traceback.print_exc()
				self.time_event.set()
				return
	def _poll(self):
		print 'Starting poller thread'
		while 1:
			try:
				item = 	self.executed_commands.get()
				self.event.wait(0.2)
				self.callback(self.poller,[item])
				if self.event.isSet():
#					print 'poller exited on event'
					break;
			except:
				print "Poller error"
				traceback.print_exc()
				return
