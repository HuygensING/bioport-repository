import os

from bioport_repository.tests.common_testcase import CommonTestCase, unittest , THIS_DIR
from bioport_repository.repository import  Source, Biography 
from bioport_repository.db_definitions import (
   CacheSimilarityPersons, AntiIdentifyRecord, STATUS_NEW,
   STATUS_ONLY_VISIBLE_IF_CONNECTED,
   )
                                               
from bioport_repository.person import Person


class RepositoryTestCase(CommonTestCase):

    def test_download_bios(self):
        url = os.path.abspath(os.path.join(THIS_DIR, 'data/knaw/list.xml'))
        #add some sources source
        src = Source(id=u'test', url=url , description=u'test')
        self.repo.add_source(src)
    
        self.repo.download_biographies(src)
        assert len(list(self.repo.get_biographies()))

    def test_get_persons(self):
        self.assertEqual(len(self.repo.get_persons()), 10)
        self.assertEqual(self.repo.count_persons(), 10)
        
    def test_get_persons_sequence(self):
        persons = self.repo.get_persons_sequence()
        self.assertEqual(len(persons), 10)
        b_persons = self.repo.get_persons_sequence(beginletter='b')
        assert 0<len(b_persons) <  len(persons) #not all person names start with a 'b'

    def test_created_repository(self):
        repo = self.create_filled_repository()
        
        bios = repo.get_biographies()
        self.assertEqual(len(bios), 10)
        bio = bios[3]
        assert bio.get_value('local_id')
        assert bio.get_value('bioport_id')
    
    def test_add_biography(self):
        #make a new biography
        source = Source(id=u'bioport_test')
        self.repo.add_source(source)
        bio = Biography( id = u'test_bio.xml', source_id=source.id)
        
        #XXX Do we need this?
        bio.from_args( 
              url_biografie='http://ladida/didum', 
              naam_publisher='nogeensiets', 
              url_publisher='http://pbulihser_url',
              naam='Tiedel Doodle Dum',
              local_id='123',
              )
        
        #save it
        self._save_biography(bio)
        assert bio.get_bioport_id()
        self.assertEqual(bio.repository, self.repo)
        
    def test_get_biographies(self):
        self.create_filled_repository()
        bios = self.repo.get_biographies()
        bio = list(bios)[2]
        id =bio.get_bioport_id()
        assert id, bio.to_string()
        p = Person(id)
        source = bio.get_source()
        self.assertEqual([b.id for b in self.repo.get_biographies(bioport_id=id)], [bio.id])
        self.assertEqual(len(list(self.repo.get_biographies(source=source))), 5)
        self.assertEqual(self.repo.get_biographies(bioport_id=id, source=bio.get_source()), [bio])
    
        self.assertEqual(self.repo.count_biographies(), len(list(self.repo.get_biographies())))
        self.assertEqual(self.repo.count_biographies(source=source), 5)
                   
    def test_source_manipulation(self):  
        i = self.repo 
        url = 'file://%s' % os.path.abspath(os.path.join(THIS_DIR, 'data/knaw/list.xml'))
        sources = i.get_sources()
        
        #add some sources source
        src1 = Source(id=u'test', url=url , description=u'test')
        i.add_source(src1)
        
        src2 = i.add_source(Source(id=u'test2', url=url , description=u'test2 description'))
       
        self.assertEqual(len(i.get_sources()), len(sources) + 2, i.get_sources())
        #and the source we added is among  them
        assert 'test' in [s.id for s in i.get_sources()], i.get_sources()
      
        self.assertEqual(src2.url, url)
        self.assertEqual(src2.description,'test2 description')
        
        i.download_biographies(src1)
        self.assertEqual(len(list(i.get_biographies(source=src1))), 5)
        
        i.delete_biographies(src1)
        self.assertEqual(len((i.get_biographies(source=src1))), 0)
        
        i.download_biographies(source=src1)
        self.assertEqual(len((i.get_biographies(source=src1))), 5)
        
        i.delete_biographies(src1)
        self.assertEqual(len((i.get_biographies(source=src1))), 0)
        
        #the source is also in the repository         
        #see if we can delete the source
        i.delete_source(Source(u'test'))
        self.assertEqual(len(i.get_sources()), 1 + len(sources))
        
        self.assertEqual(len((i.get_biographies(source=Source('test')))), 0)
        
    def test_refill(self):
        self.create_filled_repository()
        #now donwload the data from the first source a seond time
        
       
    def test_redirect_to(self):
        repo = self.create_filled_repository()
        bioport_ids = repo.get_bioport_ids()
        id1 = bioport_ids[1]
        id2 = bioport_ids[2]
        self.assertEqual(repo.redirects_to(id1), id1)
        repo.redirect_identifier(id1, id2)
        self.assertEqual(repo.redirects_to(id1), id2)
        

        
    def test_bioport_biography(self):
        repo = self.create_filled_repository()
        person = repo.get_persons()[2]
        
        #get the bioport biography (the one used for editing)
        bio = repo.get_bioport_biography(person)
        #check sanity
        self.assertEqual(bio.get_value('bioport_id'), [person.get_bioport_id()]) 
        self.assertEqual(self.repo.db.get_sources()[0], bio.get_source())
        #set a value
        bio.set_value('geboortedatum', '1999-01-01')
        self.assertEqual(bio.get_value('geboortedatum'), '1999-01-01')
        self._save_biography(bio)
        
        self.assertEqual(bio.get_value('geboortedatum'), '1999-01-01')
        
        self.assertEqual(person.get_merged_biography().get_value('geboortedatum'), '1999-01-01')
        
        bio.set_value('geboortedatum', '1999-01-02')
        self.assertEqual(bio.get_value('geboortedatum'), '1999-01-02')
        self._save_biography(bio)
        self.assertEqual(self.repo.get_person(person.bioport_id).get_merged_biography().get_value('geboortedatum'), '1999-01-02')
        
        bio.set_religion('3')
        self.assertEqual(bio.get_religion().get('idno'), '3')
        self._save_biography(bio)
        self.assertEqual(self.repo.get_person(person.bioport_id).get_merged_biography().get_religion().get('idno'), '3')
     
    def test_save_biography(self):
        source = Source(id='bioport_test')
        self.repo.add_source(source)
        bio = Biography(id='test_bio.xml', source_id=source.id)
        
        name = 'Name1'
        #XXX Do we need this?
        bio.from_args( 
              url_biografie='http://ladida/didum', 
              naam_publisher='nogeensiets', 
              url_publisher='http://pbulihser_url',
              naam=name,
              local_id='123',
              )
        self.assertEqual(len(bio.get_idnos()), 1, bio.to_string())
        self._save_biography(bio)
        #we now have two idnos: the local "id", and the "bioport_id"
