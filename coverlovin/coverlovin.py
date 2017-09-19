#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''recursively process subdirectories of given directory, downloading
appropriate cover images from Google Images if .mp3 files are found'''

'''author: James Stewart
https://launchpad.net/coverlovin'''

import os, sys
import urllib, urllib2
import simplejson
import logging
from mutagen.easymp4 import EasyMP4
from mutagen.easyid3 import EasyID3
from optparse import OptionParser

# logging
log = logging.getLogger('coverlovin')
log.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(message)s")
handler.setFormatter(formatter)
log.addHandler(handler)

# google images
defaultReferer = "https://launchpad.net/coverlovin"
googleImagesUrl = "https://ajax.googleapis.com/ajax/services/search/images"

def sanitise_for_url(inputString):
    '''sanitise a string such that it can be used in a url'''

    # return blank string if none provided
    if inputString == None:
        return ""
    # process inputString
    words = inputString.split(' ')
    outputString = ''
    for word in words:
        try:
            word = urllib.quote(word)
            outputString += word + '+'
        except Exception, err:
            log.error("Exception: " + str(err))
    # drop trailing '+'
    outputString = outputString[:-1]

    return outputString

def dl_cover(urlList, directory, fileName, overWrite=False):
    '''download cover image from url in list to given directory/fileName'''

    coverImg = os.path.join(directory, fileName)
    # move existing file if overWrite enabled
    if os.path.isfile(coverImg) and overWrite:
        log.info("%s exists and overwrite enabled - moving to %s.bak" % (coverImg, coverImg))
        os.rename(coverImg, (coverImg + '.bak'))
    # download cover image from urls in list
    for url in urlList:
        log.debug('opening url: ' + url)
        urlOk = True
        # open connection
        try:
            coverImgWeb = urllib2.urlopen(url, None, 10)
        except Exception, err:
            log.error('exception: ' + str(err))
            urlOk = False
        # download file
        if urlOk:
            log.info('downloading cover image\n from: %s\n to: %s' % (url, coverImg))
            coverImgLocal = open(os.path.join(directory, fileName), 'w')
            coverImgLocal.write(coverImgWeb.read())
            coverImgWeb.close()
            coverImgLocal.close()
            # cover successfully downloaded so return
            return True

    # no cover image downloaded
    return False

def get_img_urls(searchWords, fileType='jpg', fileSize='small', resultCount=8, referer=defaultReferer):
    '''return list of cover urls obtained by searching
    google images for searchWords'''

    imgUrls = []

    # sanitise searchwords
    searchWords = [sanitise_for_url(searchWord) for searchWord in searchWords]
    # construct url
    url = googleImagesUrl + '?v=1.0&q='
    # add searchwords
    for searchWord in searchWords:
        url += searchWord + '+'
    url = url[:-1]
    # add other parameters
    url += '&as_filetype=' + fileType
    url += '&imgsz=' + fileSize
    url += '&rsz=' + str(resultCount)
    request = urllib2.Request(url, None, {'Referer': referer})
    # open url
    try:
        log.debug('opening url: %s' % url)
        response = urllib2.urlopen(request, None, 10)
    except Exception, err:
        log.error('exception: ' + str(err))
        return imgUrls
    # load json response
    try:
        results = simplejson.load(response)
    except Exception, err:
        log.error('exception: ' + str(err))
        return imgUrls
    # add results to list
    if results:
        for result in results['responseData']['results']:
            imgUrls.append(result['url'])

    return imgUrls

def process_dir(thisDir, results=[], coverFiles=[]):
    '''Recursively process sub-directories of given directory,
    gathering artist/album info per-directory.

    Call initially with empty results. Results will be
    gradually populated by recursive calls. Provide coverFiles
    list to ignore directories where cover files already exist.'''

    dirs = []
    files = []

    # read directory contents
    if os.path.exists(thisDir):
        try:
            for item in os.listdir(thisDir):
                itemFullPath=os.path.join(thisDir, item)
                if os.path.isdir(itemFullPath):
                    dirs.append(itemFullPath)
                else:
                    files.append(item)
        except OSError, err:
            log.error(err)
            return results
    else:
        log.error('directory does not exist: %s' % (thisDir))
        return results
    # sort dirs and files to be processed in order
    dirs.sort()
    files.sort()
    # recurse into subdirs
    for dir in dirs:
        results = process_dir(dir, results=results, coverFiles=coverFiles)
    # continue processing this dir once subdirs have been processed
    log.debug("evaluating " + thisDir)
    # if any of the given cover files exist, no further work required
    for coverFile in coverFiles:
        if coverFile in files:
            log.debug("cover file %s exists - skipping" % coverFile)
            return results
    for file in files:
        mp3Audio = False
        mp4Audio = False
        fileFullPath = os.path.join(thisDir, file)
        fileName, fileExtension = os.path.splitext(file)
        # check file for id3 tag info
        try:
            if fileExtension == ".m4a":
                mp4Audio = EasyMP4(fileFullPath)
            if fileExtension == ".mp3":
                mp3Audio = EasyID3(fileFullPath)
        except Exception, err:
            log.error('exception: ' + str(err))
            continue
        # get values and sanitise nulls
        artist = None
        album = None
        if mp4Audio:
            artist = mp4Audio['artist'][0].encode('utf-8')
            album = mp4Audio['album'][0].encode('utf-8')
        if mp3Audio:
            artist = mp3Audio['artist'][0].encode('utf-8')
            album = mp3Audio['album'][0].encode('utf-8')
        if artist == None: artist = ''
        if album == None: album = ''
        # if either artist or album found, append to results and return
        if artist or album:
            log.info("album details found: %s/%s in %s" % (artist.decode('utf-8'), album.decode('utf-8'), file))
            results.append((thisDir, artist, album))
            return results
    # no artist or album info found, return results unchanged
    return results

