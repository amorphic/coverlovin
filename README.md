CoverLovin
==========

Coverlovin is a Python module for collecting artist and album details from a directory hierarchy and downloading cover art from Google Images. It can be used both as a module and as a standalone application.

Standalone Usage
==========

Usage: coverlovin.py <music_dir> [options]

Options:
  -h, --help            show this help message and exit
  -s SIZE, --size=SIZE  file size: small, medium, or large (default: medium)
  -i IMAGE, --image=IMAGE
                        image format, eg jpg, png, gif (default: jpg)
  -n NAME, --name=NAME  cover image file name (default: cover.jpg)
  -r REFERER, --referer=REFERER
                        referer url (default:
                        https://launchpad.net/coverlovin)
  -c COUNT, --count=COUNT
                        image lookup count (default: 8))
  -o, --overwrite       overwrite (default False)
  -d, --debug           show debug (default False)

Requirements
==========

id3reader
