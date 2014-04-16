# encoding=utf8
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
from bioport_repository.person import Person
# from bioport_repository.source import Source
from bioport_repository.biography import Biography
from bioport_repository.db_definitions import STATUS_DONE, STATUS_FOREIGNER


class PersonTestCase(CommonTestCase):

    def test_person_init(self):
        p1 = Person('1234', repository=self.repo)
        p2 = Person('2345')
        self.assertNotEqual(p1.id, p2.id)

    def test_get_names(self):
        self.create_filled_repository(sources=1)
        p1 = self.repo.get_persons()[1]
        p2 = self.repo.get_persons()[2]
        names1 = p1.get_names()
        names2 = p2.get_names()
        n1 = len(names1)
        n2 = len(names2)
        assert names1 != names2, names1 + names2
        p = self.repo.identify(p1, p2)
        self.assertEqual(len(p.get_names()), n1 + n2)

    def test_memoization(self):
        p1 = self.repo.get_persons()[1]
        p1.get_merged_biography()
        p1.get_merged_biography()
        p1.get_merged_biography()
        p1.get_merged_biography()

    def test_person_initial_is_set(self):
        self.create_filled_repository(sources=1)
        p1 = self.repo.get_persons()[1]
        p2 = self.repo.get_persons()[2]
        expected_initial1 = p1.naam()[0].lower()
        expected_initial2 = p2.naam()[0].lower()
        self.assertEquals(p1.initial(), expected_initial1, 'wrong initial: %s' % p1.initial())
        self.assertEquals(p2.initial(), expected_initial2, 'wrong initial: %s' % p2.initial())
        
    def test_person_initial_is_set1(self):
        person = self._add_person(name='Zylophon')
        self.assertEquals(person.initial(), 'z', 'wrong initial: %s' % person.initial())
        person = self._add_person(name='Xenophon')
        self.assertEquals(person.initial(), 'x', 'wrong initial: %s' % person.initial())
        person = self._add_person(name=u'Äriél')
        self.assertEquals(person.initial(), u'ä', u'wrong initial: %s' % person.initial())

    def test_person_has_name_is_set(self):
        person = self._add_person(name='')
        self.assertEqual(person.has_name(), False, 'has_name should be false')
        person = self._add_person()
        self.assertEqual(person.has_name(), False, 'has_name should be false')
        person = self._add_person(name='Xenophon')
        self.assertEqual(person.has_name(), True, 'has_name should be true')

    def test_person_birthday_is_set(self):
        person = self._add_person(name='Saskia', geboortedatum='2010-01-06')
        self.assertEqual(person.birthday(), '0106', 'person.birthday() returns %s' % person.birthday())
        person = self._add_person(name='Unknown')
        self.assertEqual(person.birthday(), None, 'person.birthday() returns %s' % person.birthday())

    def test_person_deathday_is_set(self):
        person = self._add_person(name='Methusaleh', sterfdatum='2010-01-06')
        self.assertEqual(person.deathday(), '0106', 'person.deathday() returns %s' % person.deathday())
        person = self._add_person(name='Unknown')
        self.assertEqual(person.deathday(), None, 'person.deathday() returns %s' % person.deathday())

    def test_person_invisible_is_set(self):
        person = self._add_person(name='Saskia')
        person.record.status = STATUS_FOREIGNER
        person.save()
        self.assertEqual(person.is_invisible(), True, 'person should be invisible')
        person.record.status = STATUS_DONE
        person.save()
        self.assertEqual(person.is_invisible(), False, 'person should be visible')

    def test_person_orphan_is_set(self):
        person = self._add_person(name='Remi')
        self.assertEqual(person.is_orphan(), False)
        b = person.get_biographies()
        self.assertEqual(len(b),1)
        default_bio = b[0]
        self.assertNotEqual(default_bio.source_id, 'bioport')

        bio = Biography(id="bla", source_id=u"bioport",
                        repository=self.repo)
        person.add_biography(bio)
        person.save()
        self.assertEqual(person.is_orphan(), False)

        self.repo.delete_biography(default_bio)
        self.assertEqual(person.is_orphan(), True)

    def test_get_dates_for_overview(self):
        person = self._add_person(name='Estragon')
        bio = person.get_biographies()[0]
        bioport_id = person.get_bioport_id()
        date_birth = '1900'
        date_baptism = '1901'
        date_death = '1902'
        date_burial = '1903'

        bio._add_event(type='baptism', when=date_baptism)
        self._save_biography(bio)
        self.assertEqual(self.repo.get_person(bioport_id).get_dates_for_overview(), (date_baptism, None))

        bio.set_value('birth_date', date_birth)
        self._save_biography(bio)
        self.assertEqual(self.repo.get_person(bioport_id).get_dates_for_overview(), (date_birth, None))

        bio._add_event(type='burial', when=date_burial)
        self._save_biography(bio)
        self.assertEqual(self.repo.get_person(bioport_id).get_dates_for_overview(), (date_birth, date_burial))

        bio.set_value('death_date', date_death)
        self._save_biography(bio)
        self.assertEqual(self.repo.get_person(bioport_id).get_dates_for_overview(), (date_birth, date_death))