#        assert 0, bio.xpath('person/idno')
        self.assertEqual(len(bio.get_idnos(type=None)), 2, bio.to_string())
        
        self.assertEqual(self.repo.get_biography(bio.id).naam().volledige_naam(), name)
        name = 'Name2'
        bio.set_value('namen', [name])
        self._save_biography(bio)
        biography_from_repo = list(self.repo.get_biographies(local_id=bio.id))[0]
        self.assertEqual(biography_from_repo.naam().volledige_naam(), name)
        
        biography_record = list(self.repo.db._get_biography_records(local_id=bio.id))[0]
        self.assertEqual(biography_record.url_biography , bio.get_value('url_biography'))
                
        self.assertEqual(len(bio.get_idnos(type=None)), 2, bio.to_string())
    
    def test_number_of_biographies_in_database(self): 
        source = Source(id='bioport_test')
        bio_id = 'test_bio.xml'
        self.repo.add_source(source)
        bio = Biography( id = bio_id , source_id=source.id)
        
        self._save_biography(bio)
        
        def get_versions():
            return list(self.repo.db._get_biography_records(local_id=bio_id))
        
        
        self.assertEqual(len(get_versions()), 1)
        self._save_biography(bio)
        self.assertEqual(len(get_versions()), 2)
        self.assertEqual([r.version for r in get_versions()], [0,1])
        self._save_biography(bio)
        self.assertEqual(len(get_versions()), 3)
        self.assertEqual([r.version for r in get_versions()], [0,1, 2])
        
    def test_antiidentify(self):
        repo = self.create_filled_repository()
        persons = repo.get_persons()
        self.repo.db.SIMILARITY_TRESHOLD = 0.0
        self.repo.db.fill_similarity_cache(minimal_score=0.0)
        ls = self.repo.get_most_similar_persons()
        score, p1, p2 = ls[1]