def parse_args_opts():
    '''parse command line argument and options'''

    googImgOpts = ["small", "medium", "large"]
    fileTypeOpts = ["jpg", "png", "gif"]
    parameters = {}

    parser = OptionParser()
    parser.add_option("-s", "--size", dest="size", action="store", default="medium", help="file size: small, medium, or large (default: medium)")
    parser.add_option("-i", "--image", dest="image", action="store", default="jpg", help="image format, eg jpg, png, gif (default: jpg)")
    parser.add_option("-n", "--name", dest="name", action="store", default="cover.jpg", help="cover image file name (default: cover.jpg)")
    parser.add_option("-r", "--referer", dest="referer", action="store", default=defaultReferer, help="referer url (default: %s)" % defaultReferer)
    parser.add_option("-c", "--count", dest="count", action="store", default="8", type="int", help="image lookup count (default: 8))")
    parser.add_option("-o", "--overwrite", dest="overwrite", action="store_true", default=False, help="overwrite (default False)")
    parser.add_option("-d", "--debug", dest="debug", action="store_true", default=False, help="show debug (default False)")
    parser.set_usage("Usage: coverlovin.py <music_dir> [options]")
    (options, args) = parser.parse_args()

    # set musicDir or bail if invalid
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(2)
    elif os.path.isdir(sys.argv[1]) == False:
        log.error(sys.argv[1] + " is not a valid directory")
        parser.print_help()
        sys.exit(2)
    else:
        parameters['musicDir'] = sys.argv[1]
    # set fileSize or bail if invalid
    if options.size in googImgOpts:
        parameters['fileSize'] = options.size
    else:
        log.error(options.size + " is not a valid size")
        parser.print_help()
        sys.exit(2)
    # ensure fileName type matches fileType
    fileNameSplit = options.name.split('.')
    fileNamePrefix = fileNameSplit[0:-1]
    fileNameSuffix = fileNameSplit[-1]
    if fileNameSuffix != options.image:
        log.error('--name "%s" does not match --image "%s"' % (options.name, options.image))
        parser.print_help()
        sys.exit(2)
    # set other variables
    parameters['fileType'] = options.image
    parameters['fileName'] = options.name
    parameters['referer'] = options.referer
    parameters['resultCount'] = int(options.count)
    parameters['overWrite'] = options.overwrite
    parameters['debug'] = options.debug

    return parameters

def main():
    '''recursively download cover images for music files in a
    given directory and its sub-directories'''

    parameters = parse_args_opts()

    # allocate args/opts to vars, converting to utf-8
    musicDir = unicode(parameters['musicDir'], 'utf-8')
    fileType = unicode(parameters['fileType'], 'utf-8')
    fileName = unicode(parameters['fileName'], 'utf-8')
    fileSize = unicode(parameters['fileSize'], 'utf-8')
    referer = unicode(parameters['referer'], 'utf-8')
    resultCount = parameters['resultCount']
    overWrite = parameters['overWrite']
    debug = parameters['debug']
    # set loglevel to debug
    if debug:
        log.setLevel(logging.DEBUG)
    # only pass cover filename if overwrite disabled
    if overWrite:
        coverFiles = []
    else:
        coverFiles = [fileName]
    # gather list of directories with album/artist info
    musicDirs = process_dir(musicDir, coverFiles=coverFiles)
    # download covers
    for details in musicDirs:
        directory, artist, album = details
        urls = get_img_urls([artist,album], fileType=fileType, fileSize=fileSize, resultCount=resultCount)
        if len(urls) > 0:
            log.debug('gathered %i urls for %s/%s:' % (len(urls), artist, album))
            for url in urls:
                log.debug(' %s' % url)
            # download cover image
            dl_cover(urls, directory, fileName, overWrite=overWrite)
        else:
            log.info('no urls found for %s/%s' % (artist, album))

    return 0

if __name__ == "__main__":
    sys.exit(main())
