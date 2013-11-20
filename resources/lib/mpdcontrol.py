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
import xbmpc

try:
    __addon__ = xbmcaddon.Addon(id='plugin.audio.mpdc')
    _ = __addon__.getLocalizedString
except:
    def lang(id):
        return 'String ID %d' % id
    _ = lang

try:
    import StorageServer
except:
    print 'Using dummy storage server'
    import storageserverdummy as StorageServer

class MPDController():

    def __init__(self,host,port,password,settings):
        self.host = host
        self.port = port
        self.password = password
        self.settings = settings
        self.mpd = None

    def connect(self):
        client = xbmpc.MPDClient()
        print 'Connecting...'
        client.connect(self.host,int(self.port))
        if not self.password == '':
            client.password(self.password)
            print 'Password sent'
        print 'Connected to MPD server'
        self.mpd = client

    def disconnect(self):
        self.mpd.close()
        self.mpd.disconnect()
        self.mpd = None

    def modules(self):
        if self.mpd == None:
            raise Exception('Not connected, cannot initialize modules')
        return [(MPDQueue(self.mpd,self.settings),True),
                (MPDPlayerControl(self.mpd,self.settings),True),
                (MPDSearchRoot(self.mpd,self.settings),True),
                (MPDSearchArtist(self.mpd,self.settings),False),
                (MPDSearchAlbum(self.mpd,self.settings),False),
                (MPDSearchSong(self.mpd,self.settings),False),
                (MPDArtists(self.mpd,self.settings),True),
                (MPDFiles(self.mpd,self.settings),True),
                (MPDPlaylists(self.mpd,self.settings),True)]

    def run(self,params):
        print params
        modules = self.modules()
        if params == {}:
            result = []
            for m,visible in modules:
                if visible:
                    result.append(m.root())
            return result
        if params.has_key('m'):
            for m,visible in modules:
                if params['m'] == m.key:
                    return m.run(params)
            else:
                raise Exception('No module found to run')

class MPDBase(object):
    def __init__(self,key,name,client,settings,icon=''):
        self.mpd = client
        self.key = key
        self.name = name
        self.settings = settings
        self.icon = icon
        self.cache = StorageServer.StorageServer('script_mpdc_'+self.key, 24)

    def getSetting(self,name):
        if self.settings.has_key(name):
            return self.settings[name]
        return ''

    def module(self,clazz):
        return clazz(self.mpd,self.settings)

    def run(self,params):
        return []

    def item_dummy(self):
        return {'type':'dummy'}

    def item_play(self,path=''):
        return {'type':'play','path':path}

    def item_dir(self,title='',params={},icon='',menu=[],info={}):
        '''
        creates a directory item        
        '''
        return {'type':'dir','m':self.key,'title':title,'icon':icon,'params':params,'menu':menu,'info':info}

    def item_menu(self,params={}):
        params.update({'m':self.key})
        return params

    def item_audio(self,title='',params={},icon='',menu=[],info={},playable=False):
        return {'type':'audio','m':self.key,'title':title,'icon':icon,'params':params,'menu':menu,'info':info,'play':playable}
    
    def item_notify(self,title='',message='',icon=''):
        return {'type':'notify','title':title,'message':message,'icon':icon}

    def item_func(self,func=''):
        return {'type':'func','func':func}

    def item_refresh(self):
        return self.item_func(func='Container.Refresh')
    

    def item_sort(self,keys=[]):
        return {'type':'sort','keys':keys}

    def root(self):
        return self.item_dir(title=self.name,params={'root':''},icon=self.icon)

def controls(func):
    """
        Decorator to 'inject' control menuItems
    """
    def wrap(*arg):
        self = arg[0]
        res = func(*arg)
        return self.module(MPDPlayerControl).menu_items() + res
    return wrap


