#!/usr/bin/env python

from plone.memoize import instance

from bioport_repository.repocommon import is_valid_bioport_id
from bioport_repository.merged_biography import MergedBiography, BiographyMerger
from bioport_repository.db_definitions import STATUS_NEW
from bioport_repository.common import format_date

class Person(object):
    """A Person is an object that is identified with a bioport
    identifier.  It is usually associated with one or more Biography
    objects.
    """

    def __init__(self, 
        bioport_id,
        biographies=None,  # XXX - this is not used!
        repository=None,
        record=None,
        status=STATUS_NEW,
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
#      assert is_valid_bioport_id(bioport_id)
        self.id = self.bioport_id = bioport_id
        self.repository = repository
        self.record = record
        self.status = status
        self.remarks = remarks
        if record is not None:
            self.status = record.status
            self.remarks = record.remarks
        self.score = score

    def __eq__(self, other):
        if type(other) == type(self) and other.bioport_id == self.bioport_id:
            return True
        return False

    @instance.clearafter
    def refresh(self):
        """empty the cache"""
        # XXX - why is it not implemented?
        # well, maybe it is, given that is has a clearafter decorator
        pass

    def singleton_id(self, id, **args):
        # XXX - what is this?
        return self.id

    def __str__(self):
        if self.get_names():
            return '<Person %s with id %s>' % (self.get_names()[0], self.id)
        else:
            return '<Person with id %s>' % (self.id)

    __repr__ = __str__


    @instance.clearafter
    def add_biography(self, biography, comment=None):
        biography.set_value('bioport_id',self.get_bioport_id())
        if not comment:
            comment='added biography to %s' % self
            
        self.repository.save_biography(
           biography=biography, 
           comment = comment,
           )
        
#    @instance.clearafter
#    def _instance_clearafter(self):
#        pass
    
#    @instance.memoize
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

#    @instance.memoize
    def get_sources(self):
        return [bio.get_source() for bio in self.get_biographies()]

    def get_quality(self):
        return max([bio.get_quality() for bio in self.get_biographies()])

#    @instance.memoize
    def get_value(self, k, default=None):
        return self.get_merged_biography().get_value(k, default)

#    @instance.memoize
    def get_merged_biography(self):
        """
        Return a Biography that represents the 'cascaded information'
        contained in the biographies of this person.
        """
        return MergedBiography(self.get_biographies())

    def get_bioport_biography(self, create_if_not_exists=True):
        #convenience mthod
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
#        event = self.get_merged_biography().get_event('birth')
#        if event is not None:
#            return event.get('when')

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
        
        the first data is the date of bith, but if that does not exist, it is date of baptism
        the second date is the date of death, or, if that does not exist, date of burial
        """
        date1 = self.geboortedatum() 
#        if not date1:
#            event = self.get_merged_biography().get_event('baptism')
#            if event is not None:
#                date1 = event.get('when')
#        
        date2 = self.sterfdatum()
        #XXX remove the 'False'part!
#        if not date2:
#            event = self.get_merged_biography().get_event('burial')
#            if event is not None:
#                date2 = event.get('when')
        return date1, date2
        
    
    def names(self):
        return self.record.names

    def thumbnail(self):
        return self.record.thumbnail

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

    def get_biography_contradictions(self):
        """Iterates over all biographies and checks birth dates and
        places for contradictions (e.g. one bio states "x" while
        another one states "y").
        Rerturn a list of Contradiction instances or [].
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
        """these are the computed values, that go back as much as possible to the source data """
        
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
                illustrations =  self.merged_biography.get_illustrations()
                self.thumbnail = illustrations and illustrations[0].has_image() and illustrations[0].image_small_url or u''
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
                    self._merged_biography =  self.p.get_merged_biography()
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
                result =[]
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
                date1 =  self.merged_biography.get_value('geboortedatum')
                #XXX remove the 'False'part!
                if not date1:
                    event = self.merged_biography.get_event('baptism')
                    if event is not None:
                        date1 = event.get('when')
                return date1
            
            @property
            def sterfdatum(self):
                
                date2 = self.merged_biography.sterfdatum()
                #XXX remove the 'False'part!
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
        s = "<%s at %s; type=%s values=%s>" % (self.__class__.__name__,  id(self),
                                               repr(self.type), repr(self.values))
        return s

    def __len__(self):
        return len(self.values)

    __repr__ = __str__