#        assert 0, [(p.get_bioport_id(), p2.get_bioport_id()) for score, p, p2 in ls]
        #we have n candidates
        n = len(ls)
        self.assertEqual(len(list(ls)), n)
        #now we anti-identify one pair
        repo.antiidentify(p1, p2)
        #check if we really anti-identified only one pair
        self.assertEqual(self.repo.db.get_session().query(AntiIdentifyRecord).count(), 1)
        self.assertTrue(repo.is_antiidentified(p1, p2))
        
        #so, now we must have 1 less person left
        ls = self.repo.get_most_similar_persons()
        self.assertEqual(len(list(ls)), n-1)

        self.assertEqual(len(list(repo.get_antiidentified())), 1)    


    def test_get_bioport_biography(self):
        repo = self.repo
        persons = repo.get_persons()
        p = persons[1]
        bioport_bio = repo.get_bioport_biography(p)
        self.assertTrue(bioport_bio in p.get_biographies())
        bioport_bio = repo.get_bioport_biography(p)
        self.assertTrue(bioport_bio in p.get_biographies())
        
    def test_unidentify(self):
        repo = self.repo
        persons = repo.get_persons()
        p1 = persons[1]
        p2 = persons[2]
        id1 = p1.bioport_id
        id2 = p2.bioport_id
        
        #identify two persons
        p = repo.identify(p1, p2)
        #the new person has one of the original bioport ids
        id = p.bioport_id
        self.assertTrue(id in [id1, id2])  
        self.assertEqual(len(repo.get_identified()), 1)
        
        #add some bioport-edited info to our new person
        bioport_bio = repo.get_bioport_biography(p)
        self.assertTrue(bioport_bio in p.get_biographies())
        
        #now unidentify them again
        ls = repo.unidentify(p)
        
        #we should get two persons back
        self.assertEqual(len(ls), 2)
        p3, p4 = ls
        id3 = p3.bioport_id
        id4 = p4.bioport_id
        
        #each of the new persons is associated with a single biogrpahy
        self.assertEqual(len(p3.get_biographies()),1)
        self.assertEqual(len(p4.get_biographies()),1)
        
        #these new persons have been saved in the repository
        p3 = repo.get_person(id3)
        p4 = repo.get_person(id4)
        
        #they use the same old ids
        self.assertTrue(id1 in [id3, id4], [id1, id2, id3, id4, id])
        self.assertTrue(id2 in [id3, id4])
        self.assertEqual(len(p3.get_biographies()),1)
        self.assertEqual(len(p4.get_biographies()),1)
       
        #sanity? the biography should refer to the old id
        self.assertEqual(p3.get_biographies()[0].get_idno('bioport'), id3)
        self.assertEqual(p4.get_biographies()[0].get_idno('bioport'), id4)
        
        self.assertEqual(len(repo.get_identified()), 0)
        
        #the status of the two people should be back to new
        self.assertEqual(p3.status, STATUS_NEW)
        self.assertEqual(p4.status, STATUS_NEW)
    
        
    def test_detach_biography(self):
        repo = self.repo
        persons = repo.get_persons()
        p1 = persons[1]
        p2 = persons[2]
        bio1 = p1.get_biographies()[0]
        bio2 = p1.get_biographies()[0]
        id1 = p1.bioport_id
        id2 = p2.bioport_id
        
        #identify two persons
        p = repo.identify(p1, p2)
        #the new person has one of the original bioport ids
        id = p.bioport_id
        self.assertTrue(id in [id1, id2])  
        self.assertEqual(len(repo.get_identified()), 1)
        
        #add some bioport-edited info to our new person
        bioport_bio = repo.get_bioport_biography(p)
        self.assertTrue(bioport_bio in p.get_biographies())
        
        self.assertTrue(len(p.get_biographies()), 3)
        
        #now detach the old biography, and create a new person
        new_person = self.repo.detach_biography(bio1)
        
        #is it really detached?
        self.assertTrue(len(p.get_biographies()), 2)
        self.assertTrue(len(new_person.get_biographies()), 1)
        
        #this new persons have been saved in the repository
        self.assertTrue(repo.get_person(new_person.bioport_id))
        
        #the status of the new person should be back to new
        self.assertEqual(new_person.status, STATUS_NEW)
    
    
    def test_fill_similarity_cache(self):
        self.repo.db.fill_similarity_cache(refresh=True)
        source_id = self.repo.get_sources()[0].id
        self.repo.db.fill_similarity_cache(source_id=source_id, refresh=True)
        person = self.repo.get_persons()[0]
        self.repo.db.fill_similarity_cache(person=person, refresh=True)
        
    def test_workflow_identification(self):
        #we have three options in the identifaction process:
        #    1. identify the two
        #    2. anti-identify the two
        #    3. defer
        
        #set up an environmenet
        repo = self.create_filled_repository()
        self.repo.db.SIMILARITY_TRESHOLD = 0.0
        self.repo.db.fill_similarity_cache(minimal_score=0.0, refresh=True)
        
        #we now have original_length "most similar persons"
        original_length = len(self.repo.get_most_similar_persons())
            
        #get two similar persons
        score, p1, p2 = self.repo.get_most_similar_persons()[1]
        
        
        #we should also find them if we search for the peopele
        ls = self.repo.get_most_similar_persons(bioport_id=p1.bioport_id)
        assert (score, p1, p2) in ls
        #now we identify two people
        repo.identify(p1, p2)
        assert len(self.repo.get_most_similar_persons()) <= original_length-1
        score, p1, p2 = self.repo.get_most_similar_persons()[1] 
        repo.antiidentify(p1, p2)
        assert len(self.repo.get_most_similar_persons()) <=  original_length-2
        
        score, p1, p2 = self.repo.get_most_similar_persons()[1] 
        repo.defer_identification(p1, p2)
        ls = self.repo.get_most_similar_persons()
        assert len(ls) <= original_length-3
        self.assertEqual(len(self.repo.get_deferred()), 1)
        
        
        score, p1, p2 = self.repo.get_most_similar_persons()[1] 
        repo.defer_identification(p1, p2)
        self.assertEqual(len(self.repo.get_deferred()), 2)
        assert len(self.repo.get_most_similar_persons()) <=  original_length-4
       
        id1 = min(p1.bioport_id, p2.bioport_id)
        id2 = max(p1.bioport_id, p2.bioport_id)
        qry = repo.db.get_session().query(CacheSimilarityPersons)
        
        #(p1,p2) were deferred, but now we identify them after all
        repo.identify(p1, p2)
        
        #the deferred list contains now only 1 pair
        self.assertEqual(len(self.repo.get_deferred()), 1)

    def test_get_most_similar_persons(self):
        repo = self.create_filled_repository()
        self.repo.db.SIMILARITY_TRESHOLD = 0.0
        self.repo.db.fill_similarity_cache(minimal_score=0.0, refresh=True)
        score, p1, p2  = repo.get_most_similar_persons()[0]
        source_id = p1.get_biographies()[0].get_source().id
        self.assertEqual((score, p1, p2 ) , repo.get_most_similar_persons(source_id=source_id)[0])
        self.assertEqual((score, p1, p2 ) , repo.get_most_similar_persons(source_id2=source_id)[0])
        
    def xxx_test_merging_in_identification(self):
        #XXX this is a test for when merging while identifying has been activated (in Repository.identify)
        #when we identify two persons that have bioport biographies defined, they should merge
        p1 = self._add_person('Lucky')
        p2 = self._add_person('Pozzo')
        self.repo.get_bioport_biography(person=p1)
        self.repo.get_bioport_biography(person=p2)
        #check sanity
        assert p1.get_biographies(source_id='bioport')
        assert p2.get_biographies(source_id='bioport')
        new_p = self.repo.identify(p1, p2)
        
        self.assertEqual(len(new_p.get_biographies()), 3)
        p = self.repo.get_person(bioport_id=new_p.get_bioport_id())
        self.assertEqual(len(p.get_biographies()), 3)
