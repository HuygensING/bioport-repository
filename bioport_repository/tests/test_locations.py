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

class DBRepositoryTestCase(CommonTestCase):
       
    def test_workflow(self): 
        db = self.db
        db._update_geolocations_table(limit=100)
        locations = db.get_locations()
        self.assertEqual(len(locations), 100)
            
        #get the locations that start with 'a'
        locations = db.get_locations(startswith='a')
        assert locations
        #there is one Anjum (within the first 100 on the list) 
        locations = db.get_locations(name='Anjum')
        self.assertEqual(len(locations), 1)
        
       
        location = locations[0]
        
        location.adm1 = '02' #amsterdam is in friesland
        
        #set the location of a biography
        
        #get a biography
        self.create_filled_repository()
        biography = list(self.db.get_biographies())[0]       
        biography.add_or_update_event(type="birth", place_id=location.ufi)
        

def test_suite():
    test_suite = unittest.TestSuite()
    tests = [DBRepositoryTestCase]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test))
    return test_suite

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')    


