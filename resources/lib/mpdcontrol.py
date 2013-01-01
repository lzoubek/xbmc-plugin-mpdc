# -*- coding: utf-8 -*-
#/*
# *      Copyright (C) 2013 Libor Zoubek
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
import xbmcaddon,xbmcplugin,xbmc,xbmcgui
import os,sys
import mpdutil as util

__addon__ = xbmcaddon.Addon(id='plugin.audio.mpdc')
__str__ = __addon__.getLocalizedString
__sett__ = __addon__.getSetting

class MPDQueue(object):
    def __init__(self,key,client):
        self.mpd = client
        self.key = key

    def run(self,params):
        print params
        action = params[self.key]
        if 'list' == action:
            self.list()
        elif 'play' == action:
            return self.play(params['id'])
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def play(self,id):
        self.mpd.seekid(id,0)
        xbmc.executebuiltin('Container.Refresh')

    def list(self):
        playlist = self.mpd.playlistinfo()
        print playlist
        current = util.fix_keys(self.mpd.currentsong(),['id'])
        for item in playlist:
            info = util.get_info_labels_from_queued_item(item)
            title = util.format_song(info)
            if current['id'] == item['id']:
                title = '* %s' % title
            util.add_song(title,{self.key:'play','id':item['id']},infoLabels=info,menuItems={})

class MPDControl(object):
    def __init__(self,key,client):
        self.mpd = client
        self.key = key

    def run(self,params):
        print params
        action = params[self.key]
        if 'list' == action:
            self.list()
        elif 'play_stream' == action:
            return self.play_stream()
        elif 'play' == action:
            self.mpd.play()
            return self.refresh()
        elif 'stop' == action:
            self.mpd.stop()
            return self.refresh()
        elif 'pause' == action:
            self.mpd.pause()
            return self.refresh()
        elif 'next' == action:
            self.mpd.next()
            return self.refresh()
        elif 'prev' == action:
            self.mpd.previous()
            return self.refresh()
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def refresh(self):
        xbmc.executebuiltin('Container.Refresh')
        util.notify_status(self.mpd)

    def list(self):
        status = self.mpd.status()
        print status
        print self.mpd.currentsong()
        if status['state'] == 'pause' or status['state'] == 'stop':
            util.add_song('Play',{self.key:'play'})
        else:
            util.add_song('Pause',{self.key:'pause'})

        util.add_song('Stop',{self.key:'stop'})
        util.add_song('Next',{self.key:'next'})
        util.add_song('Previous',{self.key:'prev'})
        if not __sett__('stream_url') == '' and status['state'] == 'play':
            util.add_song(__str__(30039),{self.key:'play_stream'},playable='true')

    def get_stream(self):
        stream_url = __sett__('stream_url')
        if not stream_url.startswith('http://'):
            stream_url= 'http://'+stream_url
        return stream_url

    def play_stream(self):
        stream = self.get_stream()
        print 'Plaing MPD Stream '+stream
        li = xbmcgui.ListItem(path=stream,iconImage='DefaulAudio.png')
        return xbmcplugin.setResolvedUrl(int(0), True, li)

class MPDArtists(object):
    def __init__(self,key,client):
        self.mpd = client
        self.key = key

    def run(self,params):
        print params
        action = params[self.key]
        if 'list' == action:
            self.list_artists()
        elif 'artist' == action:
            self.list_albums(params['name'])
        elif 'album' == action:
            self.list_tracks(params['art'],params['name'])
        elif 'queue_add' == action or 'queue_repl' == action:
            return self.add_to_queue(params)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def add_to_queue(self,params):
        print params
        if params[self.key] == 'queue_repl':
            # replacing queue
            self.mpd.stop()
            self.mpd.clear()
        if 'file' in params.keys():
            self.mpd.add(params['file'])
            util.notify(params['file'],__str__(30018))
            return
        if 'art' in params.keys():
            files = []
            notify = ''
            if 'album' in params.keys():
                files = self.mpd.find('artist',params['art'],'album',params['album'])
                notify = '%s - %s' % (params['art'],params['album'])
            else:
                files = self.mpd.find('artist',params['art'])
                notify = '%s' % (params['art'])
            if len(files) > 0:
                self.mpd.command_list_ok_begin()
                for f in files:
                    self.mpd.add(f['file'])
                self.mpd.command_list_end()
                util.notify(notify,__str__(30018))


    def list_tracks(self,artist,album):
        xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_TRACKNUM)
        for item in self.mpd.find('artist',artist,'album',album):
            info = util.get_info_labels_from_queued_item(item)
            title = '%02d %s' % (info['tracknumber'],item['title'])
            menu={
                    __str__(30030):{self.key:'queue_add','file':item['file']},
                    __str__(30031):{self.key:'queue_repl','file':item['file']}
            }
            util.add_song(title,{self.key:'play','id':'id'},infoLabels=info,menuItems=menu,replace=True)

    def list_albums(self,artist):
        for album in self.mpd.list('album','artist',artist):
            date = 0
            dates = self.mpd.list('date','album',album,'artist',artist)
            if len(dates) > 0:
                try:
                    date = int(dates[0])
                except:
                    pass
            title = '%s' % album
            if date > 0:
                title = '%s (%d)' % (album,date)
            info={'year':date,'artist':artist}
            menu={
                    __str__(30030):{self.key:'queue_add','art':artist,'album':album},
                    __str__(30031):{self.key:'queue_repl','art':artist,'album':album}
            }
            util.add_dir(title,{self.key:'album','name':album,'art':artist},infoLabels=info,menuItems=menu,replace=True)
        xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL, label2Mask="%X")
        xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_DATE)

    def list_artists(self):
        for artist in self.mpd.list('artist'):
            menu={
                    __str__(30030):{self.key:'queue_add','art':artist},
                    __str__(30031):{self.key:'queue_repl','art':artist}
            }
            util.add_dir(artist,{self.key:'artist','name':artist},infoLabels={},menuItems=menu,replace=True)
        xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL, label2Mask="%X")

