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
from bioport_repository.db import Source, BiographyRecord, PersonRecord, SourceRecord, Biography, RelBioPortIdBiographyRecord, Person
from bioport_repository.db_definitions import RelPersonCategory, PersonSoundex, \
    RELIGION_VALUES, STATUS_NOBIOS, PersonSource
from bioport_repository.common import format_date , to_date, BioPortException, BioPortNotFoundError


class DBRepositoryTestCase(CommonTestCase):

    def test_basics(self):
        db = self.db

        assert 'biography' in db.engine.table_names()
        assert 'naam' in db.engine.table_names()
        assert 'soundex' in db.engine.table_names(), db.engine.table_names()

    def test_manipulate_source(self):
        #nbase is the amount of sources in the database
        nbase = self.db.get_session().query(SourceRecord).count()
        src = Source(id='123')
        self.db.add_source(src)
        self.assertEqual(len(self.db.get_session().query(SourceRecord).all()), nbase + 1)
        self.assertEqual(len(self.db.get_sources()), nbase + 1)
        self.db.delete_source(src)
        self.assertEqual(len(self.db.get_sources()), nbase)
        #now add the source again, to check if the previous result did not reamin cached
        self.db.add_source(src)
        self.assertEqual(len(self.db.get_sources()), nbase + 1)



    def test_manipulate_biographies(self):
        """tests for adding and deleting biographies"""
        n_bios = n_base = self.db.count_biographies()

#        n_base_naam = self.db.get_session().query(NaamRecord).count()
#        n_base_soundex = self.db.get_session().query(SoundexRecord).count()
        n_base_soundex = self.db.get_session().query(PersonSoundex).count()
        self.assertEqual(len(self.db.get_session().query(BiographyRecord).all()), n_base)
        src = Source(id='123')
        self.repo.save_source(src)

        bio1 = Biography(id='ladida', source_id=src.id, repository=self.repo)
        bio1.from_args(naam_publisher="1", url_biografie="http://www.url.com/1", url_publisher="http:///url2.com", naam="jantje")

        self.db.save_biography(bio1, user=self.db.user, comment='test')

        #we have added one new biography, with one name that corresponds to one single soundex
        n_bios += 1
        self.assertEqual(self.db.count_biographies(), n_bios)
        self.assertEqual(len(self.db.get_session().query(BiographyRecord).all()), n_bios)
        self.assertEqual(len(self.db.get_session().query(PersonSoundex).all()), n_base_soundex + 1)

        #this biography has one oauthor
        bio1.set_value('auteur', ['Johan'])
        self.db.save_biography(bio1, user=self.db.user, comment='test')
        #now we have a new version of this biography
        self.assertEqual(len(self.db.get_session().query(BiographyRecord).all()), n_bios + 1)
        #but the number of biographies (with version 0) is still the ssame
        self.assertEqual(len(list(self.db.get_biographies())), n_bios)

        self.assertEqual(len(bio1.get_value('auteur', [])), 1, bio1.to_string())

        bio2 = Biography(id='ladida2', source_id=src.id, repository=self.repo)
        bio2.from_args(naam_publisher="1", url_biografie="http://www.url.com/1", url_publisher="http:///url2.com", naam="jantje")
        self.db.save_biography(bio2, user=self.db.user, comment='test')
        #we added one more biography
        n_bios += 1
        self.assertEqual(len(list(self.db.get_biographies())), n_bios)

    def test_save_biography(self):
        #set up a source
        src = Source(id='123')
        self.repo.save_source(src)
        bio1 = Biography(id='id1', source_id=src.id, repository=self.repo)
        bio1.from_args(naam_publisher="1", url_biografie="http://www.url.com/1", url_publisher="http:///url1.com", naam="name1", text='text1')
        self.db.save_biography(bio1, user=self.db.user, comment='test')
        bio1.from_args(naam_publisher="1", url_biografie="http://www.url.com/1", url_publisher="http:///url1.com", naam="name1", text='text2')
        self.db.save_biography(bio1, user=self.db.user, comment='test')

        bio = self.db.get_biography(local_id=bio1.id)

        #basic sanity check
        self.assertEqual(bio.snippet(), 'text2')

        person = self.db.get_person(bio1.get_bioport_id())

        self.db.update_person(person.bioport_id)
        person = self.db.get_person(bio1.get_bioport_id())

        self.assertEqual(person.snippet(), 'text2')

    def test_source_updating(self):
        src = self.repo.get_source(id=u'knaw')
        self.db.delete_biographies(src)
        self.assertEqual(len(list(self.db.get_biographies(source=src))), 0)

        self.repo.download_biographies(src)
        self.assertEqual(len(list(self.db.get_biographies(source=src))), 5)

    def test_update_persons(self):
        self.repo.db.update_persons()

    def test_add_person(self):

        #this is what we want to do

        #add a source
        source_id = u'bioport_test'
