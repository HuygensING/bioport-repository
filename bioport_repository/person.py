#!/usr/bin/env python

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

import os

from sqlalchemy.orm.exc import NoResultFound, DetachedInstanceError
from lxml import etree

from bioport_repository.merged_biography import MergedBiography, BiographyMerger
from bioport_repository.db_definitions import STATUS_NEW
from bioport_repository.common import format_date, to_date
from bioport_repository.db_definitions import (
    RelPersonCategory,
    RelPersonReligion,
    PersonRecord,
    PersonSource,
    STATUS_FOREIGNER,
    STATUS_MESSY,
    STATUS_REFERENCE,
    STATUS_NOBIOS,
    STATUS_ONLY_VISIBLE_IF_CONNECTED,
    STATUS_ALIVE
    )

TO_HIDE = [
   STATUS_FOREIGNER,
   STATUS_MESSY,
   STATUS_REFERENCE,
   STATUS_NOBIOS,
   STATUS_ALIVE,
   STATUS_ONLY_VISIBLE_IF_CONNECTED,
   ]


class Person(object):
    """A Person is an object that is identified with a bioport identifier.
    A Person is usually associated with one or more Biography objects.
    """

    def __init__(self,
        bioport_id,
        biographies=None,  # XXX - this is not used!
        repository=None,
        record=None,
#        status=None,
        remarks=None,
        score=None,
        ):
        """
        Arguments:
            bioport_id - a unique identifier for this person
                bioport_id is MANDATORY because persons are by definitiion identified
            biographies - a list of Biography instances
            repository - a Repository instance
            record - an instance of PersonRecord
            status - an integer
            remarks - a string
        """

        self.id = self.bioport_id = bioport_id
        self.repository = repository
        self._record = record
#        self._status = status
        self.remarks = remarks
        if record is not None:
#            self.status = record.status
            self.remarks = record.remarks
        self.score = score

    def __eq__(self, other):
        if type(other) == type(self) and other.bioport_id == self.bioport_id:
            return True
        return False

    def singleton_id(self, id, **args):
        # XXX - what is this?
        return self.id

    def __str__(self):
        if self.get_names():
            return '<Person %s with id %s>' % (self.get_names()[0], self.id)
        else:
            return '<Person with id %s>' % (self.id)

    __repr__ = __str__

    @property
    def status(self):
        return self.record.status or STATUS_NEW

    @property
    def record(self):
        try:
            if self._record:
                try:
                    self._record.naam
                except DetachedInstanceError:
                    raise AttributeError  # reload the record
            else:
                raise AttributeError
        except AttributeError:
            with self.repository.db.get_session_context() as session:
                try:
                    r = session.query(PersonRecord).filter(PersonRecord.bioport_id == self.get_bioport_id()).one()
                except NoResultFound:
                    r = PersonRecord(bioport_id=self.get_bioport_id())
                    session.add(r)
                self._record = r

        return self._record

    def _fresh_record(self):
        """return a fresh record from the db"""
        del self._record
        return self.record

    def save(self):
        with self.repository.db.get_session_context() as session:
            r_person = self.record
            bioport_id = self.get_bioport_id()
            # XXX: is this obsolete?
            if getattr(self, 'remarks', None) is not None:
                r_person.remarks = self.remarks
            if getattr(self, 'status', None):
                r_person.status = self.status

            # check if a person with this bioportid alreay exists
            merged_biography = self.get_merged_biography()
            computed_values = self.computed_values
            r_person.naam = computed_values.naam
            r_person.sort_key = computed_values.sort_key
            r_person.has_illustrations = computed_values.has_illustrations
            r_person.search_source = computed_values.search_source
            r_person.sex = computed_values.sex
            r_person.geboortedatum_min = computed_values.geboortedatum_min
            r_person.geboortedatum_max = computed_values.geboortedatum_max
            r_person.sterfdatum_min = computed_values.sterfdatum_min
            r_person.sterfdatum_max = computed_values.sterfdatum_max
            r_person.geboortedatum = computed_values.geboortedatum
            r_person.sterfdatum = computed_values.sterfdatum
            r_person.geboorteplaats = computed_values.geboorteplaats
            r_person.sterfplaats = computed_values.sterfplaats
            r_person.names = computed_values.names
            r_person.snippet = computed_values.snippet
            r_person.has_contradictions = computed_values.has_contradictions
            r_person.thumbnail = computed_values.thumbnail
            # # BB
            #     has_name = Column(Boolean) # if naam != null && != ''
            r_person.has_name = (r_person.naam != None) and (r_person.naam != '') 
            
            #     birthday = Column(MSString(4), index=True) # if geboortedatum_min = geboortedatum_max, then extract geboortedag
            if r_person.geboortedatum_min != None and r_person.geboortedatum_min == r_person.geboortedatum_max:
#                 print 'r_person.geboortedatum_min=%s' % r_person.geboortedatum_min
                date = to_date(r_person.geboortedatum_min[0:10])
#                 print 'date = %s' % date
                iso = date.isoformat()
                r_person.birthday = iso[5:7] + iso[8:10]
#                 print 'birthday = %s' % r_person.birthday

            if r_person.sterfdatum_min != None and r_person.sterfdatum_min == r_person.sterfdatum_max:
                date = to_date(r_person.sterfdatum_min[0:10])
#                 print 'date = %s' % date
                iso = date.isoformat()
                r_person.deathday = iso[5:7] + iso[8:10]

            #     initial = Column(MSString(1), index=True) # eerste letter van naam
            if r_person.has_name:
                r_person.initial = r_person.naam[0].lower()
            #     invisible = Column(Boolean) # person.status IN (11, 5, 9, 9999, 14, 15)
            r_person.invisible = r_person.status in TO_HIDE
#             #     foreigner = Column(Boolean) # person.status IN (11)
#             r_person.foreigner = r_person.status == STATUS_FOREIGNER
            #     orphan = Column(Boolean) # person is orphan when the only sources linking to it is 'bioport'
            """ TODO: test this"""
            sources = self.get_sources()
            r_person.orphan = len(sources) == 1 and sources[0].id == 'bioport' 
              
            # # /BB
            # update categories
            session.query(RelPersonCategory).filter(RelPersonCategory.bioport_id == bioport_id).delete()

            done=[] 
            for category in merged_biography.get_states(type='category'):
                category_id = category.get('idno')
                assert type(category_id) in [type(u''), type('')], category_id
                try:
                    category_id = int(category_id)
                except ValueError:
                    msg = '%s- %s: %s' % (category_id, etree.tostring(category), self.bioport_id)
                    raise Exception(msg)
                if category_id not in done:
                    r = RelPersonCategory(bioport_id=bioport_id, category_id=category_id)
                    done.append(category_id)
                    session.add(r)
                    session.flush()

            # update the religion table
            religion = merged_biography.get_religion()
            religion_qry = session.query(RelPersonReligion).filter(RelPersonReligion.bioport_id == bioport_id)
            if religion is not None:
                religion_id = religion.get('idno')
                if religion_id:
                    try:
                        r = religion_qry.one()
                        r.religion_id = religion_id
                    except  NoResultFound:
                        r = RelPersonReligion(bioport_id=bioport_id, religion_id=religion_id)
                        session.add(r)
                    session.flush()
            else:
                religion_qry.delete()
                session.flush()

            # 'the' source -- we take the first non-bioport source as 'the' source
            # and we use it only for filtering later
            # XXX what is this used for???
            src = [s for s in merged_biography.get_biographies() if s.source_id != 'bioport']
            if src:
                src = src[0].source_id
            else:
                src = None

            # refresh the names
            self.repository.db.delete_names(bioport_id=bioport_id)
            self.repository.db.update_name(bioport_id=bioport_id, names=computed_values._names)

            self._update_source()

            if self.get_biography_contradictions():
                r_person.has_contradictions = True
            else:
                r_person.has_contradictions = False

            msg = 'Changed person'
            self.repository.db.log(msg, r_person)

        # XXX: these next two lines somehow guarantee that something does not break - find out why, what, and remove them
        with self.repository.db.get_session_context() as session:
            session.merge(self.record)

        self.repository.db._all_persons[self.bioport_id] = self

    def add_biography(self, biography, comment=None):
        biography.set_value('bioport_id', self.get_bioport_id())
        if not comment:
            comment = 'added biography to %s' % self

        biography.save(user=self.repository.user, comment=comment)

    def get_biographies(self, source_id=None):
        """Return all Biographies instances that are known to be
        of this person.

        We order the results in some way (any way) that is determinate
        """
        ls = self.repository.get_biographies(
            bioport_id=self.get_bioport_id(),
            order_by='quality',
            source_id=source_id,
            version=0,
            )

        return ls

    @property
    def has_illustrations(self):
        if self.record:
            return self.record.has_illustrations
        else:
            return self.computed_values.has_illustrations

    def get_bioport_id(self):
        return self.bioport_id

    def get_sources(self):
        return [bio.get_source() for bio in self.get_biographies()]

    def get_quality(self):
        return max([bio.get_quality() for bio in self.get_biographies()])

    def get_value(self, k, default=None):
        return self.get_merged_biography().get_value(k, default)

    def get_merged_biography(self):
        """
        Return a Biography that represents the 'cascaded information'
        contained in the biographies of this person.
        """
        return MergedBiography(self.get_biographies())

    def get_bioport_biography(self, create_if_not_exists=True):
        # convenience mthod
        return  self.repository.get_bioport_biography(self, create_if_not_exists=create_if_not_exists)

    def get_names(self):
        return self.get_merged_biography().get_names()

    def title(self):
        if self.record:
            return self.record.naam
        return self.get_merged_biography().title()

    def name(self):
        if self.record:
            return self.record.naam
        else:
            return self.get_merged_biography().naam()

    naam = name

    def initial(self):
        if self.record:
            return self.record.initial
        else:
            return self.get_merged_biography().initial()

    def is_invisible(self):
        if self.record:
            return self.record.invisible
        else:
            return self.get_merged_biography().is_invisible()

    def has_name(self):
        if self.record:
            return self.record.has_name
        else:
            return self.get_merged_biography().has_name()

    def is_orphan(self):
        # Not literally: the meaning of orphan here is that the only source available
        # for this person is a bioport biography
        if self.record:
            return self.record.orphan
        else:
            return self.get_merged_biography().is_orphan()

    def birthday(self):
        if self.record:
            return self.record.birthday
        else:
            return self.get_merged_biography().birthday()

    def deathday(self):
        if self.record:
            return self.record.deathday
        else:
            return self.get_merged_biography().deathday()

    def redirects_to(self):
        """
        Does this bioport_id redirect somewhere else? if yes, return
        that id, if not, return self.bioport_id.
        """
        return self.repository.redirects_to(self.get_bioport_id())

    def search_source(self):
        if self.record:
            return self.record.search_source
        else:
            return self.computed_values.search_source

    def snippet(self, term=None):
        """
        Ask a snippet to each biography, and return the first we can find.
        """
        if self.record:
            return self.record.snippet
        else:
            return self.computed_values.snippet

    def get_comments(self):
        return self.repository.db.get_comments(bioport_id=self.id)

    def add_comment(self, **kwargs):
        kwargs['bioport_id'] = self.id
        return self.repository.db.add_comment(bioport_id=self.id, values=kwargs)

    def geboortedatum(self):
        if self.record:
            return self.record.geboortedatum
        else:
            return self.computed_values.geboortedatum

    def sterfdatum(self):
        if self.record:
            return self.record.sterfdatum
        else:
            return self.computed_values.sterfdatum

