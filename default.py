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
#do http request
def request(url):
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    data = response.read()
    response.close()
    return data

def replace(obj,what=None,replacement=''):
    if obj == what:
        return replacement
    return obj

def add_stream(name,url,bitrate,logo):
    bit = 0
    try:
        bit = int(bitrate)
    except:
        pass
    name = replace(name,None,'No name').replace('&amp;','&')
    logo = replace(logo)
    url=sys.argv[0]+"?play="+url
    li=xbmcgui.ListItem(name,path = url,iconImage="DefaultAudio.png",thumbnailImage=logo)
    li.setInfo( type="Music", infoLabels={ "Title": name,"Size":bit } )
    li.setProperty("IsPlayable","true")
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=li,isFolder=False)

# retrieve target stream if url is asx or m3u
def parse_playlist(url):
    if url.endswith('m3u'):
        return request(url).strip()
    if not url.endswith('asx'):
        return url
    data = request(url)
    refs = re.compile('.*<Ref href = \"([^\"]+).*').findall(data,re.IGNORECASE|re.DOTALL|re.MULTILINE)
    urls = []
    for ref in refs:
        stream = parse_playlist(ref)
        urls.append(stream.replace(' ','%20'))
    if urls == []:
        print 'Unable to parse '+url
        print data
        return ''
    return urls[-1]

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

def download_stationfile(dest):
    print 'Saving station file'
    data = request('http://abradio.cz/external/rss/radia.xml')
    f = open(dest,'w')
    f.write(unicode(data,'UTF-8').encode('UTF-8'))
    f.close()

def get_data():
    local = xbmc.translatePath(__addon__.getAddonInfo('profile'))
    if not os.path.exists(local):
        os.makedirs(local)
    local = os.path.join(local,'stations.xml')
    if os.path.exists(local):
        # update local station file when it becomes 1day old
        if (time.time() - os.path.getctime(local)) > (3600*24):
            download_stationfile(local)
    else:
        download_stationfile(local)
    return ET.parse(local)

def list_categories():
    tree = get_data()
    categories = {}
    for category in tree.findall('ABRADIOITEM/CATEGORY'):
        id = category.get('ID')
        categories[category.get('ID')]=category.text
    for id in categories.keys():
        add_dir(categories[id],'category='+id,'')
        add_dir(__language__(30000),'category=-1','')
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def list_category(id):
    tree = get_data()
    for station in tree.findall('ABRADIOITEM'):
        category = station.find('CATEGORY')
        if int(id) < 0 or id == category.get('ID'):
            add_dir(station.find('RADIO').text,'station='+station.find('ID').text,station.find('LOGO').text)
    xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL, label2Mask="%X")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

def resolve_station(id):
    tree = get_data()
    for station in tree.findall('ABRADIOITEM'):
        if station.find('ID').text == id:
            name = station.find('RADIO').text
            logo = station.find('LOGO').text
            for stream in station.findall('STREAMS/*'):
                add_stream(name,stream.text,stream.get('name'),logo)
                xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_LABEL, label2Mask="%X")
                xbmcplugin.addSortMethod( handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_BITRATE, label2Mask="%X")
            return xbmcplugin.endOfDirectory(int(sys.argv[1]))

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
