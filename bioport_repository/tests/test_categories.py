##########################################################################
# Copyright (C) 2009 - 2014 Huygens ING & Gebrandy S.R.L.
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

from bioport_repository.tests.common_testcase import CommonTestCase, unittest 
from bioport_repository.db import *

class CategoryTestCase(CommonTestCase):
        
    def test_workflow(self): 
        db = self.db
        db._update_category_table()
        repo = self.repo
        ls = repo.get_categories()
        self.assertEqual(len(ls), 16)
        some_element = ls[4]
        id = some_element.id
        assert repo.get_category(id)
        self.assertEqual(repo.get_category(id).name, some_element.name)
        
        #get a biography
        self.create_filled_repository()
        biography = list(self.db.get_biographies())[0]
        biography.add_or_update_state(type='category', idno=str(some_element.id), text=some_element.name)
        
        #assert 0, biography.to_string()
        
        
        #now, if we get the occupation from the biography, it is the one we just set
        self.assertEqual(len( biography.get_states(type='category')), 1)
        #self.assertEqual(biography.get_state(type='occupation').get('idno'), id)


def test_suite():
    test_suite = unittest.TestSuite()
    tests = [CategoryTestCase]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test))
    return test_suite 

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
    
