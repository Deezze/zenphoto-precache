#!/usr/bin/python
# -*- coding: utf-8 -*-

#python 2/3 compatibility
from __future__ import print_function

import os
import sys
import MySQLdb
import phpserialize
import requests
import imghdr
import argparse
import yaml

parser = argparse.ArgumentParser(description='Utility to cache all images in the zenphoto gallery.')
parser.add_argument('-p', '--pretend', action='store_true',
                   help='only print what needs to be cached')
parser.add_argument('-c', '--config', type=str, default='/etc/zenphoto.yml',
                   help='Use a specific config file')
parser.add_argument('-t', '--themes', nargs='+', default=[], type=str,
                    help='Specify additional themes to grab cache sizes from'),
parser.add_argument('-v', '--verbose', action='store_true',
                    help='Show more information about what is being done'),

args = parser.parse_args()
with open(args.config, 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

db = MySQLdb.connect(host=cfg['mysql_host'],
                     user=cfg['mysql_user'],
                     passwd=cfg['mysql_password'],
                     db=cfg['database_name'])
table_prefix = cfg['table_prefix'] #make sure to include an underscore if using this
domain = cfg['zenphoto_url']
zenphoto = cfg['install_folder']
cache = zenphoto + 'cache/'
albums = zenphoto + 'albums/'
cachefiles = []
result = []

def getCurrentTheme():
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    options = cur.execute("SELECT value FROM " + table_prefix + "options WHERE name='gallery_data'")
    data = phpserialize.loads(cur.fetchone()['value'].encode(), decode_strings=True)
    return data['current_theme']

def getCacheSizes():
    postfixes = []
    themes = args.themes
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    numrows = cur.execute("SELECT aux, data FROM " + table_prefix + "plugin_storage WHERE type='cacheManager' ORDER BY aux")
    themes.append(getCurrentTheme())
    themes.append('admin')
    for x in range(0, numrows):
        row = cur.fetchone()
        themeName = row['aux']
        data = phpserialize.loads(row['data'].encode(), decode_strings=True)
        postfix_string = (('_' + str(data['image_size']) if data['image_size'] else '') +
            ('_w' + str(data['image_width']) if data['image_width'] else '') +
            ('_h' + str(data['image_height']) if data['image_height'] else '') +
            ('_cw' + str(data['crop_width']) if data['crop_width'] else '') +
            ('_ch' + str(data['crop_height']) if data['crop_height'] else '') +
            ('_cx' + str(data['crop_x']) if data['crop_x'] else '') +
            ('_cy' + str(data['crop_y']) if data['crop_y'] else '') +
            ('_thumb' if data['thumb'] else '') +
            ('_' + str(data['wmk']) if data['wmk'] else '') +
            ('_' + str(data['gray']) if data['gray'] else ''))
        if(themeName in themes):
            postfixes.append(postfix_string)
    print('will cache ' + str(len(postfixes)) + ' sizes for \'' + '\', \''.join(themes) + '\'...')
    return postfixes

def getCachedFileName(original, postfix):
        cachedFile = os.path.splitext(original.replace(albums, cache, 1))[0] + postfix + '.jpg'
        return cachedFile

def getUri(filename):
        uri = filename.replace(zenphoto, domain)
        return uri

# Add photos to the list if no cache exists

image_files = 0
cache_sizes = getCacheSizes()
already_cached = 0
non_image_files=0
print('Scanning for image files in \'' + albums + '\'...')
for root, subFolders, files in os.walk(albums):
    for file in files:
        if args.verbose: print('Scanning (',end="")
        albumfile = os.path.join(root, file)
        if (imghdr.what(albumfile) != None):
            image_files+=1
            for postfix in cache_sizes:
                cachefile = getCachedFileName(albumfile, postfix)
                if not os.path.exists(cachefile):
                    if args.verbose: print('\033[1;31;40m✘\033[0;37;40m',end="")
                    cachefiles.append(cachefile)
                else:
                    albumfiletime = os.path.getmtime(albumfile)
                    cachefiletime = os.path.getmtime(cachefile)
                    if (cachefiletime < albumfiletime):
                        #remove the cachefile if it's older than the albumfile
                        if(not args.pretend): os.remove(cachefile)
                        if args.verbose: print('\033[1;33;40m⟲\033[0;37;40m',end="")
                        cachefiles.append(cachefile)
                    else:
                        already_cached+=1
                        if args.verbose: print('\033[1;32;40m✔\033[0;37;40m',end="")
        else:
            if args.verbose: print('\033[1;33;40mSKIPPED\033[0;37;40m',end="")
            non_image_files+=1
        if args.verbose: print(") " + file)

print('Will create ' + str(len(cachefiles)) + ' new caches (' + str(already_cached) + ' already cached) for ' + str(image_files) + ' images (' + str(non_image_files) + ' non-image files skipped)...')
if(not args.pretend):
    for uncachedfile in cachefiles:
        #just get the image from zenphoto, that will cause the cached image to be generated
        print("Caching " + uncachedfile)
        requests.get(getUri(uncachedfile))
else:
    print('Skipping caching!')
