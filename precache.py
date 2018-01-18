#!/usr/bin/python3

import os
import sys
import MySQLdb
import phpserialize
import requests

db = MySQLdb.connect(host="localhost",
                     user="zenphoto",
                     passwd="password",
                     db="zenphoto")
table_prefix = ''
domain = 'https://zenphoto.example.com/zenphoto/'
cachefiles = []
result = []
zenphoto = '/var/www/html/zenphoto/'
cache = zenphoto + 'cache/'
albums = zenphoto + 'albums/'

def getCacheSizes():
    postfixes = []
    cur = db.cursor(MySQLdb.cursors.DictCursor)
    numrows = cur.execute("SELECT * FROM " + table_prefix + "plugin_storage WHERE type='cacheManager' ORDER BY aux")
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
        postfixes.append(postfix_string)
    return postfixes

def getCachedFileName(original, postfix):
        cachedFile = original.replace(albums, cache, 1).replace('.jpg', '', 1).replace('.JPG', '', 1) + postfix + '.jpg'
        return cachedFile

def getUri(filename):
        uri = filename.replace(zenphoto, domain)
        return uri

# Add photos to the list if no cache exists
for root, subFolders, files in os.walk(albums):
    for file in files:
        print('scanning (',end="")
        albumfile = os.path.join(root, file)
        if (albumfile.find('jpg')>=0 or albumfile.find('JPG')>=0):
            for postfix in getCacheSizes():
                if not os.path.exists(getCachedFileName(albumfile, postfix)):
                    print('\033[1;31;40m✘\033[0;37;40m',end="")
                    cachefiles.append(getCachedFileName(albumfile, postfix))
                else:
                    print('\033[1;32;40m✔\033[0;37;40m',end="")
        else:
            print('\033[1;33;40mSKIPPED\033[0;37;40m',end="")
        print(") " + file)

for uncachedfile in cachefiles:
    #just get the image from zenphoto, that will cause the cached image to be generated
    print("caching " + uncachedfile)
    requests.get(getUri(uncachedfile))
