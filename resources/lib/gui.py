#/*
# *      Copyright (C) 2010 lzoubek
# *
# *
# *  This Program is free software; you can redistribute it and/or modify
# *  it under the terms of the GNU General Public License as published by
# *  the Free Software Foundation; either version 2, or (at your option)
# *  any later version.
# *
# *  This Program is distributed in the hope that it will be useful,
# *  but WITHOUT ANY WARRANTY; without even the implied warranty of
# *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# *  GNU General Public License for more details.
# *
# *  You should have received a copy of the GNU General Public License
# *  along with this program; see the file COPYING.  If not, write to
# *  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
# *  http://www.gnu.org/copyleft/gpl.html
# *
# */
import sys,os,time
import xbmc,xbmcaddon,xbmcgui,xbmcplugin
import pmpd

#get actioncodes from keymap.xml
ACTION_CLOSE = [6,10,216,247,257,275,61448,61467]
ACTION_SELECT_ITEM = 7
# control IDs
STATUS = 100
PLAY = 668
PAUSE = 670
PREV = 666
STOP = 667
NEXT = 669 
REPEAT_OFF = 700
REPEAT_ON = 701
SHUFFLE_OFF = 702
SHUFFLE_ON = 703
CURRENT_PLAYLIST = 120
PROFILE=101

Addon = xbmcaddon.Addon(id=os.path.basename(os.getcwd()))

#String IDs
STR_STOPPED=Addon.getLocalizedString(30003)
STR_PAUSED=Addon.getLocalizedString(30004)
STR_NOT_CONNECTED=Addon.getLocalizedString(30005)
STR_CONNECTED_TO=Addon.getLocalizedString(30011) 
STR_PLAYING=Addon.getLocalizedString(30006) 
STR_PROFILE_NAME=Addon.getLocalizedString(30002)
STR_CONNECTING_TITLE=Addon.getLocalizedString(30015)
STR_DISCONNECTING_TITLE=Addon.getLocalizedString(30017) 
STR_GETTING_DATA=Addon.getLocalizedString(30016)      

class GUI ( xbmcgui.WindowXMLDialog ) :
	
	def __init__( self, *args, **kwargs ):
		self.client = pmpd.PMPDClient()
		self.client.register_callback(self._handle_changes)
		self.profile_id=args[3]
		self.profile_name=Addon.getSetting(self.profile_id+'_name')
		self.mpd_host = Addon.getSetting(self.profile_id+'_mpd_host')
		self.mpd_port = Addon.getSetting(self.profile_id+'_mpd_port')		
		
	def onFocus (self,controlId ):
		self.controlId=controlId

	def onInit (self ):
		self.getControl( PAUSE ).setVisible( False )
		self.getControl( PROFILE ).setLabel(STR_PROFILE_NAME+' : '+self.profile_name)		
		self._connect()
	def _connect(self):
		p = xbmcgui.DialogProgress()
		p.create(STR_CONNECTING_TITLE,STR_CONNECTING_TITLE+' '+self.mpd_host+':'+self.mpd_port)
		p.update(0)
		try:				
#			print 'Connecting  to  MPD ' + self.mpd_host + ':'+self.mpd_port 
			self.client.connect(self.mpd_host,int(self.mpd_port))
		except:
			self.getControl ( STATUS ).setLabel(STR_NOT_CONNECTED)
#			print 'Cannot connect'
			p.close()
			return
#		print 'Connected to  MPD v' + self.client.mpd_version
		self.getControl ( STATUS ).setLabel(STR_CONNECTED_TO +' '+self.mpd_host+':'+self.mpd_port )
		p.update(50,STR_GETTING_DATA)
		self._handle_changes(['playlist','player','options'])
		p.close()			

	def _handle_changes(self,changes):
		state = self.client.status()
