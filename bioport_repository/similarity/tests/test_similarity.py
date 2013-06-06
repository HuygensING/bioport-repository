import os
import pickle

from common import CommonTestCase, unittest
from bioport_repository.similarity.similarity import Similarity
#from bioport_repository.person import Person
from bioport_repository.db_definitions import CacheSimilarityPersons


class SimilarityTestCase(CommonTestCase):
    
    def setUp(self):
        CommonTestCase.setUp(self)
        self.sim = Similarity()
        self.similarity_score = self.sim.similarity_score
    
    def test_sanity(self):
        persons = self.repo.get_persons()
        sim = Similarity(persons[1], persons)
        sim.compute()
        sim.sort()

    def assert_similarity_order(self, ls):
        def _format_person(p):
            return '%s (%s-%s)' % (p.get_names(), p.get_value('birth_date'), p.get_value('death_date'))
        sims = [(self.similarity_score(p1, p2), p1, p2) for p1, p2 in ls]
        for i, score in enumerate(sims):
            if i > 1:
                self.assertTrue(sims[i-1][0] >= sims[i][0], 'Expected %s, %s [%s] to be more similar than %s and %s [%s]' % (
                            _format_person(sims[i-1][1]), _format_person(sims[i-1][2]), sims[i-1][0],
                            _format_person(sims[i][1]), _format_person(sims[i][2]), sims[i][0]
                            ))
            
    def test_similarity(self):
        p1 = self._add_person('Jan', geboortedatum='1000', sterfdatum='2000')
        p2 = self._add_person('Jan', geboortedatum='1000', sterfdatum='2000')
        p3 = self._add_person('Piet Jan')
        p4 = self._add_person('Piet', geboortedatum='1000', sterfdatum='2000')
        p5 = self._add_person('Jan', geboortedatum='1001', sterfdatum='2000')
        self.assertEqual(self.similarity_score(p1, p2), 1)
        self.assertTrue(0 < self.similarity_score(p1, p3)< 1)
        self.assertTrue(self.similarity_score(p1, p4) < 1.0)
        self.assertTrue(self.similarity_score(p1, p5) < 1.0)
    
    def test_similarity_with_dates(self):
        p1 = self._add_person('Lucky', geboortedatum='1000', sterfdatum='2000')
        p2 = self._add_person('Lucky', geboortedatum='', sterfdatum='2000')
        p3 = self._add_person('Lucky', geboortedatum='1000', sterfdatum='')
        p4 = self._add_person('Lucky', geboortedatum='', sterfdatum='')
        self.assert_similarity_order([
          (p1, p1),
          (p1, p2),
          (p1, p3),
          (p1, p4),
        ]) 
        p2 = self._add_person('Lucky', geboortedatum='1001', sterfdatum='2000')
        p3 = self._add_person('Lucky', geboortedatum='1900', sterfdatum='2000')
       
        self.assert_similarity_order([
          (p1, p1),
          (p1, p2),
          (p1, p3),
        ]) 
        
        p1 = self._add_person('Lucky, Pozzo Vladimir Estragon', geboortedatum='1000', sterfdatum='2000')
        p2 = self._add_person('Luckie, Pozzo Vladimir Estragon', geboortedatum='1000', sterfdatum='2000')
        p3 = self._add_person('Lucky, Pozzo Vladimir Estragon', geboortedatum='', sterfdatum='')
        p4 = self._add_person('Luckie, Pozzo Vladimir Estragon', geboortedatum='', sterfdatum='')
        score1 = Similarity.similarity_score(p1, p2) #@UndefinedVariable
        score2 = Similarity.ratio(p1.get_names()[0], p2.get_names()[0])
        #given the fact that they have the same birth and death dates, the scores of p1 and p2 shoudl imporve wrt the "bare" names
        self.assertTrue(score1 > score2)
        self.assert_similarity_order([
          (p1, p1),
          (p1, p2),
          (p1, p3),
          (p1, p4),
        ])
        
        
    def test_surely_equal(self):
        p0 = self._add_person('Estragon', geboortedatum='1000', sterfdatum='2000')
        p1 = self._add_person('Estragon', geboortedatum='1000', sterfdatum='2000')
        p2 = self._add_person('Estragon', geboortedatum='1001', sterfdatum='2000')
        p3 = self._add_person('Estragon', geboortedatum='1000-12-12', sterfdatum='2000')
        p4 = self._add_person('Estragon', geboortedatum='1000', sterfdatum='2001')
        p5 = self._add_person('Vladimir', geboortedatum='1000', sterfdatum='2000')
        p6 = self._add_person('Estragon', geboortedatum='1000', sterfdatum='')
        p7 = self._add_person('Mercier Camier', geboortedatum='1000', sterfdatum='1200')
        p8 = self._add_person('Camier, Mercier', geboortedatum='1000', sterfdatum='1200')
        p9 = self._add_person('Dongen, Kees van', geboortedatum='1000', sterfdatum='1200')
        p10 = self._add_person('Kees van Dongen', geboortedatum='1000', sterfdatum='1200')
        p11 = self._add_person(names=['Kees van Dongen', 'Cornelius van Dongen'], geboortedatum='1000', sterfdatum='1200')
        p12 = self._add_person('Mercier', geboortedatum='1000', sterfdatum='1200')
        bio = self._create_biography(name='Dongen, Kees van')
        p12.save_biography(bio)
        self.save_biography(bio, comment='test')
        self.assertTrue(Similarity.are_surely_equal( p0, p1)) #@UndefinedVariable
        self.assertFalse(Similarity.are_surely_equal(p0, p2)) #@UndefinedVariable)
        self.assertTrue(Similarity.are_surely_equal(p0, p3)) #@UndefinedVariable)
        self.assertFalse(Similarity.are_surely_equal(p0, p4) )#@UndefinedVariable)
        self.assertFalse(Similarity.are_surely_equal(p0, p5) )#@UndefinedVariable)
        self.assertFalse(Similarity.are_surely_equal(p0, p6) )#@UndefinedVariable)
        self.assertTrue(Similarity.are_surely_equal(p7, p8) )#@UndefinedVariable)
        self.assertTrue(Similarity.are_surely_equal(p9, p10)) #@UndefinedVariable)
        self.assertTrue(Similarity.are_surely_equal(p9, p11)) #@UndefinedVariable)
        self.assertTrue(Similarity.are_surely_equal(p9, p12)) #@UndefinedVariable)
        self.assertTrue(Similarity.are_surely_equal(p10, p12)) #@UndefinedVariable)
    
    def test_with_biodes_files(self):
        s1 = """<biodes version="1.0.1">
  <fileDesc>
    <title/>
    <ref target="http://www.rkd.nl/rkddb/dispatcher.aspx?action=search&amp;database=ChoiceArtists&amp;search=priref=19815"/>
    <publisher>
      <name>Rijksbureau voor Kunsthistorische Documentatie</name>
      <ref target="http://www.rkd.nl/"/>
    </publisher>
  </fileDesc>
  <person>
    <persName>Dam, Max van</persName>
    <event type="birth" when="1910-03-19">
      <place>Winterswijk</place>
    </event>
    <event type="death" when="1943-09-20">
      <place>S&#243;bibor (Polen)</place>
    </event>
    <state type="occupation">schilder</state>
    <state type="occupation">tekenaar</state>
    <idno type="id">19815</idno>
  </person>
  <biography>
    <text>Schilder, tekenaar. Geboren: 19 maart 1910, Winterswijk. Gestorven: 20 september 1943, S&#243;bibor (Polen). </text>
  </biography>
</biodes>"""

        s2 = """    
<biodes version="1.0.1">
  <fileDesc>
    <title/>
    <publisher/>
  </fileDesc>
  <person>
    <idno type="id">50019330</idno>
  <persName>Max van Dam</persName><event type="birth" when="1910-03-19"><place>Winterswijk</place></event><event type="death" when="1943-09-20"><place>Sobibor, Polen</place></event><event type="funeral"><place/></event><event type="baptism"><place/></event><sex value="1"/><state type="category" idno="8">Maatschappelijke bewegingen</state><state type="floruit" from="" to=""><place/></state></person>
  <biography><snippet source_id="jews/109.xml"/></biography>
</biodes>"""
        p1 = self._add_person(xml_source=s1)
        p2 = self._add_person(xml_source=s2)
        self.assertTrue(Similarity.are_surely_equal(p1, p2)) #@UndefinedVariable
        
    def _read_testsets(self): 
        fn_identified =  os.path.join(os.path.dirname(__file__), 'data', 'identified_examples.pickle')
        self._identified = []
        for bio1, bio2 in pickle.load(open(fn_identified)):
            self._identified.append((bio1, bio2))
            
    def test_most_similar_persons(self):
        repo = self.repo
        self.assertEqual(len(self.repo.get_persons()) ,10)
        self.repo.db.fill_similarity_cache(minimal_score=0.0, refresh=True)
        for r in self.repo.db.get_session().query(CacheSimilarityPersons).all():
            assert r.bioport_id1 <= r.bioport_id2, (r.bioport_id1, r.bioport_id2)
        
        ls = self.repo.get_most_similar_persons(size=3) 
        ls = list(ls)
        self.assertEqual(len(ls) ,3)
        score, p1, p2  = ls[0]
        self.assertNotEqual(p1.get_bioport_id(), p2.get_bioport_id())
        
        ls = self.repo.get_most_similar_persons(bioport_id=p1.bioport_id)
        for score, pa, pb in ls:
            assert p1.bioport_id in [pa.bioport_id, pb.bioport_id]
        ls = self.repo.get_most_similar_persons(source_id=self.repo.get_sources()[0].id)
        ls = self.repo.get_most_similar_persons(search_name='jan')

def test_suite():
    test_suite = unittest.TestSuite()
    tests = [SimilarityTestCase]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test))
    return test_suite
 
if __name__ == "__main__":
    unittest.main() #defaultTest='SimilarityTestCase.test_cases_to_optimize')
