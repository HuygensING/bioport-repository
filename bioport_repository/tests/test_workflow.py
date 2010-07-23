from bioport_repository.tests.common_testcase import CommonTestCase, unittest 
from bioport_repository.repository import *
from bioport_repository.source import Source


THIS_DIR = os.path.split(os.path.abspath(__file__))[0]


class WorkflowTestCase(CommonTestCase):

    _fill_repository = False

    def test_workflow(self):
        #a test where we run trhough the whole workflow 
        #of downloading, identifyying, adding and editing descriptions, combining information
        
        repository = self.repo 

        self.repo.db._update_category_table()
        
        #------------------------ 
        #download data from a source
        #------------------------ 
#        import pdb;pdb.set_trace()
        url = 'file://%s' % os.path.join(THIS_DIR, 'data/knaw/list.xml')
        source = Source(id=u'test', url=url , description=u'test', repository=repository)
        
        repository.add_source(source)
        repository.download_biographies(source)
        
        url = 'file://%s' % os.path.join(THIS_DIR, 'data/knaw2/list.xml')
        source = Source(id=u'knaw2', url=url , description=u'test', repository=repository)
        repository.add_source(source)
        repository.download_biographies(source)
        
        #inspect the sources
        repository.get_sources(order_by='quality', desc=True)
        
        self.assertEqual(len(repository.get_biographies()), 10)
        self.assertEqual(len(repository.get_persons()), 10)
        #------------------------ 
        #identify two biographies
        #------------------------ 
        
        #get two biographies
        
        #get a biography
        person1 = repository.get_persons()[1]
        bio1 = person1.get_biographies()[0]
        #find names that are similar
        repository.db.fill_similarity_cache(minimal_score=0.0)
        similar_persons = repository.get_most_similar_persons(bioport_id=person1.bioport_id)
        score, p1, p2 = similar_persons[0]
        person2 = (person1 == p1 and p2) or (person1 == p2 and p1)
        bio2 = person2.get_biographies()[-1]
        id1 = person1.get_bioport_id()
        id2 = person2.get_bioport_id()
        
        self.assertNotEqual(id1 ,id2)
        
        
        #for more identification workflow, see test_repository.RepositoryTestCase.test_workflow_identification
        
        person = repository.identify(person1, person2)
        if person.get_bioport_id() == person2.get_bioport_id():
            id1, id2 = id2, id1
        #sometimes we know that people are not identifical - and we tell it to the system so it doesnt suggest them to us

        person3 = repository.get_persons()[-1]
        person4 = repository.get_persons()[-2]
        #so this means we have a person with these two biographies attached
        bios = person.get_biographies()
        self.assertEqual(set([b.id for b in bios]), set([bio1.id, bio2.id]))
        
        #now the old bioport_id redirets to the new one
        assert id2 in repository.get_bioport_ids()
        self.assertEqual(repository.redirects_to(id2), id1)
        
        #it also means that we (still) have 10 biographies
        self.assertEqual(len(repository.get_biographies()), 10) 
        #but now we have 9 persons
        self.assertEqual(len(repository.get_persons()), 9, repository.get_persons())
        
         
        #find the 5 most similar personname-pairs
        repository.db.fill_similarity_cache(minimal_score=0.0)
        ls = repository.get_most_similar_persons() 
        ls = [p for p in ls]
        _nr_similarity = len(ls)
        #get the score, and two persons
        score, p1, p2 = ls[0]

        repository.antiidentify(p1, p2)
#        ls = repository.get_most_similar_persons() 
        ls =  list(ls)
        
#        self.assertEqual(len(ls), _nr_similarity-1, '%s - %s - %s' % (len(ls), _nr_similarity-1,  ls))
        score, p1, p2 = ls[0]
        
        #identifiy the persons
        repository.identify(p1, p2)
        
        #in the end, we commit our changes
        #repository.commit()
        
        #------------------------ 
        #add a new biodes document for a person
        #------------------------ 
        person = repository.get_persons()[3]
        bio = repository.get_bioport_biography(person)
        #
        self.assertEqual(bio.get_bioport_id(), person.get_bioport_id())
        
        #so now this is a biography of this person
        assert bio.id in [bio.id for bio in person.get_biographies()]
        
        #edit it
        #try to extract the gelsachtsnaam from the text
        s = bio.guess_value('geboortedatum')
        bio.set_value(geboortedatum=s)
        bio.set_category([1,2,3])
        person.status = 3 
        #save your edited bioportsource
        repository.save_biography(bio)
        repository.save_person(person)
        #show show metedata to the editor
        bio.last_commit()         
        bio.last_commit_by()
       
        
        
        #-----------------------------
        # PRESENtATION
        #-----------------------
        
        #do some queries
        repository.get_persons(beginletter='a')
        repository.get_persons(search_term='A*')
        #------------------------ 
        # combine the biographies
        #------------------------ 
        bio = person.get_merged_biography()
        
if __name__ == "__main__":
    unittest.main()
