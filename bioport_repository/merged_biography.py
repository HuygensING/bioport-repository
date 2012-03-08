#!/usr/bin/env python
import copy
#import simplejson
from biodes import BioDesDoc
#from bioport_repositorydata_extraction import BioDataExtractor
from bioport_repository.biography import Biography
from bioport_repository.common import to_date
from lxml.etree import SubElement
from lxml import etree

class MergedBiography:    
    """ """
    
    def __init__(self, biographies):
#        ls = [(b.get_source().quality,b.id, b) for b in biographies]
#        ls.sort(reverse=True)
#        ls = [b for q,i, b in ls]
        self._biographies = biographies
    
    def to_string(self):
        """return a BioDes file that represents all information that we want to share"""
        return self.to_xml().to_string()
    
    def to_xml(self): 
        doc = BioDesDoc()
        bioport_id = self.get_biographies()[0].get_bioport_id()
        #add the basic onfirmation
        doc.from_args(
            naam_publisher='Het Biografisch Portaal',
            url_biografie='http://www.biografischportaal.nl/persoon/%s' % bioport_id,
            url_publisher='http://www.biografischportaal.nl',
            namen=self.get_names(),
            bioport_id=bioport_id,
            sex = self.get_value('sex'),
        )
        #add the events
        for event_type in ['birth', 'death', 'funeral', 'baptism', 'floruit']:
            event = self.get_event(event_type)
            if event is not None:
                doc._add_event_element(event)
        #add illustrations
        for ill in self.get_illustrations():
            doc._add_figure(url=ill.source_url, head=ill.caption)
        #add links to all sources
        for bio in self.get_biographies():
            if bio.get_source().id != 'bioport':
                #construct a bibl element
                bibl = SubElement(doc.get_element_biography(), 'bibl')
                publisher = SubElement(bibl, 'publisher')
                publisher.text = bio.get_value('name_publisher')
                ref = SubElement(bibl, 'ref')
                ref.attrib['target'] = bio.get_value('url_biography' )
                author = bio.get_value('author')
                if author:
                    for s in author:
                        el_author = SubElement(bibl, 'author') 
                        el_author.text = s
        return doc
        
    def to_dict(self):
        bioport_id = self.get_biographies()[0].get_bioport_id()
        d = dict(
            naam_publisher='Het Biografisch Portaal',
            url_biografie='http://www.biografischportaal.nl/persoon/%s' % bioport_id,
            url_publisher='http://www.biografischportaal.nl',
            namen=[n.volledige_naam() for n in self.get_names()],
            bioport_id=bioport_id,
            sex = self.get_value('sex'),
            )
        
        #add the events
        d['event'] = []
        for event_type in ['birth', 'death', 'funeral', 'baptism', 'floruit']:
            event = self.get_event(event_type)
            if event is not None:
                d['event'] += [self._event_to_dict(event)]
        
        #the category this person is in
        states = []
        for state in self.get_states(type='category'): 
            states.append(state.get('idno'))
        d['categories'] = states
            
        d.update({'figures':[dict(url=ill.source_url, head=ill.caption) for ill in self.get_illustrations()]})
        #add links to all sources
        bios = []
        for bio in self.get_biographies():
            if bio.get_source().id != 'bioport':
                #construct a bibl element
                author = bio.get_value('author') or []
                bios.append(dict(
                    publisher= bio.get_value('name_publisher'),
                    url_biography = bio.get_value('url_biography'),
                    author = [s for s in author],
                    source_id = bio.get_source().id,
                    ))
                
        d.update(dict(biographies = bios))
        return d

    def _event_to_dict(self, event):
        """represent the main info of the event as a json dictionary"""
        return dict(
                type = event.get('type'),
                when = event.get('when'),
                text = event.text,
                place = event.find('place') is not None and event.find('place').text,
                )
    def get_biographies(self):
        return self._biographies
    
    def geboortedatum(self):
        event = self.get_event('birth')
        if event is not None:
            if event.get('when'):
                return event.get('when')
            elif event.find('date') is not None:
                return event.find('date').text
    def sterfdatum(self):
        event = self.get_event('death')
        if event is not None:
            if event.get('when'):
                return event.get('when')
            elif event.find('date') is not None:
                return event.find('date').text
    
    def get_geboortedatum_min(self):
        return self._get_min_max_dates()[0]

    def _get_min_max_dates(self):
        """return a tuple (birth_date_min, birth_date_max, death_date_min, death_date_max
        
        using as much information as is possibly available"""
        
        def extract_min_max_from_event(type):
            """given an event, return a miminal and maximal date
            
            returns a tuple of two date instances
            """
            event = self.get_event(type)
            if event is not None:
                date_min = date_max =  event.get('when')
                if not date_min:
                    date_min =  event.get('notBefore')
                if not date_max:
                    date_max = event.get('notAfter')
                try:
                    date_min = to_date(date_min)
                except ValueError:
                    date_min = None
                try:
                    date_max = to_date(date_max, round='up')
                except ValueError:
                    date_max = None
                return (date_min, date_max)
            else:
                return (None, None)
        birth_date_min,   birth_date_max   = extract_min_max_from_event('birth') 
        death_date_min,   death_date_max   = extract_min_max_from_event('death') 
        baptism_date_min, baptism_date_max = extract_min_max_from_event('baptism') 
        burial_date_min,  burial_date_max  = extract_min_max_from_event('burial') 
   
        #we can assume people in the portal lived for at least 20 years
        DELTA_BIRTH_DEATH_MIN = 20
        DELTA_BIRTH_DEATH_MAX = 100
        DELTA_BIRTH_BAPTISM_MIN = 0
        DELTA_BIRTH_BAPTISM_MAX = 10 
        if not birth_date_min:
            if baptism_date_min:
                try:
                    birth_date_min = baptism_date_min.replace(year = baptism_date_min.year-DELTA_BIRTH_BAPTISM_MAX)
                except ValueError:
                    pass
            elif death_date_min:
                #we assume people live less than 100 year
                try:
                    birth_date_min = death_date_min.replace(year = death_date_min.year-DELTA_BIRTH_DEATH_MAX)
                except ValueError:
                    pass
            elif burial_date_min:
                try:
                    birth_date_min = burial_date_min.replace(year = burial_date_min.year-DELTA_BIRTH_DEATH_MAX)
                except ValueError:
                    pass
                       
        if not birth_date_max:
            if baptism_date_max:
                birth_date_max = baptism_date_max.replace(year=baptism_date_max.year - DELTA_BIRTH_BAPTISM_MIN)
            elif death_date_max:
                try:
                    birth_date_max = death_date_max.replace(year = death_date_max.year-DELTA_BIRTH_DEATH_MIN)
                except ValueError:
                    pass
            elif burial_date_max:
                try:
                    birth_date_max = burial_date_max.replace(year = burial_date_max.year-DELTA_BIRTH_DEATH_MIN)
                except ValueError:
                    pass
        
        if not death_date_min:
            if birth_date_min:
                death_date_min = birth_date_min.replace(year = birth_date_min.year + DELTA_BIRTH_DEATH_MIN)
       
        if not death_date_max:
            if birth_date_max:
                death_date_max = birth_date_max.replace(year = birth_date_max.year + DELTA_BIRTH_DEATH_MAX) 
                
        return birth_date_min, birth_date_max, death_date_min, death_date_max
    
    def get_geboortedatum_max(self):
        return self.geboortedatum()
    
    def get_sterfdatum_min(self):
        return self.sterfdatum()
    
    def get_sterfdatum_max(self):
        return self.sterfdatum()
    
    def get_event(self, type):
        for bio in self.get_biographies():
            if bio.get_event(type) is not None:
                return bio.get_event(type)
            
    def get_states(self, type):
        for bio in self.get_biographies():
            if bio.get_states(type):
                return bio.get_states(type)
        return []
    
    def get_value(self, k, default=None):
        """get the 'merged' value of for k
        
        for some fields, the 'merged value' is 'cumulative'
            (e.g. for illustraties we want to show all illustrations)
        for others it is the value from the 'most reliable' source 
            (e.g. for the place of birth)
        while for others (dates) we have special cases
        """
        cumulative_keys = [
               'illustraties',
               'beroep',
               ]
        
        if k in cumulative_keys:
            result = []
            for bio in self.get_biographies():
                result += bio.get_value(k, [])
            if not result:
                result = default 
            return result
        
        else:
            for b in self.get_biographies():
                v = b.get_value(k)
                if v:
                    return v
                
        return default
    
    def get_religion(self):
        for bio in self.get_biographies():
            if bio.get_religion() is not None:
                return bio.get_religion()
            
    def title(self):
        for b in self.get_biographies():
            if b.title():
                return b.title()
            
    def get_names(self): 
        result = []
        for bio in self.get_biographies():
            if bio.source_id == 'bioport' and bio.get_names():
                return bio.get_names()
            else:
                for naam in bio.get_names():
                    if naam.volledige_naam() not in [n.volledige_naam() for n in result]:
                        result.append(naam)
        return result 

    def get_illustrations(self, default=[]):
        ls = []
        for bio in self.get_biographies():
            ls += bio.get_illustrations() 
        return ls or default
    
    def naam(self):
        """return the first name that you can find in the associated biographies"""
        for b in self.get_biographies():
            s= b.naam()
            if s:
                return s

