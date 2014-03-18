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

import os
#import sys
import unittest
import shutil

import datetime
from bioport_repository.common import to_date, format_date


class CommonTestCase(unittest.TestCase):
    
    def test_to_date(self):
        self.assertEqual(to_date('2000'), datetime.datetime(2000, 1, 1, 0, 0))
        self.assertEqual(to_date('2000-02'), datetime.datetime(2000, 2, 1, 0, 0))
        self.assertEqual(to_date('2000-02-03'), datetime.datetime(2000, 2, 3, 0, 0))
        self.assertEqual(to_date('2001-02', round='up'), datetime.datetime(2001, 2, 28, 0, 0))
        #2000 is a leap year
        self.assertEqual(to_date('2000-02', round='up'), datetime.datetime(2000, 2, 29, 0, 0))
        self.assertEqual(to_date('2000-12', round='up'), datetime.datetime(2000, 12, 31, 0, 0))
 
        self.assertEqual(to_date('2000', round='up'), datetime.datetime(2000, 12, 31, 0, 0))
        self.assertEqual(to_date('0200', round='up'), datetime.datetime(200, 12, 31, 0, 0))
        self.assertEqual(to_date('1200', ), datetime.datetime(1200, 1, 1, 0, 0))
    
    def test_format_date(self):
        d = datetime.datetime(1700, 3, 2)
        self.assertEqual(format_date(d), '1700-03-02 00:00')
        d = datetime.datetime(1, 3, 2)
        self.assertEqual(format_date(d), '0001-03-02 00:00')
        
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(CommonTestCase, 'test'),
        ))


if __name__=='__main__':
    unittest.main(defaultTest='test_suite')


