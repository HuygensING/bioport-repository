##########################################################################
# Copyright (C) 2009 - 2014 Huygens ING & Gerbrandy S.R.L.
#
# This file is part of bioport.
#
# bioport is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/gpl-3.0.html>.
##########################################################################

from __future__ import with_statement

import os
import urllib2
import httplib
import traceback
import sys
import logging
from hashlib import md5
import simplejson
from gerbrandyutils import normalize_url

try:
    from PIL import Image
except ImportError:
    import Image
# The following should avoid the "AccessInit: hash collision: 3 for both 1 and 1" error
# see http://jaredforsyth.com/blog/2010/apr/28/accessinit-hash-collision-3-both-1-and-1/
sys.modules['PIL.Image'] = Image

MEDIUM_THUMB_SIZE = (200, 200)
SMALL_THUMB_SIZE = (100, 100)
HOME_THUMB_SIZE = (300, 300)


class CantDownloadImage(Exception):
    """Raised by download() when it can't download the image from an external url"""


def logexception():
    msg = traceback.format_exc()
    print >> sys.stderr
    logging.error(msg)


class Illustration:
    """XXX - needs docstring"""

    def __init__(self, url,
           images_cache_local,
           images_cache_url,
           prefix=u'',
           caption=None,
           link_url=None):
        """
        arguments:
         - url  : the original url of the image
         - images_cache_local : path to a place on the filesystem where the image will be downloaded to.
         - images_cache_url : URL at which the image will be accessabiel once
           downloaded
         - link_url: an optional url to link to
         - prefix : will be prefixed to the local cached filename
        """
        self._url = url
        self._images_cache_local = images_cache_local and unicode(images_cache_local) or u''
        self._thumbnails_directory = os.path.join(self._images_cache_local, 'thumbnails')
        if not os.path.isdir(self._thumbnails_directory):
            try:
                os.mkdir(self._thumbnails_directory)
            except OSError:
                if not os.path.exists(self._images_cache_local):
                    msg = 'The path at {self._images_cache_local} does not exist.'.format(self=self)
                    msg += 'Check the setting for IMAGES_CACHE_LOCAL on the page /admin/edit '
                    raise OSError(msg)
                else:
                    raise
        self._images_cache_url = images_cache_url or u''
        self._prefix = prefix
        self._link_url = link_url
        self._caption = caption
        self._id = self._create_id()

    # --- public API used by the view
    @property
    def link_url(self):
        """The url of the site the biography points to"""
        return self._link_url

    @property
    def caption(self):
        return self._caption

    @property
    def json_stripped_caption(self):
        return simplejson.dumps(self.caption)

    @property
    def source_url(self):
        """the original url of the image (typically on an external sever)"""
        return self._url

    @property
    def image_url(self):  # XXX - l'url dell'immagine originale: da rinominare !!!
        """public url of the local copy of the image"""
        return os.path.join(self._images_cache_url, self.id)

    @property
    def image_medium_url(self):
        """The url of the medium size thumbnail"""
        width, height = MEDIUM_THUMB_SIZE
        return os.path.join(self._images_cache_url,
                            'thumbnails',
                            '%ix%i_%s' % (width, height, self.id))

    @property
    def image_small_url(self):
        """The url of the small size thumbnail"""
        width, height = SMALL_THUMB_SIZE
        return os.path.join(self._images_cache_url,
                            'thumbnails',
                            '%ix%i_%s' % (width, height, self.id))

    @property
    def image_home_url(self):
        """The url of the thumbnails shown in the home page"""
        width, height = HOME_THUMB_SIZE
        return os.path.join(self._images_cache_url,
                            'thumbnails',
                            '%ix%i_%s' % (width, height, self.id))

    # --- public API used *internally* (not by the view)
    @property
    def id(self):
        return self._id

    @property
    def cached_local(self):
        """path on the local file system to a copy of the image"""
        # in the test environment (on jenkins, but not locally) we get an enocding error here
        # when this is given as input to os.stat
        # (the locale settings there are slighly different, IT instead of en_US, but still UTF8)
        # return unicode(os.path.join(self._images_cache_local,  self.id))
        # and so we try to return an encoded string instead
        return os.path.join(self._images_cache_local, self.id).encode('utf8')

    @property
    def images_directory(self):
        """The physical path on disk where the images are held/saved"""
        return self._images_cache_local

    @property
    def thumbnails_directory(self):
        """The physical path on disk where the thumbnails are held/saved"""
        return self._thumbnails_directory

    @property
    def cached_url(self):
        """Public url of the local copy of the image"""
        return os.path.join(self._images_cache_url, self.id)

    def has_image(self):
        """return True if we a local copy of this image exists"""
        return os.path.isfile(self.cached_local)

    # --- actions
    def download(self, overwrite=True):
        """Download the original image with original dimensions and saves it on
        disk.

        Also, create two resized images which will then by used in the view,
        a medium and a smaller one, which will be saved im /thumbnails directory
        """
        if not overwrite and os.path.exists(self.cached_local):
            logging.info('image already exists at %s - no image downloaded' % self.cached_local)
        else:
            url = normalize_url(self.source_url)
            logging.info('Downloading image from %s to %s' % (repr(url), repr(self.cached_local)))
            try:
                http = urllib2.urlopen(url)
            except (urllib2.HTTPError, OSError, UnicodeEncodeError, httplib.BadStatusLine, urllib2.URLError), err:
                if os.path.isfile(self.cached_local):
                    os.remove(self.cached_local)
                raise CantDownloadImage(str(err))

            # write main image file on disk
            try:
                with open(self.cached_local, 'w') as f:
                    f.write(http.read())
                http.close()
            except:
                if os.path.isfile(self.cached_local):
                    os.remove(self.cached_local)
                raise

        # write two smaller thumbs on disk
        try:
            self._create_thumbnail(*MEDIUM_THUMB_SIZE)
            self._create_thumbnail(*SMALL_THUMB_SIZE)
            self._create_thumbnail(*HOME_THUMB_SIZE)
        except IOError, err:
            os.remove(self.cached_local)  # why??
            raise CantDownloadImage(str(err))
        except:
            logexception()
            os.remove(self.cached_local)
            raise CantDownloadImage(str(err))

    def _create_thumbnail(self, width, height):
        """
        Create a thumbnail of the image and store a local copy
        width and height are sizes in pixels - the image should fit within
        the rectangle defined by these sizes.
        inspired from Products.Archetypes.Field
        """
        assert isinstance(width, int)
        assert isinstance(height, int)
        if not os.path.isfile(self.cached_local):
            raise ValueError("the original image does not exist (it was supposed to be found here: %s)"
                             % self.cached_local)

        basename = os.path.basename(self.cached_local)
        basename = "%sx%s_%s" % (width, height, basename)
        filename = os.path.join(self.thumbnails_directory, basename)
        if os.path.exists(filename):
            logging.info('thumbnail already exists at %s - none created' % filename)
            return

        # PIL stuff
        pilfilter = 0  # NEAREST
        if Image.VERSION >= "1.1.3":  # @UndefinedVariable
            pilfilter = 1  # ANTIALIAS

        image = Image.open(self.cached_local)  # @UndefinedVariable
        image = image.convert('RGB')
        image.thumbnail((width, height), pilfilter)

        # write on disk
        image.save(filename, "JPEG", quality=88)
        return filename

    def _create_id(self):
        # XXX - IMPORTANT
        # the code which generates the id should NOT be changed because
        # it will be used to compose the name of the image as it will
        # be saved on the filesystem.
        # If for some reason this must be changed then all source images
        # must be deleted and re-downloaded.
        url = self.source_url
        filename = url.split('/')[-1]
        # create a unique hash on the basis of the url
        # (the hash code is created in this somewhat illogical way to
        # maintian compatibility with earlier versions)
        url_to_hash = '/'.join(url.split('/')[:-1])
        if '?' in url:
            url_to_hash = url

        def get_digest(astring):
            return md5(astring).hexdigest()
        digest = get_digest(url_to_hash)
        filename = filename.split('?')[0]
        filename = '%s_%s_%s' % (self._prefix, digest, filename)
        filename = filename.replace(' ', '-').lower()
        # this is gonna look like this:
        # "dvn_e46ebab5370e48685269f8b511762d3a_louise-van.oranjenassau.jpg"
        try:
            filename = unicode(filename)
        except:
            filename = filename.decode('utf8')
        return filename

    # --- deprecated attrs

    def create_id(self):
        raise ValueError("deprecated; use _create_id instead")

    def has_thumbnail(self, *args, **kwargs):
        raise ValueError("deprecated; not supposed to be u9sed")

    def thumbnail_url(self, *args, **kwargs):
        raise ValueError("deprecated; not supposed to be used")

    def cached_thumbnail_local(self, *args, **kwargs):
#       return os.path.join(self._images_cache_local,  'thumbnails', '%ix%i_%s'
#                            % (width, height, self.create_id()))
        raise ValueError("deprecated; not supposed to be used")
