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
import xbmcplugin,xbmcaddon,xbmcgui,sys,traceback,os,xbmc

__addon__ = xbmcaddon.Addon(id='plugin.audio.mpdc')
__str__ = __addon__.getLocalizedString

def add_dir(name,id,logo):
    u=sys.argv[0]+"?"+id
    liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png",thumbnailImage=logo)
    liz.setInfo( type="Audio", infoLabels={ "Title": name } )
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

def add_dir(name,params,logo='',infoLabels={},menuItems={},replace=False):
	if not 'title' in infoLabels:
		infoLabels['title'] = name
	if logo == None:
		logo = ''
	liz=xbmcgui.ListItem(name, iconImage='DefaultFolder.png',thumbnailImage=logo)
        try:
		liz.setInfo( type='Video', infoLabels=infoLabels )
	except:
		traceback.print_exc()
	items = []
	for mi in menuItems.keys():
		action = menuItems[mi]
		if not type(action) == type({}):
			items.append((mi,action))
		else:
			items.append((mi,'RunPlugin(%s)'%_create_plugin_url(action)))
	if len(items) > 0:
		liz.addContextMenuItems(items,replaceItems=replace)
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=_create_plugin_url(params),listitem=liz,isFolder=True)

def get_info_labels_from_queued_item(item):
    print item
    item = fix_keys(item,['title','genre','artist','album','time','track'])
    labels = {}
    labels['title'] = item['title']
    labels['genre'] = item['genre']
    labels['artist'] = item['artist']
    labels['album'] = item['album']
    labels['duration'] = int(item['time'])
    try:
        labels['year'] = int(item['date'])
    except:
        pass
    try:
        labels['tracknumber'] = 0
        labels['tracknumber'] = int(item['track'])
    except:
        pass
    return labels

def add_song(name,params={},logo='',infoLabels={},menuItems={},playable='false',replace=False):
	if not 'Title' in infoLabels:
		infoLabels['Title'] = name
	url = _create_plugin_url(params)
	li=xbmcgui.ListItem(name,path=url,iconImage='DefaultAudio.png',thumbnailImage=logo)
        li.setInfo( type='Audio', infoLabels=infoLabels )
	li.setProperty('IsPlayable',playable)
	items = []
	for mi in menuItems.keys():
		action = menuItems[mi]
		if not type(action) == type({}):
			items.append((mi,action))
		else:
			items.append((mi,'RunPlugin(%s)'%_create_plugin_url(action)))
	if len(items) > 0:
		li.addContextMenuItems(items,replaceItems=replace)
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=li,isFolder=False)


def _create_plugin_url(params,plugin=sys.argv[0]):
	url=[]
	for key in params.keys():
		value = params[key]
		#value = params[key].encode('utf-8')
		url.append(key+'='+value.encode('hex',)+'&')
	return plugin+'?'+''.join(url)

def notify(message,title=__addon__.getAddonInfo('name')):
    try:
        icon =  os.path.join(__addon__.getAddonInfo('path'),'icon.png')
        xbmc.executebuiltin("XBMC.Notification(%s,%s,5000,%s)" % (title.encode('UTF-8','ignore'),message.encode('UTF-8','ignore'),icon))
    except:
        print 'Unable to display notify message'
        traceback.print_exc()

def notify_status(mpd):
    status = mpd.status()
    if status['state'] == 'play' or status['state'] == 'pause':
        current = mpd.currentsong()
        song = format_song(current)
        if status['state'] == 'play':
            notify(song,__str__(30006))
        else:
            notify(song,__str__(30004))
    if status['state'] == 'stop':
        notify('',__str__(30003))

def format_song(item):
    try:
        if item['title'] == '' and item['artist'] == '' and item['album'] == '':
            ret = current['file']
        else:
            ret = item['artist'] + ' - ' + item['album'] + ' - ' + item['title']
        return ret.decode('utf-8') 
    except:
        return ''


def fix_keys(obj,fields):
    for field in fields:
        if not field in obj:
            obj[field]=''
    return obj
