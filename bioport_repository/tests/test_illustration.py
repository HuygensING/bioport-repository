#!/usr/bin/env python
#encoding=utf8

import os
import urllib2
import unittest
from cStringIO import StringIO
import shutil

try:
    from PIL import Image
except ImportError:
    import Image

from bioport_repository.tests.common_testcase import CommonTestCase, IMAGES_CACHE_LOCAL
#from bioport_repository.illustration import MEDIUM_THUMB_SIZE
from bioport_repository.illustration import Illustration, CantDownloadImage

#(all the encode(ENC) loops are for getting text

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
url_root = 'file://%s/data/images/' % THIS_DIR
images = u'%s/data/images/' % THIS_DIR
images_cache_local = IMAGES_CACHE_LOCAL 
images_cache_url = 'file://%s' % IMAGES_CACHE_LOCAL 
fn = u'image1.jpg'
#this unicode stuff gives problems
fn2 = 'imege.jpg'


class IllustrationTestCase(CommonTestCase):

    def setUp(self): 
        CommonTestCase.setUp(self)
        #fn2 has a unicode name, which trips up svn, so we copy it and later remove it
#        fn2 = fn2.decode('utf8')
        shutil.copyfile(os.path.join(images, fn), os.path.join(images, fn2))

    def test_create_id(self):
        ill = Illustration(url='xxx', images_cache_local=images_cache_local, images_cache_url=images_cache_url)
        assert ill.id.endswith('xxx')
        ill = Illustration('xxx?asdf=xfajl&adsfklj=x', images_cache_local=images_cache_local, images_cache_url=images_cache_url)
        ill2 = Illustration('xxx?asdf=aaa&adsfklj=x',  images_cache_local=images_cache_local, images_cache_url=images_cache_url)
        assert ill.id.endswith('xxx')
        self.assertNotEqual(ill.id, ill2.id)
        
    def test_illustration_standalone(self):
        ill = Illustration(
            url=os.path.join(url_root ,fn), 
            images_cache_local=images_cache_local,
            images_cache_url =images_cache_url,
            prefix = 'test',
            )
        ill.download()
        local_fn =  ill.images_directory
        self.failUnless(os.path.exists(local_fn))
#        self.failUnless(urllib2.urlopen(ill.image_url).read()) # XXX failing because it's a fs pathname
        
        ill = Illustration(
            url=os.path.join(url_root ,fn2), 
            images_cache_local=images_cache_local,
            images_cache_url =images_cache_url,
            prefix = 'test'
            )
        ill.download()
        image_path = ill.images_directory
        self.failUnless(os.path.exists(image_path))
        self.failUnless(os.listdir(images_cache_local))
        
    def test_illustration_in_repository(self):
        repo = self.repo
        repo.images_cache_local = images_cache_local
        repo.images_cache_url = images_cache_url
        
        [repo.download_illustrations(s) for s in repo.get_sources()]
        for person in [p for p in repo.get_persons() if p.has_illustrations]:
            for biography  in person.get_biographies():
                for illustration in biography.get_illustrations():
                    # should have downloaded this image
                    try:
                        illustration.download()
                    except CantDownloadImage:
                        continue
                    self.failUnless(os.path.exists(illustration.images_directory))
                    path = illustration.images_directory
                    self.failUnless(os.path.exists(path))

    def test_illustration_with_same_name_as_another(self):
        repo = self.repo
        repo.images_cache_local = images_cache_local
        repo.images_cache_url = images_cache_url
        [repo.download_illustrations(s) for s in repo.get_sources()]
        illustrations = []
        for person in [p for p in repo.get_persons()
                        if p.has_illustrations]:
            for biography  in person.get_biographies():
                for illustration in biography.get_illustrations():
                    illustrations.append(illustration)
#        illustration_paths = [a.images_directory for a in illustrations]


class ThumbnailTestCase(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(images_cache_local):
            os.mkdir(images_cache_local)
        super(ThumbnailTestCase, self).setUp()
        self.ill = Illustration(
            url=os.path.join(url_root ,fn), 
            images_cache_local=images_cache_local,
            images_cache_url =images_cache_url,
            prefix = 'test'
            )

    def test_thumbnail_generation(self):
        ill = self.ill
        ill.download()
        data = urllib2.urlopen(ill.image_small_url).read()
        _img = Image.open(StringIO(data))


def test_suite():
    test_suite = unittest.TestSuite()
    tests = [IllustrationTestCase, ThumbnailTestCase]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test))
    return test_suite

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')    
