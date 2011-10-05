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
    