#		print 'Handling changes - ' + str(changes)
		for change in changes:
			if change == 'player':
				current = self.client.currentsong()
				if state['state'] =='play':					
					self.toggleVisible( PLAY, PAUSE )
					self.getControl( STATUS ).setLabel(STR_PLAYING + ' : ' + self.currentSong(current))
					self.update_playlist('play',current)
				elif state['state'] == 'pause':
					self.toggleVisible( PAUSE, PLAY )
					self.getControl( STATUS ).setLabel(STR_PAUSED + ' : ' + self.currentSong(current))
					self.update_playlist('pause',current)
				elif state['state'] == 'stop':
					self.getControl( STATUS ).setLabel(STR_STOPPED)
					self.toggleVisible( PAUSE, PLAY )
					self.update_playlist('stop',current)
			if change == 'options':
				if state['repeat'] == '0':
					self.toggleVisible( REPEAT_ON, REPEAT_OFF )
				elif state['repeat'] == '1':
					self.toggleVisible( REPEAT_OFF, REPEAT_ON )
				if state['random'] == '0':
					self.toggleVisible( SHUFFLE_ON, SHUFFLE_OFF )
				elif state['random'] == '1':
					self.toggleVisible( SHUFFLE_OFF, SHUFFLE_ON )					
			if change == 'playlist':
					playlist = self.client.playlistinfo()
					current = self.client.currentsong()					
					self.update_fields(current,['id'])
					current_id = current['id']
					self.getControl( CURRENT_PLAYLIST ).reset()					
					index = 0
					for item in playlist:
						self.update_fields(item,['title','artist','album','time'])
						listitem = xbmcgui.ListItem( label=item['title'])
						listitem.setProperty( 'index', str(index))						
						listitem.setProperty( 'id', item['id'] )						
						listitem.setProperty( 'artist', item['artist'] )
						listitem.setProperty( 'album', item['album'] )
						if not item['time'] == '':
							listitem.setProperty( 'time', time.strftime("%M:%S",time.gmtime(float(item['time']))) )
						if item['title'] == '' and item['artist'] == '' and item['album'] == '':
							listitem.setProperty( 'file' , item['file'] )
						if item['id'] == current_id:
							listitem.setIconImage(state['state']+'-item.png')						
						self.getControl( CURRENT_PLAYLIST ).addItem( listitem )
						index  = index + 1
#		print 'Changes handled'

	def toggleVisible(self,cFrom,cTo):
		self.getControl( cFrom ).setVisible(False)
		self.getControl( cTo ).setVisible(True)
	
	def update_fields(self,obj,fields):
		for field in fields:
			if not field in obj:
				obj[field]=''

	def currentSong(self,current) :
		self.update_fields(current,['artist','album','title'])
		if current['title'] == '' and current['artist'] == '' and current['album'] == '':
			return current['file']
		return current['artist'] + ' - ' + current['album'] + ' - ' + current['title'] 

	def update_playlist(self,state,current) :
		self.update_fields(current,['id'])		
		itemid = current['id']
		playlist = 	self.getControl(CURRENT_PLAYLIST)
		for i in range(0,playlist.size()):
			item = playlist.getListItem(i)
			item.setIconImage('')
			if item.getProperty('id') == itemid:
				item.setIconImage(state+'-item.png')
				playlist.selectItem(int(item.getProperty('index')))		
							
	def onAction(self, action):
#		print 'OnAction '+str(action)
		if action.getButtonCode() in ACTION_CLOSE:
			self.disconnect()			
			self.close()
	def disconnect(self):
		p = xbmcgui.DialogProgress()
		p.create(STR_DISCONNECTING_TITLE)
		p.update(0)
		self.client.disconnect()
		p.close()
			
	def onClick( self, controlId ):
		try:
			if controlId == PLAY:
				self.client.play()
			elif controlId == STOP:
				self.client.stop()
			elif controlId == PAUSE:
				self.client.pause()
			elif controlId == NEXT:
				self.client.next()
			elif controlId == PREV:
				self.client.previous()
			elif controlId == REPEAT_OFF:
				self.client.repeat(1)
			elif controlId == REPEAT_ON:
				self.client.repeat(0)
			elif controlId == SHUFFLE_OFF:
				self.client.random(1)
			elif controlId == SHUFFLE_ON:
				self.client.random(0)				
			elif controlId == CURRENT_PLAYLIST:
				print self.getControl( CURRENT_PLAYLIST ).getSelectedItem().getLabel()
				seekid = self.getControl( CURRENT_PLAYLIST ).getSelectedItem().getProperty('id')
				status = self.client.status()
				if status['state'] == 'play' and status['songid'] == seekid:
					self.client.pause()
				elif status['state'] == 'pause' and status['songid'] == seekid:
					self.client.play()
				else:	
					self.client.seekid(seekid,0) 
		except mpd.ProtocolError:
			self.disconnect()
			self.getControl( STATUS ).setLabel(STR_NOT_CONNECTED)
		except mpd.ConnectionError:
			self.disconnect()
			self.getControl( STATUS ).setLabel(STR_NOT_CONNECTED)