#        event = self.get_merged_biography().get_event('death')
#        if event is not None:
#            return event.get('when')
#        if self.record.sterfdatum_min == self.record.sterfdatum_max:
#            return self.record.sterfdatum_max

    def get_dates_for_overview(self):
        """return a tuple of ISO-dates to show in the overview

        the first data is the date of birth, but if that does not exist, it is date of baptism
        the second date is the date of death, or, if that does not exist, date of burial

        TODO: why is the baptism-burial part commented out?
        """
        date1 = self.geboortedatum()
#        if not date1:
#            event = self.get_merged_biography().get_event('baptism')
#            if event is not None:
#                date1 = event.get('when')
#
        date2 = self.sterfdatum()
#        if not date2:
#            event = self.get_merged_biography().get_event('burial')
#            if event is not None:
#                date2 = event.get('when')
        return date1, date2

    def names(self):
        return self.record.names

    def thumbnail(self):
        url = self.record.thumbnail
        if not url:
            return url
        elif url.startswith('http:'):
            return url
        else:
            images_cache_url = self.repository.images_cache_url
            return '%s/%s' % (images_cache_url, self.record.thumbnail)

    def geslachtsnaam(self):
        return self.record.geslachtsnaam

    @classmethod
    def _are_dates_equal(cls, date1, date2):
        """return True if the two dates are 'equal'

        arguments:
            date1, date2 are strings in ISO-xxxxx format.
        """
        # "1980-09-10" and "1980" are equal
        # "1980-09" and "1980" are equal
        # "1980-09-10" and "1980-09-12" are not

        x, y = date1, date2
        lenx = len(x)
        leny = len(y)
        # "1980-09-10" and "1980" are equal
        if lenx == 4 or leny == 4:
            return x.startswith(y[:4])
        # "1980-09" and "1980" are equal
        elif lenx == 7 or leny == 7:
            return x.startswith(y[:7])
        # "1980-09-10" and "1980-09-12" are not
        else:
            return x == y

    @classmethod
    def _are_dates_different(cls, pairs):
        dates = set([x[0] for x in pairs])
        for tocheck, _source in pairs:
            for d in dates:
                if not cls._are_dates_equal(tocheck, d):
                    return True
        return False

    def update(self):
        # XXX you should call "save" and not "update"
        return self.save()

    def _update_source(self):
        """update the table person_source and replace the source_ids to the bioport_id"""
        bioport_id = self.bioport_id

        # BB sometimes there's duplication in source_ids, should this be possible?
        # BB anyway, put it in a set to remove duplication
        source_ids = frozenset([b.source_id for b in self.get_biographies()])