#        bioport_id = self.db.fresh_identifier()
        name = 'name, test'
        source = Source(source_id, repository=self.repo)
        source.save()
        #add a biography
        args = {
            'naam_publisher':'x',
            'url_biografie': 'http://placeholder.com',
            'url_publisher': 'http://placeholder.com',
            'name':name,
#            'bioport_id':bioport_id,    
            'local_id':'1'
            }

        biography = Biography(repository=self.repo, source_id=source_id)
        biography.from_args(**args)
        #now at this point, the biography does not have a bioport_id yet
        self.assertEqual(biography.get_bioport_id(), None)
        biography.save(user='test')

        #this biography should be connected with the source
        self.assertEqual(biography.get_source(), source)

        #the biography has a local_id defined
        self.assertEqual(biography.create_id(), 'bioport_test/1')
        #the biography should be in the repository
        bioport_id = biography.get_bioport_id()
        assert bioport_id

        #is our biography available in the repository?
        self.assertEqual(self.repo.get_biography(biography.create_id()), biography)
        self.assertEqual(self.repo.get_biographies(bioport_id=bioport_id), [biography])


#        #now we check if we have added a corresponding person
#        qry = self.repo.db.get_session().query(PersonRecord).filter(PersonRecord.bioport_id==bioport_id)
#        assert qry.all(), qry.statement
#        self.assertEqual(len(qry.all()), 1)
#        self.assertEqual(qry.one().naam, name)
#        qry = self.repo.db.get_session().query(PersonSource).filter(PersonSource.bioport_id==bioport_id)
#        assert qry.all(), qry.statement
##        qry = self.repo.db._get_persons_query(full_records=True, hide_invisible=False)

        person = biography.get_person()
        self.assertTrue(person.bioport_id, bioport_id)
        self.assertEqual(person.record.naam, name)
        person1 = self.db.get_person(bioport_id)
        self.assertEqual(person1, person)