#class RepositoryTestCase(CommonTestCase):

    def test_refreshing_of_identification_cache(self):
        #we have three options in the identifaction process:
        #    1. identify the two
        #    2. anti-identify the two
        #    3. defer
        repo = self.repo
        
        #set up the environmenet
        self.repo.db.SIMILARITY_TRESHOLD = 0.0
        self.repo.db.fill_similarity_cache(refresh=True)
        persons = self.repo.get_persons()
        similar_persons = self.repo.get_most_similar_persons()
        
        #We need at least 5  'most similar persons' for the tests below to work
        original_length= len(similar_persons)
        assert original_length >= 5, 'We need at least 5 "most similar persons" for the tests to work'
            
        #now identify two persons 
        score, p1, p2 = similar_persons[0] 
        new_p = repo.identify(p1, p2)
        old_bioport_id = p1.bioport_id == new_p.bioport_id and p2.bioport_id or p1.bioport_id
        new_bioport_id = new_p.bioport_id
        
        new_len = len(self.repo.get_most_similar_persons()) 
        
        #all information about similiarty of the old person (that has been identified) should be gone
        self.assertEqual(len(self.repo.get_most_similar_persons(bioport_id=old_bioport_id)), 0)
        
        assert new_len <= original_length  -4,  '%s - %s' % (len(self.repo.get_most_similar_persons()), original_length)
        
        #now refresh the cache, and make sure that everything remains as it was
        repo.db.fill_similarity_cache(refresh=True)
        
        #all information about similiarty of the old person (that has been identified) should be gone
        self.assertEqual(len(self.repo.get_most_similar_persons(bioport_id=old_bioport_id)), 0)
        self.assertEqual(len(self.repo.get_antiidentified()), 0)
        self.assertEqual(len(self.repo.get_identified()), 1)
        self.assertEqual(len(self.repo.get_deferred()), 0)
        self.assertEqual(len(self.repo.get_persons()), 9)
        self.assertEqual(len(self.repo.get_most_similar_persons(bioport_id=old_bioport_id)), 0)
        self.assertEqual(len(self.repo.get_most_similar_persons()), new_len)

        score, p1, p2 = self.repo.get_most_similar_persons()[1]
