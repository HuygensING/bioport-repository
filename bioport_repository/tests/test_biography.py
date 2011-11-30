# encoding=utf8
from bioport_repository.tests.common_testcase import CommonTestCase, unittest 
from bioport_repository.biography import Biography
from bioport_repository.source import Source
from bioport_repository.db_definitions import * #@UnusedWildImport


class BiographyTestCase(CommonTestCase):

    def test_biography(self):
        self.create_filled_repository()
        repo = self.repo
        
        #get an existing biography
        bio = list(repo.get_biographies())[5]
        
        #get the information of this biography
        #this biography has no identifier yet
        assert bio.get_bioport_id()
        #but it has lost of other properties (inherited from BioDesDoc?)
        
        
        #create a new biography e
        source = Source(id='bioport_test')
        repo.save_source(source)        
        #make a new biography
        bio = Biography( id = 'bioport_test/test_bio', source_id=source.id)
        
        self.assertEqual(bio.id, 'bioport_test/test_bio')
        
        bio.from_args( 
              url_biografie='http://ladida/didum', 
              naam_publisher='nogeensiets', 
              url_publisher='http://pbulihser_url',
              naam='Tiedel Doodle Dum',
              )
        
        #save it
        self._save_biography(bio)
        
        #the new biography now also has a bioport_id
        assert bio.get_bioport_id()
        self.assertEqual(bio.title(), 'Tiedel Doodle Dum')
       
        p = bio.get_person() 
        self.assertEqual(bio.get_bioport_id(), p.get_bioport_id())
        
        bio.set_value('geboortedatum', '2009-01-01')
        bio.set_value('geboortedatum', '2009-01-02')
        self.assertEqual(bio.get_value('geboortedatum'), '2009-01-02')
        
        bio.set_value('geboortedatum', '2009-01-02')
        bio.set_value('geboorteplaats', 'nog een test')
        self.assertEqual(bio.get_value('geboortedatum'), '2009-01-02')
        bio.set_value('sterfdatum', '2010-01-02')
        bio.set_value('sterfplaats', 'nog een test')
        self.assertEqual(bio.get_value('sterfdatum'), '2010-01-02')
        bio.set_value('sterfdatum', '')
        self.assertEqual(bio.get_value('sterfdatum'), None)
    
    def test_add_or_update_event(self):
        """check if the person record is updated with changhes in birth or death events in a biography"""
        person = self.repo.get_persons()[1]
        bio = person.get_biographies()[0]
        bio.add_or_update_event(type='birth', when='1234')

    def test_ids(self):
        bio = Biography(id='YYY/x', source_id='sourceY')
        self.assertEqual(bio.id, 'YYY/x')
        bio = Biography(id='z', source_id='sourceY')
        self.assertEqual(bio.id, 'z')
        
    def test_from_string(self):
        self.create_filled_repository(sources=1)
        bio = list(self.repo.get_biographies())[3]
        bio.set_value('geboortedatum', '2000-11-11')
        self._save_biography(bio)
        ls = self.repo.get_biographies(local_id=bio.id, version=None)
        ls = list(ls)
        self.assertEqual(len(ls), 2) #there are two versions of this biography
        bio2 = ls[0]
        self.assertEqual(bio2.get_value('geboortedatum'), '2000-11-11')

    def test_from_source(self): 
        self.create_filled_repository()
        repo = self.repo
        bio = repo.get_biography(local_id='knaw/005')
        self.assertEqual(bio.get_names()[0].to_string(), '<persName>Arien A</persName>')
    
    def test_clean_snippet(self): 
        self.create_filled_repository()
        repo = self.repo
        bio = repo.get_biography(local_id='knaw/005')
        snippet = bio.snippet()
        #USELESS_TEXT is in between <style> tags and therefore should be ignored by the snippet
        self.assertFalse('USELESS_TEXT' in snippet)
    
    def test_get_set_snippet(self):
        #make a new biography
        bio = list(self.repo.get_biographies())[5]
        
        self._save_biography(bio)
        snippet_molloy = """I took advantage of being at the seaside to lay in a store of
sucking-stones. They were pebbles but I call them stones. Yes, on
this occasion I laid in a considerable store. I distributed them
equally between my four pockets, and sucked them turn and turn
about. """
        bio.set_snippet(source_id='molloy', snippet=snippet_molloy)
        
        snippet_malone = u"""I simply believe that I can say nothing that is not true, I mean that has not happened, it's not the same thing but no matter. """
        bio.set_snippet(source_id='malone', snippet=snippet_malone)
        
        self.assertEqual(bio.get_snippet('malone'), snippet_malone)
        self.assertEqual(bio.get_snippet('molloy'), snippet_molloy)
        
        
    def test_snippet(self):
        s = """<?xml version="1.0" encoding="UTF-8"?>
<!--2011-05-18 11:26:12-->
<biodes version="1.0">
  <fileDesc>
    <author>Nationaal Archief</author>
    <ref target="http://proxy.handle.net/10648/cd48fc47-2b91-42f6-bb63-c2de770135b1"/>
    <date when="1920"/>
    <publisher>
      <name>Nationaal Archief</name>
      <ref target="http://www.gahetna.nl/collectie/archief"/>
    </publisher>
  </fileDesc>
  <person>
    <persName>Jan Daniël Cornelis Carel Willem de Constant Rebecque</persName>
  </person>
  <biography>
    <text>
      <title>Inventaris van het archief van De Constant Rebecque</title>
      <span></span>
    </text>
  </biography>
</biodes>
	    """
        bio = Biography().from_string(s)
        self.assertEqual(bio.snippet(1000), 'Inventaris van het archief van De Constant Rebecque')
        
        s = """<biodes version="1.0">
  <fileDesc>
    <author>Nationaal Archief</author>
    <ref target="http://proxy.handle.net/10648/cd48fc47-2b91-42f6-bb63-c2de770135b1"/>
    <date when="1920"/>
    <publisher>
      <name>Nationaal Archief</name>
      <ref target="http://www.gahetna.nl/collectie/archief"/>
    </publisher>
  </fileDesc>
  <person>
    <persName>Jan Daniël Cornelis Carel Willem de Constant Rebecque</persName>
  </person>
  <biography>
  </biography>
</biodes>
        """
        bio = Biography().from_string(s)
        self.assertEqual(bio.snippet(), '')
        
        source = Source(id='bioport_test')
        self.repo.save_source(source)        
        #make a new biography
        bio = Biography( id = 'bioport_test/test_bio', source_id=source.id)
        
        self.assertEqual(bio.id, 'bioport_test/test_bio')
        #XXX Do we need this?
        bio.from_args( 
              url_biografie='http://ladida/didum', 
              naam_publisher='nogeensiets', 
              url_publisher='http://pbulihser_url',
              naam='Tiedel Doodle Dum',
              tekst="""Lemuel is in charge, he raises his hatchet on which the blood will never dry, but not to hit anyone, he will not hit anyone, he will not hit anyone any more, he will not touch anyone any more, either with it or with it or with it or with or

or with it or with his hammer or with his stick or with his fist or in thought in dream I mean never he will never
or with his pencil or with his stick or

or light light I mean

never there he will never

never anything

there

any more""",
              )
        self.assertEqual(bio.snippet(size=20), 'Lemuel is in...')

        bio.set_value('text', 'abc')
        self.assertEqual(bio.snippet(), 'abc')

        bio.set_value('text', 'ca. 1800-1900')
        self.assertEqual(bio.snippet(), 'ca. 1800-1900')

        
    def test_get_illustrations(self):      
        bio = self.repo.get_biography(local_id='knaw/001')
        self.assertEqual(len(bio.get_illustrations()), 4)

        bio = self.repo.get_biography(local_id='knaw/003')
        
        self.assertEqual(len(bio.get_illustrations()), 1, bio.source_url)
        self.assertEqual(len( bio.get_value('illustraties')), 1)
        
    def test_set_categories(self):
        bio = list(self.repo.get_biographies())[3]
        bio.set_category(1)
        self.assertEqual(len(bio.get_states(type='category')), 1)
        bio.set_category([1])
        self.assertEqual(len(bio.get_states(type='category')), 1)
        self.assertEqual(bio.get_states(type='category')[0].get('idno'), '1')
        bio.set_category([1,2])
        self.assertEqual(len(bio.get_states(type='category')), 2)
        bio.set_category([2])
        self.assertEqual(len(bio.get_states(type='category')), 1)
        bio.set_category([2,0])
        self.assertEqual(len(bio.get_states(type='category')), 1)
        self.assertEqual(bio.get_states(type='category')[0].get('idno'), '2')
        bio.set_category([2,2, 2, '2'])
        self.assertEqual(len(bio.get_states(type='category')), 1)
        self.assertEqual(bio.get_states(type='category')[0].get('idno'), '2')

 
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(BiographyTestCase, 'test'),
        ))


if __name__=='__main__':
    unittest.main(defaultTest='test_suite')


