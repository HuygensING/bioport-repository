import os

from bioport_repository.tests.common_testcase import CommonTestCase, THIS_DIR, unittest
from bioport_repository.repository import Source
from bioport_repository.db_definitions import STATUS_NEW


class RepositoryTestCase(CommonTestCase):

    def test_download_changed_bios(self):
        repo = self.repo
        url = os.path.abspath(os.path.join(THIS_DIR, 'data/knaw/list.xml'))
        #add some sources source
        SOURCE_ID = u'test1'
        BASE = 10
        src = Source(id=SOURCE_ID, url=url , description='knaw test dinges')
        repo.add_source(src)
        repo.download_biographies(src)
        self.assertEqual(len(repo.get_persons()), BASE + 5)
        self.assertEqual(len(repo.get_persons(source_id=SOURCE_ID)),5,)
        
        old_persons = [repo.get_person(bioport_id) for bioport_id in repo.get_bioport_ids()]
        
        #if we download the information at our source, nothing should have changed 
        repo.download_illustrations(src)
        self.assertEqual(len(repo.get_persons()),BASE +  5)
        self.assertEqual(len(repo.get_persons(source_id=SOURCE_ID)),5,)
        self.assertEqual(set([p.bioport_id for p in old_persons]), set([p.bioport_id for p in repo.get_persons()]))
        
        repo.download_biographies(src)
        self.assertEqual(len(repo.get_persons()),BASE +  5)
        self.assertEqual(len(repo.get_persons(source_id=SOURCE_ID)),5,)
        self.assertEqual(set([p.bioport_id for p in old_persons]), set([p.bioport_id for p in repo.get_persons()]))
        
        #now we change the biographies that are available in some of the sources, and download again
        url2 = os.path.abspath(os.path.join(THIS_DIR, 'data/knaw_changed/list.xml'))
        src.url = url2
        repo.download_biographies(src)
        #the new url has one biograrphy less, and one new one. 
        #we remove the one that has disappeared, so the number of persons should now be the same as it was previously
        #1 has remained exactly the same
        #2 has disappeared 
        #3 has changed location - it is found in 006.xml
        #4 has changed name
        #5 has changed location, but should have the same data
        #7 is a new entry
        self.assertEqual(len(repo.get_persons(source_id=SOURCE_ID)),5,)
        #all of the old bioport_ids should still be available
        for p in old_persons:
            assert p.bioport_id in repo.get_bioport_ids()
        
        #create a dictionary with the persons from our test-source, accessabilble from their ID
        persons = {}
        for person in repo.get_persons(source_id=SOURCE_ID):
            knaw_bio = None
            for bio in person.get_biographies():
                if bio.get_source().id == SOURCE_ID:
                    knaw_bio = bio
            person.knaw_bio = knaw_bio 
            id = knaw_bio.get_id().split('/')[1]
            for i in range(1,10):
                if id == '00%s' % i:
                    persons[i] = person
        #person 2 has disappeared 
        self.assertTrue(2 not in persons, persons)
        #3 has changed location - it is found in 006.xml. 
        assert persons[3].knaw_bio.source_url.endswith('006.xml'), persons[3].knaw_bio.source_url
        
        #person 4 has a changed name
        #XXX we should test this somehow
        assert 'changed' in persons[4].name(), persons[4].name()
        #person 5 has changed location
        assert persons[5].knaw_bio.source_url.endswith('005a.xml'), persons[5].knaw_bio.source_url
        #person 7 is a new entry
        self.assertEqual( persons[7].status, unicode(STATUS_NEW))
        
    def test_delete_effects(self):
        repo = self.repo
        url = os.path.abspath(os.path.join(THIS_DIR, 'data/knaw/list.xml'))
        SOURCE_ID = u'test1'
        src_knaw = src = Source(id=SOURCE_ID, url=url , description='knaw test dinges...', repository=self.repo)
        self.assertEqual(src.url, url)
        repo.add_source(src)
        repo.download_biographies(src)
        repo.delete_biographies(src)
        src_knaw.url = os.path.join(THIS_DIR, 'data/knaw2/list.xml')
        repo.download_biographies(src_knaw)
        
        i= 0
        for person in repo.get_persons():
            i += 1
            bio = repo.get_bioport_biography(person)
            bio.set_value('geboortedatum_tekst',  '000%s'% i)       
            
    def test_identification_and_editing_effects(self):
        repo = self.repo
        #we start with 10 people
        BASE = 10
        SOURCE_ID = u'test1'
        SOURCE_ID2 = u'test2'
        self.assertEqual(len(repo.get_persons()), BASE)
        url = os.path.abspath(os.path.join(THIS_DIR, 'data/knaw/list.xml'))
        src1 = src = Source(id=SOURCE_ID, url=url , description='knaw test dinges...')
        self.assertEqual(src.url, url)
        repo.add_source(src)
        repo.download_biographies(src)
        persons = repo.get_persons()
        self.assertEqual(len(persons), BASE+5)
       
        url = os.path.abspath(os.path.join(THIS_DIR, 'data/knaw2/list.xml'))
        src2 = Source(id=SOURCE_ID2, url=url , description='knaw test dinges')
        repo.add_source(src2)
        repo.download_biographies(src2)
        persons = repo.get_persons()
        
        #check sanity - we should have 10 new persons, 5 from each source
        self.assertEqual(len(repo.get_persons(source_id=SOURCE_ID)), 5)
        self.assertEqual(len(repo.get_persons(source_id=SOURCE_ID2)), 5)
        self.assertEqual(len(persons), BASE + 10)
        i = 0
        for person in repo.get_persons():
            i += 1
            bio = repo.get_bioport_biography(person)
            bio.set_value('geboortedatum_tekst',  '000%s'% i)
            self._save_biography(bio)            

        persons = {} 
        j = 0
        for person in repo.get_persons():
            j += 1
            knaw_bio = None
            for bio in person.get_biographies():
                if bio.get_source().id in [SOURCE_ID, SOURCE_ID2]:
                    knaw_bio = bio
                    person.knaw_bio = knaw_bio 
                    id = knaw_bio.get_id().split('/')[1]
                    for i in range(1,11):
                        if id == '00%s' % i:
                            persons[i] = person       
       
        #person 3 will diasppear, person 5 will change location
        person2 = repo.identify(persons[2], persons[7])
        person5 = repo.identify(persons[5], persons[8])
        #check sanity
        self.assertEqual(len(person2.get_biographies()), 4)
        self.assertEqual(len(person5.get_biographies()), 4)
        #we identified two pairs, so now we have two persons less
        self.assertEqual(len(repo.get_persons()), BASE+ 8)
        self.assertEqual(len(repo.get_persons(source_id=SOURCE_ID)), 5)
        self.assertEqual(len(repo.get_persons(source_id=SOURCE_ID2)), 5)
        
        i = 0
        for person in repo.get_persons():
            i += 1
            bio = repo.get_bioport_biography(person)
            bio.set_value('geboortedatum_tekst',  '000%s'% i)
            self._save_biography(bio)        
        
        #if we download the biographies again, nothing should have changed 
        repo.download_biographies(src1)
        repo.download_biographies(src2)
        
        self.assertEqual(len(repo.get_persons()), BASE+ 8)
        self.assertEqual(len(repo.get_persons(source_id=SOURCE_ID)), 5)
        self.assertEqual(len(repo.get_persons(source_id=SOURCE_ID2)), 5)
        
        #now we change the url from src1. IT differs - it adds one new biography (007) and removes #002
        src1.url = os.path.join(THIS_DIR, 'data/knaw_changed/list.xml')
        repo.download_biographies(src1)
        self.assertEqual(len(repo.get_persons(source_id=SOURCE_ID)), 5)
        self.assertEqual(len(repo.get_persons(source_id=SOURCE_ID2)), 5)
        self.assertEqual(len(repo.get_persons()), BASE + 9)
        
        #reload the information of our two sample  person2 
        person2 = repo.get_person(person2.bioport_id)
        person5 = repo.get_person(person5.bioport_id)
        
        #we removed the src2 biography of person2
        self.assertEqual(len(person2.get_biographies(source_id=SOURCE_ID)), 0)
        self.assertEqual(len(person2.get_biographies(source_id=SOURCE_ID2)), 1)
        self.assertEqual(len(person5.get_biographies(source_id=SOURCE_ID)), 1)
        self.assertEqual(len(person5.get_biographies(source_id=SOURCE_ID2)), 1)
        
            
    def test_removal_of_bios(self):
        #one of the biographies of person1 has been removed
        #1. the biography should not be there anymore
        #2. the bioport_id shoudl still exist
        #3. if we have no more biographies for this person, the person shoudl disappear 
        repo = self.repo
        url1 = os.path.abspath(os.path.join(THIS_DIR, 'data/knaw/list.xml'))
        url2 = os.path.abspath(os.path.join(THIS_DIR, 'data/knaw_changed/list.xml'))
        
        src = Source(id=u'test', url=url1 , description='knaw test dinges')
        repo.add_source(src)
        
        repo.download_biographies(src)
        
        person2 = repo.get_biography(local_id='test/002').get_person()
        bioport_id3 = person2.bioport_id
       
        #now we change the biographies that are available in some of the sources
        src.url = url2
        repo.download_biographies(src)
        
        #now the biography of person2 does not exist anymore
        self.assertEqual(len(list(repo.get_biographies(local_id='test/002'))), 0)
        #and neither does person2 himself
        assert person2.bioport_id not in [p.bioport_id for p in repo.get_persons()],  [(p.bioport_id, p.get_biographies()) for p in repo.get_persons()]
        
        #we still, however, should have the bioport_id in our repository
        self.assertEqual(repo.db.get_bioport_id(biography_id='test/002'), person2.bioport_id )
        
        #now we re-download the old data
        src.url = url1
        repo.download_biographies(src)
        #and we have the 5 old biographies again
        self.assertEqual(len(repo.get_persons(source_id=src.id)), 5)
        self.assertEqual(len(list(repo.get_biographies(local_id='test/002'))), 1)
        
        #it is very important that our newly re-donloaed test/002 has the same bioport id as before
        self.assertEqual(repo.get_biography(local_id='test/002').get_person().bioport_id, bioport_id3)
       
        #now, we do the same exercise of removing and re-adding, but this time we identify test/002 with test/005
        person5 = repo.get_biography(local_id='test/005').get_person()
        new_person = repo.identify(person5, person2)
        
        #we have now one person less
        self.assertEqual(len(repo.get_persons(source_id=src.id)), 4)
        self.assertEqual(len(new_person.get_biographies()), 2)
        
        src.url = url2
        repo.download_biographies(src)
        self.assertEqual(len(list(repo.get_biographies(source_id=src.id))), 5)
        self.assertEqual(len(repo.get_persons(source_id=src.id)), 5, [p.get_biographies() for p in repo.get_persons(source_id=src.id)])
        new_person = repo.get_person(bioport_id=new_person.bioport_id)
        self.assertEqual(len(new_person.get_biographies()), 1)
        

def test_suite():
    test_suite = unittest.TestSuite()
    tests = [RepositoryTestCase]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test, prefix='test_'))
    return test_suite

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')    