class InconsistentPersonsTestCase(CommonTestCase):

    x = 0

    def get_bio(self, bdate=None, ddate=None, bplace=None, dplace=None):
        self.x += 1
        bio = Biography(id=str(self.x), source_id=u"knaw",
                        repository=self.repo)
        bio.from_args(url_biografie='http://google.it',
                      naam_publisher='jelle',
                      url_publisher='http://gerbrandy.com',
                      naam="gino")
        if bdate is not None:
            bio.set_value('birth_date', bdate)
        if ddate is not None:
            bio.set_value('death_date', ddate)
        if bplace is not None:
            bio.set_value('birth_place', bplace)
        if dplace is not None:
            bio.set_value('death_place', dplace)
        self._save_biography(bio)
        return bio

    def test_no_contradictions_1(self):
        bio1 = self.get_bio(dplace='bar')
        bio2 = self.get_bio(dplace='bar')
        bio3 = self.get_bio(dplace='bar')
        person = bio1.get_person()
        person.add_biography(bio1)
        person.add_biography(bio2)
        person.add_biography(bio3)

        contrs = person.get_biography_contradictions()
        self.assertEqual(contrs, [])

    def test_no_contradictions_2(self):
        bio1 = self.get_bio(bplace='foo')
        bio2 = self.get_bio(bplace='foo')
        bio3 = self.get_bio(bplace='foo')
        person = bio1.get_person()
        person.add_biography(bio1)
        person.add_biography(bio2)
        person.add_biography(bio3)

        contrs = person.get_biography_contradictions()
        self.assertEqual(contrs, [])

    def test_places_contradictions_1(self):
        # death places
        bio1 = self.get_bio(dplace='bar')
        bio2 = self.get_bio(dplace='foo')
        bio3 = self.get_bio(dplace='foo')
        person = bio1.get_person()
        person.add_biography(bio1)
        person.add_biography(bio2)
        person.add_biography(bio3)

        cons = person.get_biography_contradictions()
        self.assertEqual(len(cons), 1)
        con = cons[0]
        con.values.sort(key=lambda x: x[0])
        self.assertEqual(con.values, [('bar', 'knaw'), ('foo', 'knaw')])
        self.assertEqual(con.type, 'death places')

    def test_places_contradictions_2(self):
        bio1 = self.get_bio(dplace='death1')
        bio2 = self.get_bio(dplace='death1')
        bio3 = self.get_bio(dplace='death2')
        bio4 = self.get_bio(bplace='birth1')
        bio5 = self.get_bio(bplace='birth1')
        bio6 = self.get_bio(bplace='birth1')
        bio7 = self.get_bio(bplace='birth2')
        bio8 = self.get_bio(bplace='birth3')
        person = bio1.get_person()
        for x in bio1, bio2, bio3, bio4, bio5, bio6, bio7, bio8:
            person.add_biography(x)
        cons = person.get_biography_contradictions()
        cons.sort(key=lambda x: x.type)

        self.assertEqual(len(cons), 2)
        birth_con = cons[0]
        self.assertEqual(set(birth_con.values), set([('birth1', 'knaw'),
                                            ('birth2', 'knaw'),
                                            ('birth3', 'knaw')])
                        )
        self.assertEqual(birth_con.type, 'birth places')

        death_con = cons[1]
        self.assertEqual(set(death_con.values), set([('death1', 'knaw'),
                                            ('death2', 'knaw')])
                        )
        self.assertEqual(death_con.type, 'death places')

    def test_birthdate_contradictions(self):
        # death places
        bio1 = self.get_bio(bdate='2010-10-10')
        bio2 = self.get_bio(bdate='2010-10-10')
        bio3 = self.get_bio(bdate='2010-11-10')
        person = bio1.get_person()
        person.add_biography(bio1)
        person.add_biography(bio2)
        person.add_biography(bio3)

        cons = person.get_biography_contradictions()
        self.assertEqual(len(cons), 1)
        con = cons[0]
        con.values.sort(key=lambda x: x[0])
        self.assertEqual(con.values, [('2010-10-10', 'knaw'),
                                      ('2010-11-10', 'knaw')])
        self.assertEqual(con.type, 'birth dates')

    def test_deathdate_contradictions(self):
        # death places
        bio1 = self.get_bio(ddate='2010-10-10')
        bio2 = self.get_bio(ddate='2010-10-10')
        bio3 = self.get_bio(ddate='2010-11-10')
        person = bio1.get_person()
        person.add_biography(bio1)
        person.add_biography(bio2)
        person.add_biography(bio3)

        cons = person.get_biography_contradictions()
        self.assertEqual(len(cons), 1)
        con = cons[0]
        con.values.sort(key=lambda x: x[0])
        self.assertEqual(con.values, [('2010-10-10', 'knaw'),
                                      ('2010-11-10', 'knaw')])
        self.assertEqual(con.type, 'death dates')

    def test_are_dates_different(self):
        # false
        pairs = [("1877-02-26", "bioport"),
                 ("1877", "bwn"), ]
        self.assertFalse(Person._are_dates_different(pairs))
        pairs = [("1877-02", "bioport"),
                 ("1877", "bwn"), ]
        self.assertFalse(Person._are_dates_different(pairs))
        pairs = [("1877-02-26", "bioport"),
                 ("1877-02-26", "foo"),
                 ("1877", "bwn"),
                 ("1877", "bar"), ]
        self.assertFalse(Person._are_dates_different(pairs))

        # true
        pairs = [("1877-02-26", "bioport"),
                 ("1877-02-27", "bioport"),
                 ("1877", "bwn"), ]

        self.assertTrue(Person._are_dates_different(pairs))
        pairs = [("1877-02-26", "bioport"),
                 ("1877-02-26", "bioport"),
                 ("1876", "bwn"), ]
        self.assertTrue(Person._are_dates_different(pairs))


def test_suite():
    test_suite = unittest.TestSuite()
    tests = [PersonTestCase,
             InconsistentPersonsTestCase,
             ]
    for test in tests:
        test_suite.addTest(unittest.makeSuite(test))
    return test_suite

if __name__ == "__main__":
    unittest.TextTestRunner(verbosity=2).run(test_suite())

