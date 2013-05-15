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

import xbmpc
import mpdutil as util

import mpdcontrol as mpd

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

def connect():
    client = xbmpc.MPDClient()
    print 'Connecting...'
    client.connect(__sett__('mpd_host'),int(__sett__('mpd_port')))
    mpd_pass = __sett__('mpd_pass')
    if not mpd_pass == '':
        client.password(mpd_pass)
        print 'Password sent'
    print 'Connected to MPD server'
    return client

def root():
    util.add_dir(__str__(30016),{'ctrl':'list'},'')
    util.add_dir(__str__(200),{'queue':'list'},'')
    util.add_dir(__str__(201),{'files':'list'},'')
    util.add_dir(__str__(202),{'artists':'list'},'')
    util.add_dir(__str__(203),{'pls':'list'},'')
#    util.add_dir(__str__(112),{'settings':'list'},'')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def notify_status(client):
    if notify:
        util.notify_status(client)

notify = __sett__('notify') == 'true'

params=get_params()
print params
client = connect()
    
try:
    auto_play_stream(client)
    if params=={}:
        root()
        notify_status(client)
    if 'queue' in params.keys():
        mpd.MPDQueue('queue',client).run(params)
    if 'ctrl' in params.keys():
        mpd.MPDControl('ctrl',client).run(params)
    if 'artists' in params.keys():
        mpd.MPDArtists('artists',client).run(params)
    if 'files' in params.keys():
        mpd.MPDFiles('files',client).run(params)
    if 'pls' in params.keys():
        mpd.MPDPlaylists('pls',client).run(params)
except:
    traceback.print_exc()
print 'Disconnecting'
client.close()
client.disconnect()