class MPDQueue(MPDBase):

    def __init__(self,client,settings):
        MPDBase.__init__(self,'queue',_(200),client,settings)

    def run(self,params):
        if params.has_key('play'):
            return self.play(params['play'])
        if params.has_key('qf'):
            return self.queue_file(params['path'],params['replace'].lower() == 'true')
        if params.has_key('qp'):
            return self.queue_playlist(params['name'],params['replace'].lower() == 'true')
        if params.has_key('qa'):
            album = None
            if params.has_key('album'):
                album = params['album']
            return self.queue_album(params['artist'],album,params['replace'].lower() == 'true')
        else:
            return self.list()

    def play(self,id):
        self.mpd.seekid(id,0)
        return [self.item_refresh()]

    @controls
    def menu_items(self):
        return []

    def list(self):
        playlist = self.mpd.playlistinfo()
        current = util.fix_keys(self.mpd.currentsong(),['id'])
        yield self.item_dummy()
        for item in playlist:
            info = util.get_info_labels_from_queued_item(item)
            title = util.format_song(info)
            if current['id'] == item['id']:
                title = '[B]* %s *[/B]' % title
            yield self.item_audio(title=title,params={'play':item['id']},info=info,menu=self.menu_items())

    def item_menu_queue_file(self,path,replace):
        return self.item_menu(params={'qf':'#','path':path,'replace':str(replace)})

    def item_menu_queue_artist(self,artist,replace):
        return self.item_menu(params={'qa':'#','artist':artist,'replace':str(replace)})
    
    def item_menu_queue_album(self,artist,album,replace):
        return self.item_menu(params={'qa':'#','artist':artist,'album':album,'replace':str(replace)})
    
    def item_menu_queue_playlist(self,name,replace):
        return self.item_menu(params={'qp':'#','name':name,'replace':str(replace)})
    
    def queue_playlist(self,name,replace=False):
        if replace:
            # replacing queue
            self.mpd.stop()
            self.mpd.clear()
        self.mpd.load(name)
        yield self.item_notify(title=_(30018),message=name)
        if self.settings['play_on_queued']:
            self.mpd.play()
            yield self.item_notify(title='Status',message=_(30006))
    
    def queue_file(self,path,replace=False):
        if replace:
            # replacing queue
            self.mpd.stop()
            self.mpd.clear()
        self.mpd.add(path)
        yield self.item_notify(title=_(30018),message=path)
        if self.settings['play_on_queued']:
            self.mpd.play()
            yield self.item_notify(title='Status',message=_(30006))

    def queue_album(self,artist,album=None,replace=False):
        if replace:
            # replacing queue
            self.mpd.stop()
            self.mpd.clear()
        files = []
        item_notify = ''
        if album:
            files = self.mpd.find('artist',artist,'album',album)
            item_notify = '%s - %s' % (artist, album)
        else:
            files = self.mpd.find('artist',artist)
            item_notify = '%s' % (artist)
        if len(files) > 0:
            self.mpd.command_list_ok_begin()
            for f in files:
                self.mpd.add(f['file'])
            self.mpd.command_list_end()
            yield self.item_notify(title=_(30018),message=item_notify)
            if self.settings['play_on_queued']:
                self.mpd.play()
                yield self.item_notify(title='Status',message=_(30006))

    
class MPDPlayerControl(MPDBase):
    
    def __init__(self,client,settings):
        MPDBase.__init__(self,'player',_(30016),client,settings)

    def run(self,params):
        if params.has_key('play_stream'):
            return self.play_stream()
        elif params.has_key('play'):
            self.mpd.play()
        elif params.has_key('stop'):
            self.mpd.stop()
        elif params.has_key('pause'):
            self.mpd.pause()
        elif params.has_key('next'):
            self.mpd.next()
        elif params.has_key('prev'):
            self.mpd.previous()
        else:
            return self.list()
        return [self.status_notify(self.mpd.status()),self.item_refresh()]

    def status_notify(self,status):
        item = self.item_notify(title='Status')
        if status['state'] == 'stop':
            item['message'] = _(30003)
        elif status['state'] == 'pause':
            item['message'] = _(30004)
        elif status['state'] == 'play':
            item['message'] = _(30006)
        return item
            

    def list(self):
        status = self.mpd.status()
        state = status['state']
        #yield self.status_notify(status)
        if status['state'] == 'pause' or status['state'] == 'stop':
            yield self.item_audio(title=_(30066),params={'play':'#'},icon='play.png')
        else:
            yield self.item_audio(title=_(30068),params={'pause':'#'},icon='pause.png')

        yield self.item_audio(title=_(30067),params={'stop':'#'},icon='stop.png')
        yield self.item_audio(title=_(30069),params={'prev':'#'},icon='prev.png')
        yield self.item_audio(title=_(30070),params={'next':'#'},icon='next.png')
        if not self.getSetting('stream_url') == '' and status['state'] == 'play':
            yield self.item_audio(title=_(30039),params={'play_stream':'#'},playable=True)

    def menu_items(self):
        return [
            (_(30066)+' MPD',self.item_menu(params={'play':'#'})),
            (_(30067)+' MPD',self.item_menu(params={'stop':'#'})),
        ]

    def play_stream(self):
        stream_url = self.getSetting('stream_url')
        if not stream_url.startswith('http://'):
            stream_url= 'http://'+stream_url
        return [self.item_play(path=stream_url)]

