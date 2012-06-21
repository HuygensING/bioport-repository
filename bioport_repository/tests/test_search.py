from bioport_repository.tests.common_testcase import CommonTestCase, unittest 

class SearchTestCase(CommonTestCase):
    
    def test_get_persons(self):
        repo = self.repo
        #check sanity
        self.assertEqual(len(repo.get_persons()), 10)
       
        #add a number of persons
        pius = self._add_person('Pius IX')
        #we do not want to find Pius IX if we search for 'ik'
        self.assertEqual(list(repo.get_persons(search_name=u'IX')), [pius])
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

