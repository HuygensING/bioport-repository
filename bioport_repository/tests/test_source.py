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

from bioport_repository.tests.common_testcase import CommonTestCase, unittest , THIS_DIR

from bioport_repository.source import *
from bioport_repository.repository import Repository


class SourceTestCase(CommonTestCase):
        
    def Xtest_source(self): 
        #XXX temporary disabled  tests pertaining to SVN
        url = os.path.abspath(os.path.join(THIS_DIR, 'data/knaw/list.xml'))
        assert os.path.exists(url), url
        url = 'file://%s' % url
        #add some sources source
        source = Source(id='test', url=url , description='test', quality=1)
        #check singleton behavior
        s2 = Source(id='test')
        self.assertEqual(source, s2)
        self.assertEqual(source.id, 'test')
        repo = self.repo 
        repo.save_source(source )
        #check if we can find the source on the filesystem
        abspath = Repository().svn_repository.absolute_path(source.id)
        assert os.path.exists(abspath), abspath
        abspath = os.path.join(abspath, '_source_information.xml')
        assert os.path.exists(abspath), abspath
        
        #and check if we can find it in the repository as well
        dirnames = Repository().svn_repository.ls()
        assert 'test' in dirnames, dirnames
#        source.download_data()
        ls = Repository().get_sources()
        assert source in ls, (source, ls)
        
        s2 = Repository().get_source(source.id)
        self.assertEqual(source, s2, (source.id, s2.id))
        
        #there should be 20 biographies
        source.download_data()
        
        bios = source.get_biographies()
        bios = list(bios)
        self.assertEqual(len(bios), 20, bios)
        
        assert source.path()
    def test_save_get_source(self): 
        repo = self.repo
        src = Source(id='foo', url='http://ladida.com', description='description', default_status=2)
        self.assertEqual(src.id, 'foo')
        repo.save_source(src)
        src = repo.get_source(src.id)
        self.assertEqual(src.id, 'foo')
        self.assertEqual(src.default_status, '2')
        
        
    def test_set_quality(self):
        i = self.repo 
        sources = i.get_sources()
        src1 = Source(id=u'test1', url = 'x', repository=i)
        i.save(src1)
        self.assertEqual(src1.quality , 0)       
        src2 = Source(id=u'test2', url = 'x', repository=i)
        i.save(src2)
        self.assertEqual(src2.quality , 0)       
        src3 = Source(id=u'test3', url = 'x', repository=i)
        i.save(src3)
        self.assertEqual(src3.quality , 0)       
        src4 = Source(id=u'test4', url = 'x', repository=i)
        i.save(src4)
        self.assertEqual(src4.quality , 0)       
        #last in is, by default, of lowest quality 
        self.assertEqual(i.get_sources(), sources + [src1, src2, src3, src4])
        #we say that src2 should have lowest quality
        src2.set_quality(0)
        src1.set_quality(1)
        src4.set_quality(2)
        self.assertEqual(src4.quality, 2, [(src.id, src.quality) for src in i.get_sources()])
        src3.set_quality(9)
        self.assertEqual(src3.quality, len(i.get_sources()) -1)
        

def test_suite():
    test_suite = unittest.TestSuite()
    tests = [SourceTestCase]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test))
    return test_suite

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')