class MPDArtists(MPDBase):
    def __init__(self,client,settings):
        MPDBase.__init__(self,'artists',_(202),client,settings)

    def run(self,params):
        if params.has_key('album') and params.has_key('artist'):
            return self.list_tracks(params['artist'],params['album'])
        elif params.has_key('artist'):
            return self.list_albums(params['artist'])
        return self.list_artists()

    @controls
    def menu_items_artist(self,artist):
        q = self.module(MPDQueue)
        return [
            (_(30030),q.item_menu_queue_artist(artist,False)), #add to queue
            (_(30031),q.item_menu_queue_artist(artist,True))   #replace in queue
        ]

    @controls    
    def menu_items_album(self,artist,album):
        q = self.module(MPDQueue)
        return [
            (_(30030),q.item_menu_queue_album(artist,album,False)), #add to queue
            (_(30031),q.item_menu_queue_album(artist,album,True))   #replace in queue
        ]

    @controls
    def menu_items_file(self,path):
        q = self.module(MPDQueue)
        return [
            (_(30030),q.item_menu_queue_file(path,False)), #add to queue
            (_(30031),q.item_menu_queue_file(path,True))   #replace in queue
        ]

    def list_tracks(self,artist,album):
        yield self.item_dummy()
        yield self.item_sort(['track'])
        for item in self.mpd.find('artist',artist,'album',album):
            info = util.get_info_labels_from_queued_item(item)
            title = '%02d %s' % (info['tracknumber'],item['title'])
            yield self.item_track(title=title,path=item['file'],info=info)

    def list_albums(self,artist):
        yield self.item_dummy()
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
            yield self.item_album(title,artist,album,info)
        yield self.item_sort(['label','date'])

    def item_track(self,title='',path='',info={}):
        return self.item_audio(title=title,params={'path':path},menu=self.menu_items_file(path),info=info)

    def item_album(self,title='',artist='',album='',info={}):
            return self.item_dir(
                    title=title,
                    params={'album':album,'artist':artist},
                    menu=self.menu_items_album(artist,album)
            )

    def item_artist(self,artist):
        return self.item_dir(title=artist,params={'artist':artist},menu=self.menu_items_artist(artist))

    def list_artists(self):
        yield self.item_dummy()
        for artist in self.mpd.list('artist'):
            yield self.item_artist(artist)
        yield self.item_sort()

class MPDFiles(MPDBase):
    def __init__(self,client,settings):
        MPDBase.__init__(self,'files',_(201),client,settings)

    def run(self,params):
        return self.list(params)

    @controls
    def menu_items(self,path):
        q = self.module(MPDQueue)
        return [
            (_(30030),q.item_menu_queue_file(path,False)), #add to queue
            (_(30031),q.item_menu_queue_file(path,True))   #replace in queue
        ]

    def list(self,params):
        yield self.item_dummy()
        uri = ''
        if 'path' in params.keys():
            uri = params['path']
        for item in self.mpd.lsinfo(uri):
            if 'directory' in item:
                title = os.path.basename(item['directory'])
                yield self.item_dir(title=title,params={'path':item['directory']},menu=self.menu_items(item['directory']))
            elif 'file' in item:
                title = os.path.basename(item['file'])
                yield self.item_audio(title=title,params={'path':item['file']},menu=self.menu_items(item['file']))