#         print source_ids
        
        with self.repository.db.get_session_context() as session:
            # delete existing references
            session.query(PersonSource).filter(PersonSource.bioport_id == bioport_id).delete()
            for source_id in source_ids:
#                 print bioport_id,source_id
                r = PersonSource(bioport_id=bioport_id, source_id=source_id)
                session.add(r)

    def get_biography_contradictions(self):
        """Iterates over all biographies and checks birth dates and
        places for contradictions (e.g. one bio states "x" while
        another one states "y").
        Return a list of Contradiction instances or [].
        """
        retlist = []
        bdates, ddates, bplaces, dplaces = [], [], [], []
        for bio in self.get_biographies():
            source = str(bio.get_source().id)
            x = bio.get_value('birth_date')
            if x is not None and not (x, source) in bdates:
                bdates.append((x, source))
            x = bio.get_value('death_date')
            if x is not None and not (x, source) in ddates:
                ddates.append((x, source))
            x = bio.get_value('birth_place')
            if x is not None and not (x, source) in bplaces:
                bplaces.append((x, source))
            x = bio.get_value('death_place')
            if x is not None and not (x, source) in dplaces:
                dplaces.append((x, source))

        x = set(x[0] for x in bplaces)
        if len(x) > 1:
            retlist.append(Contradiction("birth places", bplaces))
        x = set(x[0] for x in dplaces)
        if len(x) > 1:
            retlist.append(Contradiction("death places", dplaces))
        x = set(x[0] for x in bdates)
        if len(x) > 1:
            if self._are_dates_different(bdates):
                retlist.append(Contradiction("birth dates", bdates))
        x = set(x[0] for x in ddates)
        if len(x) > 1:
            if self._are_dates_different(ddates):
                retlist.append(Contradiction("death dates", ddates))

        return retlist

    def merge_bioport_biographies(self):
        """merge the bioport biographies of this person

        if the bios are not mergeable (they may have different data), don't change anything
        otherwise, add the merged biography, and remove all the old ones
        """
        bios = self.get_biographies(source_id='bioport')
        if not bios:
            return
        elif type(bios) != type([]):
            return bios
        elif len(bios) < 2:
            return bios
        merged_bio = BiographyMerger.merge_biographies(bios)
        for bio in  bios:
            self.repository.delete_biography(bio)
        self.add_biography(merged_bio)
        return merged_bio

    @property
    def computed_values(self):
        """these are the computed values (used for caching),
        that go back as much as possible to the source data """

        class Wrapper:
            def __init__(self, person):
                self.p = self.person = person
                birth_min, birth_max, death_min, death_max = self.merged_biography._get_min_max_dates()
                self.geboortedatum_min = format_date(birth_min)
                self.geboortedatum_max = format_date(birth_max)
                self.sterfdatum_min = format_date(death_min)
                self.sterfdatum_max = format_date(death_max)
                self.geboorteplaats = self.merged_biography.get_value('geboorteplaats')
                self.sterfplaats = self.merged_biography.get_value('sterfplaats')
                self.names = u' '.join([unicode(name) for name in self._names])

                self.has_contradictions = bool(person.get_biography_contradictions())
                illustrations = self.merged_biography.get_illustrations()