#        bioport_id = self.db.fresh_identifier()
        bioport_id = self.db.fresh_identifier()
        #we cannot add a person without a biography
        self.assertRaises(BioPortException, self.db.add_person, bioport_id)

        #so we first create a biography
        defaults = {
            'naam_publisher':'x',
            'url_biografie': 'http://placeholder.com',
            'url_publisher': 'http://placeholder.com',
            'name':name,
            'bioport_id':bioport_id,
            }


        other_source_id = 'this does not exist'
        biography = Biography(repository=self.repo, source_id=other_source_id)
        biography.from_args(**defaults)
        #now, saving this biography should raise an exception, because no source was found
        self.assertRaises(Exception, biography.save, 'test')

    def test_update_soundexes(self):
        self.repo.db.update_soundexes()

    def test_saving_of_categories(self):
        repo = self.repo
        #get some person from the database

        p = repo.get_persons()[1]
        #set some properties here and there
        categories = [1, 2, 3]
        bio = p.get_bioport_biography()
        bio.set_category(categories)

        #save the changes in the repository
        self._save_biography(bio)

        #sanity checks: see if the person knows about this
        self.assertEqual(len(bio.get_states(type='category')), len(categories))
        self.assertEqual(len(p.get_bioport_biography().get_states(type='category')), len(categories))
        self.assertEqual(len(p.get_merged_biography().get_states(type='category')), len(categories))


        #do we have these categories in the database
        self.assertEqual(repo.db.get_session().query(RelPersonCategory).filter(RelPersonCategory.bioport_id == p.get_bioport_id()).count(), len(categories))
        #now try to find the person again, and see if the changes hold (and are in the db)

        new_p = repo.get_person(p.get_bioport_id())
        self.assertEqual(len(new_p.get_merged_biography().get_states(type='category')), len(categories))
        self.assertTrue(p in repo.get_persons(category=categories[0]))

    def test_religion(self):
        repo = self.repo
        #get some person from the database

        bio1 = repo.get_persons()[1].get_bioport_biography()
        bio2 = repo.get_persons()[2].get_bioport_biography()
        #set some properties here and there
        rel_id = unicode(RELIGION_VALUES[2][0])

        bio1.set_religion(rel_id)
        self._save_biography(bio1)
        self.assertEqual(bio1.get_religion().get('idno'), rel_id)
        self.assertEqual(bio1.get_person().get_merged_biography().get_religion().get('idno'), rel_id)
        self.assertEqual(len(repo.get_persons(religion=rel_id)), 1)
        bio2.set_religion(rel_id)
        self._save_biography(bio2)
        self.assertEqual(len(repo.get_persons(religion=rel_id)), 2)
        bio2.set_religion(None)
        self._save_biography(bio2)
        self.assertEqual(bio2.get_religion(), None)
        self.assertEqual(len(repo.get_persons(religion=rel_id)), 1)


    def test_get_persons(self):
        repo = self.repo
        #check sanity
        self.assertEqual(len(repo.get_persons()), 10)

        #identify  two persons so we have more interesting queries
        repo.identify(repo.get_persons(source_id=u'knaw')[0], repo.get_persons(source_id=u'knaw2')[-1])

        self.assertEqual(len(repo.get_persons()), 9)

        self.assertEqual(len(repo.get_persons(source_id=u'knaw2')), 5)
        self.assertEqual(len(repo.get_persons(source_id2=u'knaw2')), 5)
        self.assertEqual(len(repo.get_persons(source_id=u'knaw', source_id2=u'knaw2')), 1)
        self.assertEqual(len(repo.get_persons(is_identified=True)), 1)
        self.assertEqual(len(repo.get_persons(category=1)), 1)

        self.assertEqual(len(repo.get_persons(search_name='jan')), 2)
        self.assertEqual(len(repo.get_persons(search_term='molloy')), 1)
        self.assertEqual(len(repo.get_persons(has_illustrations=True)), 2)
        self.assertEqual(len(repo.get_persons(has_illustrations=False)), 7)
        self.assertEqual(len(repo.get_persons(geboortejaar_min='1778')), 7)
        self.assertEqual(len(repo.get_persons(geboortejaar_max='1777')), 2)
        self.assertEqual(len(repo.get_persons(geboortejaar_min='1778', geboortejaar_max='1778')), 1)

        self.assertEqual(len(repo.get_persons(sterfjaar_min='1858')), 7)
        self.assertEqual(len(repo.get_persons(sterfjaar_max='1857')), 2)
        self.assertEqual(len(repo.get_persons(sterfjaar_min='1858', sterfjaar_max='1858')), 1)
        self.assertEqual(len(repo.get_persons(search_name=u'molloyx')), 1)
        self.assertEqual(len(repo.get_persons(search_name=u'"molloyx"')), 1)

        self.assertEqual(len(repo.get_persons(geboorteplaats='Amsterdam')), 3)
        self.assertEqual(len(repo.get_persons(geboorteplaats='Am*')), 3)
        self.assertEqual(len(repo.get_persons(sterfplaats='*en')), 3)

    def test_get_bioport_id(self):
        repo = self.repo
        some_person = repo.get_persons()[1]
        url_biography = some_person.get_biographies()[0].get_value('url_biography')
        self.assertEqual(repo.get_bioport_id(url_biography=url_biography), some_person.bioport_id)
        self.assertEqual(repo.get_bioport_id(url_biography='this_bio_does_not_exist'), None)



    def test_search_soundex(self):
        repo = self.repo

        self.assertEqual(len(repo.get_persons(search_name=u'boschma')), 9, self.repo.get_persons())
        self.assertEqual(len(repo.get_persons(search_name=u'molloyx')), 1)
        self.assertEqual(len(repo.get_persons(search_name=u'bosma')), 9) #, self.repo.get_persons())
        self.assertEqual(len(repo.get_persons(search_name='bo?ma')), 9)
        self.assertEqual(len(repo.get_persons(search_name=u'"mollo??"')), 1)
        self.assertEqual(len(repo.get_persons(search_name=u'"mollo*"')), 1)
        self.assertEqual(len(repo.get_persons(search_name=u'hilbrand')), 9)

        self.assertEqual(len(repo.get_persons(search_family_name_only=True, search_name=u'hilbrand')), 0)
        self.assertEqual(len(repo.get_persons(search_family_name_only=True, search_name=u'bosma')), 9)

    def test_search_intrapositions(self):
        #if we search for family name only, also words like 'van' and 'van der' and such should be included
        repo = self.repo
        self.assertEqual(len(repo.get_persons(search_name=u'van')), 1)
        self.assertEqual(len(repo.get_persons(search_family_name_only=True, search_name=u'van')), 1)

    def test_search_exact_name(self):
        repo = self.repo

        self.assertEqual(len(repo.get_persons(search_name=u'"hilbrand"')), 9)
        self.assertEqual(len(repo.get_persons(search_name=u'"boschma"')), 9)
        self.assertEqual(len(repo.get_persons(search_name=u'"molloyx"')), 1)
        self.assertEqual(len(repo.get_persons(search_family_name_only=True, search_name=u'"hilbrand"')), 0)
        self.assertEqual(len(repo.get_persons(search_family_name_only=True, search_name=u'"boschma"')), 9)

    def test_complex_geboorte_date_get_persons_full(self):
        self.create_filled_repository()
        repo = self.repo
        qry = dict(geboortejaar_min=1888, geboortemaand_min=6, geboortedag_min=1)
        qry.update(dict(geboortejaar_max=1893, geboortemaand_max=3, geboortedag_max=1))
        self.assertEqual(len(repo.get_persons(**qry)), 1)
        del(qry['geboortedag_min'], qry['geboortedag_max'])
        self.assertEqual(len(repo.get_persons(**qry)), 1)

    def test_complex_levend_date_get_persons_full(self):
        self.create_filled_repository()
        repo = self.repo
        qry = dict(levendjaar_min=1778, levendmaand_min=1, levenddag_min=12)
        qry.update(dict(levendjaar_max=1778, levendmaand_max=2, levenddag_max=21))
        self.assertEqual(len(repo.get_persons(**qry)), 2)
        qry.update(dict(levendjaar_min=1770, levendjaar_max=1770))
        self.assertEqual(len(repo.get_persons(**qry)), 1)

        qry = dict(levendjaar_min=1700, levendmaand_min=1, levenddag_min=12)
        qry.update(dict(levendjaar_max=1800, levendmaand_max=2, levenddag_max=21))
        self.assertEqual(len(repo.get_persons(**qry)), 4)

        #februari!
        qry = dict(levendjaar_max=1800, levendmaand_max=2)
        self.assertEqual(len(repo.get_persons(**qry)), 4)

    def test_complex_geboorte_date_get_persons_partial(self):
        self.create_filled_repository()
        repo = self.repo
        qry = dict(geboortemaand_min="1", geboortedag_min="1")
        qry.update(dict(geboortemaand_max="2", geboortedag_max="1"))
        self.assertEqual(len(repo.get_persons(**qry)), 3)
        qry.update(dict(geboortemaand_max="1", geboortedag_max="10"))
        self.assertEqual(len(repo.get_persons(**qry)), 2)

    def test_complex_sterf_date_get_persons_full(self):
        self.create_filled_repository()
        repo = self.repo
        qry = dict(sterfjaar_min=1904, sterfmaand_min=6, sterfdag_min="1")
        qry.update(dict(sterfjaar_max=1965, sterfmaand_max="5", sterfdag_max="20"))
        self.assertEqual(len(repo.get_persons(**qry)), 2)
        qry['sterfmaand_max'] = '11'
        self.assertEqual(len(repo.get_persons(**qry)), 3)

    def test_complex_sterf_date_get_persons_partial(self):
        self.create_filled_repository()
        repo = self.repo
        qry = dict(
            sterfmaand_min="1",
            sterfdag_min="10",
            sterfmaand_max="2",
            sterfdag_max="20",
            )
        self.assertEqual(len(repo.get_persons(**qry)), 2)
        qry['sterfdag_max'] = '25'
        self.assertEqual(len(repo.get_persons(**qry)), 3)

    def test_trans_year_boundary_sterf_date_get_persons(self):
        self.create_filled_repository()
        repo = self.repo
        qry = dict(sterfmaand_min="11", sterfdag_min="20")
        qry.update(dict(sterfmaand_max="1", sterfdag_max="20"))
        self.assertEqual(len(repo.get_persons(**qry)), 2)
        qry['sterfdag_max'] = '31'
        self.assertEqual(len(repo.get_persons(**qry)), 3)
        #Let's check that a date with the year only is not returned
        self.db.get_session().execute(
            "UPDATE person set sterfdatum_min ='1882-01-01', sterfdatum_max='1882-12-31'"
            " WHERE sterfdatum_min ='1882-01-15'")
        self.assertEqual(len(repo.get_persons(**qry)), 2)
    def test_hide_invisible(self):
        self.create_filled_repository()
        repo = self.repo
        person = repo.get_persons()[1]
        self.assertEqual(len(repo.get_persons()), 10)
        person.record.status = STATUS_NOBIOS
        repo.save_person(person)
        self.assertEqual(len(repo.get_persons(hide_invisible=True)), 9)
        self.assertEqual(len(repo.get_persons(hide_invisible=False)), 10)

    def test_get_all_places(self):
        self.create_filled_repository()
        db = self.db
        all_places = db.get_places()
        expected_all_places = [u"'s Gravenhage", u'Ameide', u'Amsterdam', u'Brussel, Belgi\xeb', u'De Bilt', u'Down, Groot Brittani\xeb', u'Driebergen', u'Gent, Belgi\xeb', u'IJsbrechtum', u'Leiden', u'Lisse', u'Newham, Groot Brittani\xeb', u'Paesens, Frankrijk', u'Tilburg']
        self.assertEqual(all_places, expected_all_places)
        sterf_places = db.get_places('sterf')
        expected_sterf_places = [u"'s Gravenhage", u'Amsterdam', u'De Bilt', u'Driebergen', u'Gent, Belgi\xeb', u'Leiden', u'Lisse', u'Newham, Groot Brittani\xeb']
        self.assertEqual(sterf_places, expected_sterf_places)
        geboorte_places = self.repo.get_places('geboorte')
        expected_geboorte_places = [u'Ameide', u'Amsterdam', u'Brussel, Belgi\xeb', u'Down, Groot Brittani\xeb', u'Gent, Belgi\xeb', u'IJsbrechtum', u'Paesens, Frankrijk', u'Tilburg']
        self.assertEqual(geboorte_places, expected_geboorte_places)

    def test_delete_biographies(self):
        """check if we clean up after ourselves when deleting biographies"""
        session = self.repo.db.get_session()

        #just check some general sanity
        #we have 10 biographies in two sources, 5 bios each
        self.assertEqual(session.query(BiographyRecord).count(), 10)
        self.assertEqual(len(self.repo.get_sources()), 3)
        _bioportsource, source1, source2 = self.repo.get_sources()
        self.assertEqual(len(self.repo.get_persons()), 10)
        self.assertEqual(len(self.repo.get_persons(source_id=source1.id)), 5)
        self.assertEqual(len(self.repo.get_persons(source_id=source2.id)), 5)

        #we identify two persons from source1 and source2
        self.repo.identify(
           self.repo.get_persons(source_id=source1.id)[0],
           self.repo.get_persons(source_id=source2.id)[0],
           )
        #and we now have 9 persons, but still 5 from each
        self.assertEqual(len(self.repo.get_persons()), 9)
        self.assertEqual(len(self.repo.get_persons(source_id=source1.id)), 5)
        self.assertEqual(len(self.repo.get_persons(source_id=source2.id)), 5)

        #we delete the biographies for one source
        self.repo.delete_biographies(source1)

        #the sources are still there
        self.assertEqual(len(self.repo.get_sources()), 3)
        #and also the bioport_ids we used
        self.assertEqual(len(self.repo.get_bioport_ids()), 10)

        #there are now only 5 persons left
        self.assertEqual(session.query(PersonRecord).count(), 5)
        self.assertEqual(len(self.repo.get_persons()), 5)

        #and we should have no persons associated with source1 anymore
        self.assertEqual(list(self.repo.get_persons(source_id=source1.id)), [])

        #however, we still should remember with which bioport_ids our biogrpahies were associated
        self.assertEqual(session.query(RelBioPortIdBiographyRecord).count(), 10)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DBRepositoryTestCase, 'test_'),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