class MPDPlaylists(MPDBase):
    def __init__(self,client,settings):
        MPDBase.__init__(self,'playlists',_(203),client,settings)

    def run(self,params):
        print params
        if params.has_key('detail'):
            return self.playlist(params['detail'])
        return self.list()
    
    def menu_items_file(self,path):
        q = self.module(MPDQueue)
        return [
            (_(30030),q.item_menu_queue_file(path,False)), #add to queue
            (_(30031),q.item_menu_queue_file(path,True))   #replace in queue
        ]
        
    @controls
    def menu_items_playlist(self,name):
        q = self.module(MPDQueue)
        return [
            (_(30030),q.item_menu_queue_playlist(name,False)), #add to queue
            (_(30031),q.item_menu_queue_playlist(name,True))   #replace in queue
        ]


    def playlist(self,name):
        for item in self.mpd.listplaylistinfo(name):
            info = util.get_info_labels_from_queued_item(item)
            title = util.format_song(info)
            yield self.item_audio(title=title,params={'path':item['file']},menu=self.menu_items_file(item['file']))
    
    def list(self):
        yield self.item_dummy()
        for item in self.mpd.listplaylists():
            yield self.item_dir(
                    title=item['playlist'],
                    params={'detail':item['playlist']},
                    menu=self.menu_items_playlist(item['playlist'])

                    )


class MPDSearchRoot(MPDBase):
    def __init__(self,client,settings):
        MPDBase.__init__(self,'search-root',_(209),client,settings,'search.png')

    def run(self,params):
        yield self.module(MPDSearchArtist).root()
        yield self.module(MPDSearchAlbum).root()
        yield self.module(MPDSearchSong).root()
    

class MPDSearch(MPDBase):
    def __init__(self,key,title,client,settings,category='artist'):
        MPDBase.__init__(self,key,title,client,settings,'search.png')
        self.category = category

    def item_search(self,keyword=''):
        return {'type':'search','m':self.key,'for':keyword,'func':self.do_search}
    
    def _get_history(self):
        data = self.cache.get('search')
        if data == None or data == '':
            data = []
        else:
            data = eval(data)
        return data

    def do_search(self,keyword):
        print 'searching '+keyword
        yield self.item_dummy()
        data = self._get_history()
        if keyword in data:
            data.remove(keyword)
        data.insert(0,keyword)
        self.cache.set('search',repr(data))
        mod = self.module(MPDArtists)
        yield self.item_sort()
        if self.category == 'artist':
            artists = set([])
            for i in self.mpd.search('artist',keyword):
                artists.add(i['artist'])
            for i in artists:
                yield mod.item_artist(i)
        if self.category == 'album':
            albums = {}
            for i in self.mpd.search('album',keyword):
                albums['[%s] %s' % (i['artist'],i['album'])] = {'artist':i['artist'],'album':i['album']}
            for k,v in albums.items():
                yield mod.item_album(title=k,artist=v['artist'],album=v['album'])
        if self.category == 'song':
            for i in self.mpd.search('title',keyword):
                t = '%s (%s by %s)' % (i['title'],i['album'],i['artist'])
                yield mod.item_track(title=t,path=i['file'])
            

    def run(self,params):
        if params.has_key('do-search'):
            yield self.item_search(keyword=params['do-search'])
        yield self.item_dir(title=_(30065),params={'do-search':'#'},icon=self.icon)
        for x in self._get_history(): yield self.item_dir(title=x,params={'do-search':x})


class MPDSearchAlbum(MPDSearch):
    def __init__(self,client,settings):
        MPDSearch.__init__(self,'search-alb',_(207),client,settings,'album')

class MPDSearchArtist(MPDSearch):
    def __init__(self,client,settings):
        MPDSearch.__init__(self,'search-art',_(206),client,settings,'artist')

class MPDSearchSong(MPDSearch):
    def __init__(self,client,settings):
        MPDSearch.__init__(self,'search-song',_(208),client,settings,'song')