#                self.thumbnail = illustrations and illustrations[0].has_image() and illustrations[0].image_small_url or u''
                illustration = illustrations and illustrations[0]
                if illustration:
                    url = illustration.image_small_url
                    url = url[len(illustration._images_cache_url):]
                    if url.startswith('/'):
                        url = url[1:]
                    self.thumbnail = url
                else:
                    self.thumbnail = ''

            @property
            def snippet(self):
                self._snippet = u''
                for bio in self.p.get_biographies():
                    s = bio.snippet()
                    if s:
                        return s

            @property
            def _name(self):
                name = self.merged_biography.naam()
                return name

            @property
            def _names(self):
                return self.merged_biography.get_names()
            @property
            def merged_biography(self):
#                if not merged_biography.get_biographies():
#                    logging.warning('NO biographies found for person with bioport id %s' % person.bioport_id)
                try:
                    return self._merged_biography
                except AttributeError:
                    self._merged_biography = self.p.get_merged_biography()
                    return self._merged_biography

            @property
            def naam(self):
                return self._name and self._name.guess_normal_form()
            @property
            def sort_key(self):
                return self._name and self._name.sort_key()
            @property
            def geslachtsnaam(self):
                return self._name.geslachtsnaam()
            @property
            def has_illustrations(self):
                return bool(self.merged_biography.get_illustrations())
            @property
            def search_source(self):
                result = []
                for name in self._names:
                    result.append(name.volledige_naam())
                for bio in self.p.get_biographies():
                    result.append(bio.get_text_without_markup())
                result = [unicode(s) for s in result]
                return u'\n'.join(result)
            @property
            def sex(self):
                return self.merged_biography.get_value('geslacht')

            @property
            def geboortedatum(self):
                date1 = self.merged_biography.get_value('geboortedatum')
                if not date1:
                    event = self.merged_biography.get_event('baptism')
                    if event is not None:
                        date1 = event.get('when')
                return date1

            @property
            def sterfdatum(self):
                date2 = self.merged_biography.sterfdatum()
                if not date2:
                    event = self.merged_biography.get_event('burial')
                    if event is not None:
                        date2 = event.get('when')
                return date2


        return Wrapper(self)

class Contradiction(object):
    """An object which represents a person with contradictory
    biographies.
    """

    __slots__ = ["type", "values"]

    def __init__(self, type, values):
        self.type = type
        self.values = values

    def __str__(self):
        s = "<%s at %s; type=%s values=%s>" % (self.__class__.__name__, id(self),
                                               repr(self.type), repr(self.values))
        return s

    def __len__(self):
        return len(self.values)

    __repr__ = __str__
