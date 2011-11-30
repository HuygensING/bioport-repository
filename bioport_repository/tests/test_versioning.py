# encoding=utf8
from bioport_repository.tests.common_testcase import CommonTestCase, unittest 
#from bioport_repository.biography import Biography
import datetime
import time
class VersioningTestCase(CommonTestCase):

    def test_identification_versioning(self):
        self.create_filled_repository()
        repo = self.repo
        versions = self.repo.get_versions()
        cntr = len(versions)
        #now make a change, and see if the last version represents the change
        persons = repo.get_persons()
        p1, p2 = persons[0], persons[1]
        repo.identify(p1, p2)
        
        versions = self.repo.get_versions()
        self.assertEqual(len(versions), cntr + 1)

    def test_get_versions(self):
        repo = self.repo
        bio = list(repo.get_biographies())[0]
        bio.set_category([3])
        self._save_biography(bio, u'test_comment')
        self.assertEqual(len(repo.get_versions(document_id=bio.id)), 2)
        
        #test searching versions by user
        user = self.repo.user = 'test123'
        self._save_biography(bio, u'test_comment')
        self.assertEqual(len(repo.get_versions(user=user)), 1)
       
        #test searching users by time
        time.sleep(1)
        time0 = datetime.datetime.today().isoformat()
        self._save_biography(bio, u'test_comment')
        time.sleep(1)
        time1 = datetime.datetime.today().isoformat()
        time.sleep(1)
        self._save_biography(bio, u'test_comment')
        self.assertEqual(len(repo.get_versions(time_from=time1)), 1)
        self.assertEqual(len(repo.get_versions(time_from=time0, time_to=time1)), 1)
        self.assertEqual(len(repo.get_versions(time_to=time0)), len(repo.get_versions()) - 1)
        
    def test_undo(self):
        repo = self.repo
        bio = list(repo.get_biographies())[0]
        bioport_id = bio.get_bioport_id()
        date1 = '1111-01-01'
        date2 = '2222-01-01'
        bio.set_value(birth_date=date1)
        self._save_biography(bio, u'test_comment')
        
        bio.set_value(birth_date=date2)
        self._save_biography(bio, u'test_comment')
        
        versions = repo.get_versions(document_id=bio.id)
        #sanity check
        self.assertEqual(len(versions), 3)
        #we check that the version 1 is the one with category 3
        self.assertEqual(versions[1].version, 1)
        self.assertEqual(versions[1].biography.get_value('birth_date'), date1)
        self.assertEqual(versions[0].biography.get_value('birth_date'), date2)
        
        person = repo.get_person(bioport_id=bioport_id) 
        self.assertEqual(person.get_value('birth_date'), date2)
        repo.undo_version(document_id=bio.id, version=0)
        person = repo.get_person(bioport_id=bioport_id) 
        self.assertEqual(person.get_value('birth_date'), date1)
        
    
    def test_undo_identification(self):
        repo = self.repo
        persons = self.repo.get_persons()
        len1 = len(self.repo.get_persons())
        bioport_ids1 = [p.bioport_id for p in self.repo.get_persons()]
        bioport_ids2numberofbios1 = dict([(p.bioport_id, p.get_biographies()) for p in self.repo.get_persons()])
        for id1 in bioport_ids1:
            self.assertEqual(repo.redirects_to(id1), id1)
        p1, p2 = persons[0], persons[1]
        new_p = repo.identify(p1, p2)
        old_p = new_p == p1 and p2 or p1
        self.assertEqual(repo.redirects_to(old_p.bioport_id), new_p.bioport_id)
        len2 = len(self.repo.get_persons())
        _bioport_ids2 = [p.bioport_id for p in self.repo.get_persons()]
        
        #undo any changes in the biodes documents
        for bio in new_p.get_biographies():
            if repo.get_versions(document_id=bio.id, version=1):
                repo.undo_version(document_id=bio.id, version=0)
        len3 = len(self.repo.get_persons())
        bioport_ids3 = [p.bioport_id for p in self.repo.get_persons()]
        bioport_ids2numberofbios3 = dict([(p.bioport_id, p.get_biographies()) for p in self.repo.get_persons()])
                
        #now, by refreshment magic, the number of persons should again be equal to the old one
        self.assertEqual(len1 -1, len2)
        self.assertEqual(len2 +1, len3)
        #and our old bioport_id's should be all back
        self.assertEqual(set(bioport_ids1),set( bioport_ids3))
        #moreover, "redirection info" should be back to normal (no bioport_id redirects to another) 
        for id1 in bioport_ids3:
            self.assertEqual(repo.redirects_to(id1), id1)
        
        #now, having undone all changes, the number of biographies of our old people should be the same as the new ones
        self.assertEqual(bioport_ids2numberofbios1,bioport_ids2numberofbios3  )
        
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(VersioningTestCase),
        ))


if __name__=='__main__':
    unittest.main(defaultTest='test_suite')