#        p1, p2 = persons[2], persons[3]
        repo.antiidentify(p1, p2)
        #self.debug_info()
        
        self.assertEqual(len(self.repo.get_antiidentified()), 1)
        self.assertEqual(len(self.repo.get_identified()), 1)
        self.assertEqual(len(self.repo.get_deferred()), 0)
        self.assertEqual(len(self.repo.get_persons()), 9)
        self.assertEqual(len(self.repo.get_most_similar_persons()),new_len-1) 
        
        #all these identifications should also be persistent after we refull the cache
        repo.db.fill_similarity_cache(refresh=True)
        #self.debug_info()
        self.assertEqual(len(self.repo.get_most_similar_persons()), new_len-1)        
        
        repo.db.fill_similarity_cache(refresh=True)
        new_len = len(self.repo.get_most_similar_persons())
        score, p1, p2 = self.repo.get_most_similar_persons()[1] 
        self.assertEqual(len(self.repo.get_deferred()), 0)
        id1 = p1.bioport_id
        id2 = p2.bioport_id
        repo.defer_identification(p1, p2)
        self.assertTrue(repo.db.is_deferred(id1, id2))
        #self.debug_info()
        self.assertEqual(len(self.repo.get_antiidentified()), 1)
        self.assertEqual(len(self.repo.get_identified()), 1)
        self.assertEqual(len(self.repo.get_deferred()), 1)
        self.assertEqual(len(self.repo.get_most_similar_persons()), new_len -1)        
        
        #all these identifications should also be persistent after we refull the cache
        repo.db.fill_similarity_cache(refresh=True)
        
        self.assertEqual(len(self.repo.get_most_similar_persons()), new_len-1)        
        
        for score, p1, p2 in self.repo.get_most_similar_persons()[3:]:
            #sanity check if we have not identified one of these people before (if so, it messes up the tests below)
            if (p1 not in self.repo.get_identified() and p2 not in self.repo.get_identified()):
                break
        repo.defer_identification(p1, p2)
        self.debug_info()
        self.assertEqual(len(self.repo.get_deferred()), 2)
        self.assertEqual(len(self.repo.get_identified()), 1)
        self.assertEqual(len(self.repo.get_antiidentified()), 1)
        self.assertEqual(len(self.repo.get_most_similar_persons()), new_len-2)
        
        #all these identifications should also be persistent after we refull the cache
        repo.db.fill_similarity_cache(refresh=True)
        self.assertEqual(len(self.repo.get_most_similar_persons()), new_len-2 )        
       
       
        #(p1,p2) were deferred, but now we identify them after all
        identifieds = self.repo.get_identified()
        self.assertEqual(len(identifieds), 1)
        person = repo.identify(p1, p2)
        self.assertEqual(len(self.repo.get_deferred()), 1)
        self.assertEqual(len(self.repo.get_identified()), 2)
        self.assertEqual(len(self.repo.get_antiidentified()), 1)
        
        #XXX if the next @#$%#$% test FAILS, it is because some obscure reaons in the ORDER of the "get_most_similar_persons"
        #(I THING)- try to run the test again...
        #XXX FIX the problem described above and resurrect the follwoing test
#        self.assertEqual(len(self.repo.get_most_similar_persons()), original_length-7)
        self.assertEqual(len(self.repo.get_persons()), 8)
        #the deferred list contains now only 1 pair
        
        #all these identifications should also be persistent after we refill the cache
        repo.db.fill_similarity_cache(refresh=True)
        #XXX THIS SHOULD NOT FAIL!! 
