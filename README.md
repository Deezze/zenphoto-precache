# zenphoto-precache

This python script will, when given correct paths and database information, 
iterate across all images in your zenphoto gallery and create cached thumbnails
and other cached images for them, so it does not need to be done on the fly
when the gallery is accessed.

This may be put into `/etc/cron.daily/zenphoto-precache.py` or similar to run
daily.
