from bioport_repository.tests.common_testcase import CommonTestCase, unittest
from bioport_repository.merged_biography import MergedBiography, BiographyMerger
from lxml import etree
from datetime import datetime


class TestMergedBiography(CommonTestCase):

    def test_biography(self):
        repo = self.repo
        # get an existing biography
        bios = repo.get_biographies()
        bios = list(bios)[1:4]
        merged = MergedBiography(bios)
        bios = merged.get_biographies()
        ls = []
        for bio in bios:
            ls += bio.get_names()
        assert ls
        self.assertEqual(len(merged.get_names()), len(ls))
        self.assertEqual(set([n.to_string() for n in merged.get_names()]), set([n.to_string() for n in ls]))

        # check if the default value works
        self.assertEqual(len(merged.get_illustrations(default=['123'])), 1)

        for bio in bios:
            bio.set_value('geboortedatum', '')
            self.assertEqual(bio.get_value('geboortedatum'), None)
        self.assertEqual(merged.get_value('geboortedatum'), None)
        # if dates are consistent with each other, they "add up"
        bios[-1].set_value('geboortedatum', '2000')
        self.assertEqual(merged.get_value('geboortedatum'), '2000')
        bios[-2].set_value('geboortedatum', '2000-02')
        self.assertEqual(merged.get_value('geboortedatum'), '2000-02')
        bios[-3].set_value('geboortedatum', '2000-02-01')
        self.assertEqual(merged.get_value('geboortedatum'), '2000-02-01')
        self.assertEqual(merged.geboortedatum(), '2000-02-01')
        bios[-3].add_or_update_event(type='birth', when='', date_text='ongeveer')  # , notBefore=notBefore, notAfter=notAfter, place=place)

        self.assertEqual(merged.geboortedatum(), 'ongeveer', etree.tostring(merged.get_event('birth')))  # @UndefinedVariable

        # test if all relevaent information ends up in the "merged biodes" file
        bios[-3].set_value('geboortedatum', '2000-02-01')

        doc = merged.to_xml()
        self.assertEqual(doc.get_value('geboortedatum'), '2000-02-01', doc.to_string())
        self.assertEqual(doc.get_value('birth_date'), '2000-02-01')

    def test_to_json(self):
        repo = self.repo
        # get an existing biography
        bios = repo.get_biographies()
        bios = list(bios)[1:4]
        merged = MergedBiography(bios)
        merged.to_dict()

    def test_min_max_dates(self):
        bio1 = self._create_biography(naam='Lucky', birth_date='1900', death_date='1970')
        m_bio = MergedBiography([bio1])

        # we gave
        wanted = (
            datetime(1900, 1, 1),
            datetime(1900, 12, 31),
            datetime(1970, 1, 1),
            datetime(1970, 12, 31),
            )
        self.assertEqual(m_bio._get_min_max_dates(), wanted)

        bio = self._create_biography(naam='Pozzo')
        bio._add_event(type='baptism', when='1910-01-02')
        m_bio = MergedBiography([bio])

        wanted = (
            datetime(1900, 1, 2),  # at most 10 years before baptism
            datetime(1910, 1, 2),  # birth_date_max on the day of baptism
            datetime(1920, 1, 2),  # death_date at least 20 years after date_min
            datetime(2010, 1, 2),  # lived not more than 100 years
            )
        self.assertEqual(m_bio._get_min_max_dates(), wanted)

        # test with only a date of death
        bio = self._create_biography(naam='Vladimir')
        bio._add_event(type='death', when='1980-03')
        m_bio = MergedBiography([bio])

        wanted = (
            datetime(1880, 3, 1),  # min birth 100 years before min death
            datetime(1960, 3, 31),  # max birth 20 years before max death
            datetime(1980, 3, 1),
            datetime(1980, 3, 31),
            )
        self.assertEqual(m_bio._get_min_max_dates(), wanted)

        # test with only a range of date of death
        bio = self._create_biography(naam='Vladimir')
        bio._add_event(type='death', notBefore='1980-03', notAfter='1990')
        m_bio = MergedBiography([bio])

        wanted = (
            datetime(1880, 3, 1),  # min birth 100 years before min death
            datetime(1970, 12, 31),  # max birth 20 years before max death
            datetime(1980, 3, 1),
            datetime(1990, 12, 31),
            )
        self.assertEqual(m_bio._get_min_max_dates(), wanted)


class TestBiographyMerger(CommonTestCase):
    def test_sanity(self):
        bio1 = self._create_biography(naam='Mercier', birth_date='2000-01-01')
        bio2 = self._create_biography(naam='Mercier', death_date='2001-01-01')

        m_bio = BiographyMerger.merge_biographies(bio1, bio2)
        self.assertEqual(m_bio.get_value('name'), bio1.get_value('name'))
        self.assertEqual(m_bio.get_value('birth_date'), '2000-01-01')
        self.assertEqual(m_bio.get_value('death_date'), '2001-01-01')
        self.assertEqual(len(m_bio.get_names()), 1)
        bio3 = self._create_biography(naam='Camier')
        bio3.set_category([1, 2])
        bio3.add_or_update_event(type='birth', when='2000-01-01', place='Dublin')

        m_bio = BiographyMerger.merge_biographies(m_bio, bio3)
        self.assertEqual(len(m_bio.get_states(type='category')), 2)

        bio4 = self._create_biography(naam='Camier')
        bio4.set_category([2, 3])
        bio4.add_or_update_event(type='birth', notBefore='1900-01-01', text="I'm glad to see you back. I thought you were gone forever")

        m_bio = BiographyMerger.merge_biographies(bio3, bio4)

        # the merged biography should have 3 categories (1,2 from bio3, and 3, 4 from bio4
        self.assertEqual(len(m_bio.get_states(type='category')), 3)

        event_birth = m_bio.get_event(type='birth')
        self.assertEqual(event_birth.get('when'), '2000-01-01')

        # bio5 has a different birth date from bio3, and so should not be mergable
        bio5 = self._create_biography(naam='Camier')
        bio5.set_category([2, 3])
        bio5.add_or_update_event(type='birth', when='1900-01-01')
        m_bio = BiographyMerger.merge_biographies(bio3, bio5)
#        self.assertEqual(m_bio, [bio3, bio5])

        bio6 = self._create_biography(naam='Camier')
        bio6.add_or_update_event(type='birth', when='1900')
        m_bio = BiographyMerger.merge_biographies(bio6, bio5)
        self.assertEqual(m_bio.get_value('birth_date'), '1900-01-01')

        bio5.add_figure(uri='http://1.com', text='2')
        bio6.add_figure(uri='http://3.com', text='4')
        m_bio = BiographyMerger.merge_biographies(bio6, bio5)
        self.assertTrue(m_bio is not None)
        self.assertEqual(set(m_bio.get_figures_data()), set([('http://3.com', '4'), ('http://1.com', '2')]))


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestMergedBiography),
        unittest.makeSuite(TestBiographyMerger),
        ))


if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