#        self.assertEqual(len(self.repo.get_most_similar_persons()), original_length-4)

    def debug_info(self):
        return
        try:
            for r in  self.repo.db.get_session().query(CacheSimilarityPersons).all():
                i = 0
                if r.bioport_id1 != r.bioport_id2:
                    i += 1
            for i in self.repo.get_most_similar_persons():
                pass
            for i in self.repo.get_deferred():
                pass
            for i in self.repo.get_identified():
                pass
            for i in self.repo.get_antiidentified():
                pass
        except UnicodeEncodeError, error:
            raise
               
    def test_identify(self):
        
        repo = self.repo
        #get two persons
        persons = repo.get_persons()
        self.assertEqual(len(persons), 10)
        person1 = persons[1]
        person2 = persons[2]
        bio1 = person1.get_biographies()[0]
        bio2 = person2.get_biographies()[0]
        id1 = person1.get_bioport_id() 
        id2 = person2.get_bioport_id()  
       
        assert id1 != id2
        #identify the two people
        person = repo.identify(person1, person2)
        
        #id1 is the 'old bioport id', id2 is the new one
        if person.get_bioport_id() == person1.get_bioport_id():
            id1, id2 = id2, id1
            
        #both identifiers are still in the system
        assert id1 in repo.get_bioport_ids(), repo.get_bioport_ids()
        assert id2 in repo.get_bioport_ids(), repo.get_bioport_ids()
       
        #but id1 now redirects to id2
        self.assertEqual(repo.redirects_to(id1), id2)
        
        #we now have 9 nstead of 10 persons
        self.assertEqual(len(repo.get_persons()), 9, [r.id for r in repo.get_persons()])
        #and the newly identified person has two biographies
        self.assertEqual(len(person.get_biographies()), 2)
        
        assert person in [person1, person2]
        
        #and we have a person with these two biographies attached
        bios = person.get_biographies()
        self.assertEqual(set([b.id for b in bios]), set([bio1.id, bio2.id]))
        
        #also, if we try to find the person with id1, we cannot find it anymore
        person1 = repo.get_person(bioport_id=id1)
        self.assertEqual(person1.bioport_id, id2)
        person2 = repo.get_person(bioport_id=id2)
        
        self.assertNotEqual(person2, None)

        assert len(person2.get_biographies()) == 2, person2.get_biographies()

    def test_identify_status_only_if_connected(self):        
        
        persons = self.repo.get_persons()
        self.assertEqual(len(persons), 10)
        person1 = persons[1]
        person2 = persons[2]
        id1 = person1.get_bioport_id() 
        id2 = person2.get_bioport_id()  
        assert id1 != id2
        person1.status = STATUS_ONLY_VISIBLE_IF_CONNECTED
        self.repo.save_person(person1)
        #identify the two people
        person = self.repo.identify(person1, person2)
        self.assertEqual(person.status,person2.status)
        self.assertEqual(self.repo.get_person(person.get_bioport_id()).status, person2.status)
    
    def test_identify_categories(self):
        """see what happens with categories if we identify two persons"""
        #get two persons
        persons = self.repo.get_persons()
        self.assertEqual(len(persons), 10)
        person1 = persons[1]
        person2 = persons[2]
#        bio1 = person1.get_biographies()[0]
#        bio2 = person2.get_biographies()[0]
        id1 = person1.get_bioport_id() 
        id2 = person2.get_bioport_id()  
     
        assert id1 != id2
       
        def get_category_ids(bio):
        #now the new person should have the combined categories
            cats = bio.get_states(type='category') 
            cats = [x.get('idno') for x in cats]
            return set(cats)
       
        bio = person1.get_bioport_biography()
        bio.set_category([1,2]) 
        self.repo.save_biography(bio, 'test')
        bio = person2.get_bioport_biography()
        bio.set_category([2,3]) 
        self.repo.save_biography(bio, 'test')
        
        #just make sure everything is ok in the repo
        person1 = self.repo.get_person(person1.get_bioport_id())
        person2 = self.repo.get_person(person2.get_bioport_id())
        self.assertEqual(get_category_ids(person1.get_bioport_biography()), set(['1','2']))
        self.assertEqual(get_category_ids(person2.get_bioport_biography()), set(['2','3']))
        
        #identify the two people
        person = self.repo.identify(person1, person2)
        
        #the new person should have the combined categories of the original
        self.assertEqual(get_category_ids(person.get_bioport_biography()), set(['1','2','3']))
       
 
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(RepositoryTestCase, 'test_'),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')    
