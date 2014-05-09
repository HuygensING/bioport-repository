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

from bioport_repository.tests.common_testcase import CommonTestCase, unittest 

class SearchTestCase(CommonTestCase):
    
    def test_get_persons(self):
        repo = self.repo
        #check sanity
        self.assertEqual(len(repo.get_persons()), 10)
       
        #add a number of persons
        pius = self._add_person('Pius IX')
        #we do not want to find Pius IX if we search for 'ik'
        persons = repo.get_persons(search_name=u'IX')
        plist = list(persons)
        self.assertEqual(plist, [pius])
        assert pius not in repo.get_persons(search_name=u'ik')
        
        self.assertEqual(len(repo.get_persons(search_name=u'molloyx')), 1)
        self.assertEqual(len(repo.get_persons(search_name=u'boschma')), 9) 
        self.assertEqual(len(repo.get_persons(search_name=u'bosma')), 9) 
        self.assertEqual(len(repo.get_persons(search_name='bo?ma')), 9)
        self.assertEqual(len(repo.get_persons(search_name=u'"mollo??"')), 1)
        self.assertEqual(len(repo.get_persons(search_name=u'"mollo*"')), 1)

        
        return
        
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(SearchTestCase, 'test'),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

