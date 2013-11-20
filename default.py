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
import urllib2,re,sys,time,os,traceback
import xbmcaddon,xbmc,xbmcgui,xbmcplugin
__addon__ = xbmcaddon.Addon(id='plugin.audio.mpdc')
__str__ = __addon__.getLocalizedString
__sett__ = __addon__.getSetting

sys.path.append( os.path.join ( __addon__.getAddonInfo('path'), 'resources','lib') )

import mpdutil as util

from mpdcontrol import MPDController

def get_params(url=None):
    if url == None:
        url = sys.argv[2]
    param={}
    paramstring=url
    if len(paramstring)>=2:
        params=url
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    for p in param.keys():
        param[p] = param[p].decode('hex')
    return param

def notify(title=__addon__.getAddonInfo('name'),message=''):
    try:
        icon =  os.path.join(__addon__.getAddonInfo('path'),'icon.png')
        xbmc.executebuiltin("XBMC.Notification(%s,%s,5000,%s)" % (title.encode('UTF-8','ignore'),message.encode('UTF-8','ignore'),icon))
    except:
        print 'Unable to display notify message'
        traceback.print_exc()

def icon(icon):
    if len(icon) > 0:
        return os.path.join(__addon__.getAddonInfo('path'),'resources','icons',icon)
    return ''

def sort_methods(keys):
    if len(keys) == 0:
        return xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL,label2Mask="%X")
    else:
        for key in keys:
            if key == 'label':
                xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL,label2Mask="%X")
            elif key == 'date':
                xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_DATE)
            elif key == 'track':
                xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_TRACKNUM)
            else:
                print 'Unsupported sort method %s' % key



def get_stream():
    stream_url = __sett__('stream_url')
    if not stream_url.startswith('http://'):
        stream_url= 'http://'+stream_url
    return stream_url

def auto_play_stream(client):
    autoplay = __sett__('play_stream') == 'true'
    if autoplay and client.status()['state'] == 'play':
        stream_url = get_stream()
        player = xbmc.Player(xbmc.PLAYER_CORE_MPLAYER)
        if player.isPlayingVideo():
            return
        if player.isPlayingAudio():
            if not player.getPlayingFile() == stream_url:
                xbmc.executebuiltin('PlayMedia(%s)' % stream_url)
        else:
            xbmc.executebuiltin('PlayMedia(%s)' % stream_url)

def render(data):
    if data == None:
        raise Exception('Addon error, no data returned')
    listed = 0
    for item in data:
        if item['type'] == 'play':
            print 'Playing MPD Stream '+item['path']
            li = xbmcgui.ListItem(path=item['path'],iconImage='DefaulAudio.png')
            return xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, li)
        if item['type'] == 'dummy':
            listed+=1
        if item['type'] == 'dir':
            listed+=1
            params = item['params']
            params.update({'m':item['m']})
            util.add_dir(item['title'],params,icon(item['icon']),menuItems=item['menu'],replace=True) 
        if item['type'] == 'audio':
            listed+=1
            params = item['params']
            params.update({'m':item['m']})
            util.add_song(item['title'],params,icon(item['icon']),menuItems=item['menu'],playable=str(item['play']).lower(),replace=True) 
        if item['type'] == 'func':
            print 'Executing %s' % item['func']
            xbmc.executebuiltin(item['func'])
        if item['type'] == 'sort':
            sort_methods(item['keys'])
        if item['type'] == 'notify':
            notify(item['title'],item['message'])
        if item['type'] == 'search':
            what = item['for']
            if what == '#':
                kb = xbmc.Keyboard('',__str__(30071),False)
                kb.doModal()
                if kb.isConfirmed():
                    what = kb.getText()
            if not (what == '' or what == '#'):
                render(item['func'](what))
            return

    if listed > 0:
        xbmcplugin.endOfDirectory(int(sys.argv[1]))

params=get_params()
ctrl = MPDController(
        __sett__('mpd_host'),
        __sett__('mpd_port'),
        __sett__('mpd_pass'),
        {'stream_url':__sett__('stream_url'),'play_on_queued':__sett__('play_on_queued') == 'true'})
ctrl.connect()
data = ctrl.run(params)
render(data)
auto_play_stream(ctrl.mpd)
ctrl.disconnect()
