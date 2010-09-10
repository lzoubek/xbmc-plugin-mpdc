import rmpd,select,threading

# polling MPD Client
class PMPDClient(object):
	def __init__(self):
		self.client = rmpd.RMPDClient()
		self.poller = rmpd.RMPDClient()
		self.callback = None
		self.thread = threading.Thread(target=self._poll)
		self.thread.setDaemon(True)
		
	def register_callback(self,callback):
		self.callback = callback
		
		
	def __getattr__(self,attr):
		return self.client.__getattr__(attr)
		
	def connect(self,host,port,password=None):
		self.client.connect(host,port)		
		self.poller.connect(host,port)
		if not password==None:
			self.poller.password(password)
			self.client.password(password)
		self.thread.start()
		
	def disconnect(self):
#		print 'disconnecting'
		try:
			self.client.close()
		except:
			pass
		try:
			self.client.disconnect()
		except:
			pass
		try:
			self.poller.noidle()
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
#		print 'client disconnected'
		
	def _poll(self):
		while 1:
			self.poller.send_idle()
			select.select([self.poller],[],[],1)
			try:
				changes = self.poller.fetch_idle()
			except:
#				print "poller error"
				return
			try:
				if not self.callback == None:
					self.callback(changes)
			except:
#				print "callback error"
				return
				