class BiographyMerger(object): 
    """methods for merging biographies into a single new one"""
    @staticmethod
    def merge_biographies(bio1, bio2):
        """merge the biographies in bios into a single one
        
        changes bio1 and returns the changed biography
        
        bio1 takes precedence over bio2
       
        arguments:
            bio1, bio2: two Biography instances
        returns:
            an instance of Biography if:
                the merge succeeded
                the merged biography is different from bio1
            None: otherwise
            
        if the bios are not mergeable (they may have different data), don't change anything, and return the list
        """
        _changed = False
        
        #merged categories
        merged_categories = bio1.get_states(type='category') + bio2.get_states(type='category')
        merged_categories = [x.get('idno') for x in merged_categories]
        if set(merged_categories) != set([x.get('idno') for x in bio1.get_states(type='category')]):
            bio1.set_category(merged_categories)
            _changed = True
        
        merged_figures = bio1.get_figures_data() + bio2.get_figures_data()
        if set(merged_figures) != set(bio1.get_figures_data()):
            bio1._replace_figures(merged_figures)
            _changed = True
        
        for x in [
              'birth_date',
             'birth_place',
             'death_date',
             'death_place',
             ]:
            if not bio1.get_value(x) and bio2.get_value(x):
                bio1.set_value(x, bio2.get_value(x))
                _changed = True
        for x in [
             'birth_date',
             'death_date',
             ]:
            v1 = bio1.get_value(x)
            v2 = bio2.get_value(x)
            if v1 and v2 and len(v1) < len(v2) and v2[:len(v1)] == v1:
                bio1.set_value(x, bio2.get_value(x))
                _changed = True
                
        if _changed:
            return bio1
    
    
