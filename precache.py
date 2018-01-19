#!/usr/bin/python3

import os
import sys
import MySQLdb
import phpserialize
import requests
import imghdr
import argparse
import yaml

parser = argparse.ArgumentParser(description='Cache all images in the zenphoto gallery.')
parser.add_argument('-t', '--test', action='store_true',
                   help='only test what needs to be cached, don\'t actually do it')
parser.add_argument('-c', '--config', action='store_true',
                   help='only test what needs to be cached, don\'t actually do it')

args = parser.parse_args()


with open("/etc/zenphoto.yml", 'r') as ymlfile:
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
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    numrows = cur.execute("SELECT aux, data FROM " + table_prefix + "plugin_storage WHERE type='cacheManager' ORDER BY aux")
    current_theme = getCurrentTheme()
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
        if(themeName == current_theme or themeName == 'admin'):
            print(themeName + ': ' + postfix_string)
            postfixes.append(postfix_string)
    return postfixes

def getCachedFileName(original, postfix):
        cachedFile = os.path.splitext(original.replace(albums, cache, 1))[0] + postfix + '.jpg'
        return cachedFile

def getUri(filename):
        uri = filename.replace(zenphoto, domain)
        return uri

# Add photos to the list if no cache exists

# get cache sizes once
cache_sizes = getCacheSizes()
for root, subFolders, files in os.walk(albums):
    for file in files:
        print('scanning (',end="")
        albumfile = os.path.join(root, file)
        if (imghdr.what(albumfile) != None):
            for postfix in cache_sizes:
                if not os.path.exists(getCachedFileName(albumfile, postfix)):
                    print('\033[1;31;40m✘\033[0;37;40m',end="")
                    cachefiles.append(getCachedFileName(albumfile, postfix))
                else:
                    print('\033[1;32;40m✔\033[0;37;40m',end="")
        else:
            print('\033[1;33;40mSKIPPED\033[0;37;40m',end="")
        print(") " + file)
if(not args.t):
    for uncachedfile in cachefiles:
        #just get the image from zenphoto, that will cause the cached image to be generated
        print("Caching " + uncachedfile)
        requests.get(getUri(uncachedfile))
else:
    print('Skipping caching!')