class MPDFiles(object):
    def __init__(self,key,client):
        self.mpd = client
        self.key = key

    def run(self,params):
        print params
        action = params[self.key]
        if 'list' == action:
            self.list(params)
        elif 'queue_add' == action or 'queue_repl' == action:
            return self.add_to_queue(params)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def add_to_queue(self,params):
        print params
        if params[self.key] == 'queue_repl':
            # replacing queue
            self.mpd.stop()
            self.mpd.clear()
        self.mpd.add(params['path'])
        util.notify(params['path'],__str__(30018))

    def list(self,params):
        uri = ''
        if 'path' in params.keys():
            uri = params['path']
        for item in self.mpd.lsinfo(uri):
            print item
            if 'directory' in item:
                menu={
                    __str__(30030):{self.key:'queue_add','path':item['directory']},
                    __str__(30031):{self.key:'queue_repl','path':item['directory']}
                }
                title = os.path.basename(item['directory'])
                util.add_dir(title,{self.key:'list','path':item['directory']},infoLabels={},menuItems=menu,replace=True)
            elif 'file' in item:
                menu={
                    __str__(30030):{self.key:'queue_add','path':item['file']},
                    __str__(30031):{self.key:'queue_repl','path':item['file']}
                }
                title = os.path.basename(item['file'])
                util.add_song(title,{self.key:'list','path':item['file']},infoLabels={},menuItems=menu,replace=True)

        xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL, label2Mask="%X")



class MPDPlaylists(object):
    def __init__(self,key,client):
        self.mpd = client
        self.key = key

    def run(self,params):
        print params
        action = params[self.key]
        if 'list' == action:
            self.list()
        elif 'playlist' == action:
            self.playlist(params['name'])
        elif 'queue_add' == action or 'queue_repl' == action:
            return self.add_to_queue(params)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

    def add_to_queue(self,params):
        print params
        if params[self.key] == 'queue_repl':
            # replacing queue
            self.mpd.stop()
            self.mpd.clear()
        if 'name' in params.keys():
            self.mpd.load(params['name'])
            util.notify(params['name'],__str__(30018))
        elif 'file' in params.keys():
            self.mpd.add(params['file'])
            util.notify(params['file'],__str__(30018))

    def playlist(self,name):
        for item in self.mpd.listplaylistinfo(name):
            print item
            info = util.get_info_labels_from_queued_item(item)
            title = util.format_song(info)
            menu={
                    __str__(30030):{self.key:'queue_add','file':item['file']},
                    __str__(30031):{self.key:'queue_repl','file':item['file']}
            }
            util.add_song(title,{self.key:'play','id':'id'},infoLabels=info,menuItems=menu,replace=True)
        xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL, label2Mask="%X")
    
    def list(self):
        for item in self.mpd.listplaylists():
            menu={
                __str__(30030):{self.key:'queue_add','name':item['playlist']},
                __str__(30031):{self.key:'queue_repl','name':item['playlist']}
            }
            title = item['playlist']
            util.add_dir(title,{self.key:'playlist','name':item['playlist']},infoLabels={},menuItems=menu,replace=True)
        xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL, label2Mask="%X")