#        for bio in bios[1:]:
#            merged_bio = BiographyMerger._merge_biographies(merged_bio, bio)
#            if not merged_bio:
#                return bios
#        return merged_bio
    @staticmethod
    def _merge_biographies(bio1, bio2):
        """try to merge bio1 and bio2 - if we cannot (because they are not consistent), return None""" 
        #single values that must be equal in both biographies
        ls = ['name_publisher', 'url_publisher', 'url_biography', 'sex', 'title_biography']
        dct = {}
        for k in ls:
            v1= bio1.get_value(k)
            v2= bio2.get_value(k)
            if v1 and v2 and v1 != v2:
                raise Exception('Cannot merge biographies because values for %s are different (%s and %s)' % (k,v1, v2 ))
                return
            else:
                dct[k] = v1 or v2
                
        names = bio1.get_names()
        for n2 in  bio2.get_names():
            if n2 not in names:
                names.append(n2)
            
        dct['names'] = names
        
        merged_bio = Biography(source_id=bio1.source_id, biodes_document=bio1.to_string())
        merged_bio.from_args(**dct)
        
        #unique states
#        unique_states = []
        #non-unique states 
        states1 = bio1.get_states()
#        states1 = [state for state in states1 if state.get('type') not in unique_states]
        states2 = bio2.get_states()
#        states2 = [state for state in states2 if state.get('type') not in unique_states]
        for state in states2:
            if etree.tostring(state).strip() not in [etree.tostring(s).strip() for s in states1]: #@UndefinedVariable
                #copy the state (instead of moving it, which will change bio2 as well)
                state = copy.deepcopy(state)
                merged_bio._add_state_element(state)
            
        #unique events
        unique_events = ['birth', 'death']
        #non-unieuqe events
        events1 = merged_bio.get_events() #these are all events from bio1
        events2 = bio2.get_events()
        events = events1
        for bio2_event in events2:
            if etree.tostring(bio2_event).strip() not in [etree.tostring(e).strip() for e in events]: #@UndefinedVariable
                if bio2_event.get('type') in unique_events:
                    #if this event can occur only once, we check for consistency with an eventual existing event
                    #and if they are consistent, update accordingly
                    bio1_event = merged_bio.get_event(type=bio2_event.get('type'))
                    if bio1_event is not None:
                        when1 = bio1_event.get('when', '')
                        when2 = bio2_event.get('when', '')
                        if when1 and when2 and not (when1 in when2 or when2 in when1):
                            #these are incompatible
                            return
                        elif when1 in when2:
                            bio1_event.set('when', when2)
                        
                    else:
                        #no event of this type exists yet in bio1
                        merged_bio._add_event_element(copy.deepcopy(bio2_event))
                else:
                    merged_bio._add_event_element(copy.deepcopy(bio2_event))
        return  merged_bio
        
