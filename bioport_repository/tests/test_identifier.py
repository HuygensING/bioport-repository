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

class IdentifierTestCase(CommonTestCase):
        
    def test_generators(self):       
        i = self.repo 
        
        id1 = i.db.fresh_identifier()
        id2 = i.db.fresh_identifier()
        self.assertNotEqual(id1, id2)
        
        self.create_filled_repository()
        some_person = self.repo.get_persons()[4]
        id = some_person.get_bioport_id()
        self.repo.delete_person(some_person)


def test_suite():
    test_suite = unittest.TestSuite()
    tests = [IdentifierTestCase]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test))
    return test_suite 

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
