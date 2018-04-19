# zenphoto-precache

This python script will, when given correct paths and database information,
iterate across all images in your zenphoto gallery and create cached thumbnails
and other cached images for them, so it does not need to be done on the fly
when the gallery is accessed.

It only caches needed sizes for the current theme and the admin theme, but you can use `--themes` to specify additional themes you need to cache sizes for.

This may be put into `/etc/cron.daily/zenphoto-precache.py` or similar to run
daily.

## Installation
In order to be able to run this script, a few dependencies must be installed first.

To install using pip, `pip install phpserialize pyyaml mysql argparse requests`

Depending on your distribution, native packages may exist, but pip should work regardless.
