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

from bioport_repository.tests.common_testcase import CommonTestCase

from bioport_repository.source import Source
from bioport_repository.db_definitions import SOURCE_TYPE_PORTRAITS


class SourceTestCase(CommonTestCase):

    def test_save_get_source(self):
        repo = self.repo
        src = Source(id='foo', url='http://ladida.com', description='description', default_status=2, source_type=SOURCE_TYPE_PORTRAITS)
        self.assertEqual(src.id, 'foo')
        repo.save_source(src)
        src = repo.get_source(src.id)
        self.assertEqual(src.id, 'foo')
        self.assertEqual(src.default_status, 2)
        self.assertEqual(src.source_type, SOURCE_TYPE_PORTRAITS)

    def test_set_quality(self):
        i = self.repo
        sources = i.get_sources()
        src1 = Source(id=u'test1', url='x', repository=i)
        i.save(src1)
        self.assertEqual(src1.quality, 0)
        src2 = Source(id=u'test2', url='x', repository=i)
        i.save(src2)
        self.assertEqual(src2.quality, 0)
        src3 = Source(id=u'test3', url='x', repository=i)
        i.save(src3)
        self.assertEqual(src3.quality, 0)
        src4 = Source(id=u'test4', url='x', repository=i)
        i.save(src4)
        self.assertEqual(src4.quality, 0)
        # last in is, by default, of lowest quality
        self.assertEqual(i.get_sources(), sources + [src1, src2, src3, src4])
        # we say that src2 should have lowest quality
        src2.set_quality(0)
        src1.set_quality(1)
        src4.set_quality(2)
        self.assertEqual(src4.quality, 2, [(src.id, src.quality) for src in i.get_sources()])
        src3.set_quality(9)
        self.assertEqual(src3.quality, len(i.get_sources()) - 1)
