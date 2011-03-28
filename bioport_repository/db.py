from __future__ import with_statement

import random
import os
import types
import re
import logging
import contextlib
from datetime import datetime

from lxml import etree

import sqlalchemy
from sqlalchemy.exceptions import IntegrityError, InvalidRequestError
from sqlalchemy.orm import aliased
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import create_engine, desc, and_, or_, not_

from names.similarity import soundexes_nl
from names.common import TUSSENVOEGSELS, words
from names.name import TYPE_PREPOSITION,  TYPE_FAMILYNAME,  TYPE_GIVENNAME , TYPE_INTRAPOSITON,  TYPE_POSTFIX,  TYPE_TERRITORIAL 

from bioport_repository.db_definitions import PersonRecord, AntiIdentifyRecord,\
    CacheSimilarityPersons
from bioport_repository.db_definitions import DeferIdentificationRecord
from bioport_repository.db_definitions import ChangeLog, Occupation
from bioport_repository.db_definitions import Category, Base, Location, Comment
from bioport_repository.db_definitions import PersonSource, PersonSoundex, AuthorRecord
from bioport_repository.db_definitions import RelPersonCategory, PersonName
#from bioport_repository.db_definitions import NaamRecord 
from bioport_repository.db_definitions import SoundexRecord
from bioport_repository.db_definitions import (CacheSimilarityPersons,
                                               BioPortIdRecord,
                                               RelBioPortIdBiographyRecord,
                                               BiographyRecord,
                                               SourceRecord,
                                               STATUS_NEW, STATUS_FOREIGNER, STATUS_MESSY, STATUS_REFERENCE, STATUS_NOBIOS,
                                               STATUS_ALIVE,
                                               )



from bioport_repository.similarity.similarity import Similarity
from bioport_repository.person import Person
from bioport_repository.biography import Biography 
from bioport_repository.source import Source 
from bioport_repository.common import format_date , to_date
from bioport_repository.versioning import Version
from bioport_repository.merged_biography import BiographyMerger

LENGTH = 8  # the length of a bioport id
ECHO = False
EXCLUDE_THIS_STATUS_FROM_SIMILARITY = [5,9]

class DBRepository:
    """Interface with the MySQL database"""
    
    SIMILARITY_TRESHOLD = 0.70 #
    def __init__(self, 
        db_connection, 
        user,
        repository=None,
        ):       
        self.connection = db_connection 
        self.user = user
        self.metadata = Base.metadata
        metadata = self.metadata 
        self._session = None
        
        #get the data from the db
        self.engine = Base.metadata.bind = metadata.bind = create_engine(
                self.connection, 
                convert_unicode=True, 
                encoding='utf8', 
                echo=ECHO,
                pool_recycle=3600, #set pool_recycle to one hour to avoig sql server has gone away errors
                strategy="threadlocal",
                )
        self.Session = sessionmaker(bind=self.engine)
            
        self.db = self 
        self.repository = repository 
        
    def get_session(self):
        """Return a session object."""
        if not self._session:
            self._session = self.Session()
        return self._session
        
    @contextlib.contextmanager
    def get_session_context(self):
        """Return a session object usable as a context manager 
        automatically calling flush() on __exit__ and rollback() 
        in case of errors.
        """
        session = self.get_session()

        try:
            yield session
        except:
            session.rollback()
            raise
        else:
            try:
                session.flush()
            except:
                session.rollback()
                raise

    def query(self):
        return self.get_session().query
        
    def close_session(self):
        if self._session:
            self._session.close()
            self._session = None

    def add_source(self, src):
        assert src.id
        r = SourceRecord(id=src.id, url=src.url, description=src.description, xml=src._to_xml())
        with self.get_session_context() as session:
            session.add(r)
            msg = 'Added source'
            self.log(msg, r)

    def save_source(self, src):
        with self.get_session_context() as session:
            try:
                r = session.query(SourceRecord).filter_by(id=src.id).one()
            except sqlalchemy.orm.exc.NoResultFound:
                return self.add_source(src) 
            r.url = src.url
            r.description = src.description
            r.quality = src.quality
            r.xml = src._to_xml()
            msg = 'saved source'
            self.log(msg, r)
        
    def add_bioport_id(self, bioport_id):
        """Add a bioport id to the registry"""
        with self.get_session_context() as session:
            r_bioportid = BioPortIdRecord(bioport_id=bioport_id)
            session.add(r_bioportid)
            msg = 'Added bioport_id %s to the registry'
            self.log(msg, r_bioportid)

    def get_source(self, source_id):
        """Get a Source instance with id= source_id """
        with self.get_session_context() as session:
            qry = session.query(SourceRecord) 
            if isinstance(source_id, unicode):
                source_id = source_id.encode('ascii')
            qry = qry.filter(SourceRecord.id==source_id)
            r = qry.one()
            source = Source(id=r.id, url=r.url, description = r.description, quality=r.quality, xml=r.xml)
            return source
    
    def get_sources(self, order_by='quality', desc=True): 
        with self.get_session_context() as session:
            qry = session.query(SourceRecord)
            if order_by:
                if desc:
                    qry = qry.order_by(sqlalchemy.desc(order_by))
                else:
                    qry = qry.order_by(order_by)
            ls = qry.all()
            #session.close()
            return [Source(r.id, r.url, r.description, quality=r.quality, xml = r.xml, repository=self.repository) for r in ls]

    def delete_source(self, source):
        session = self.get_session()
        qry =  session.query(SourceRecord).filter_by(id=source.id)
        try:
            r_source = qry.one()
        except sqlalchemy.orm.exc.NoResultFound:
            raise ValueError('Cannot delete source %s because it cannot be found in the database' % source.id)

        with self.get_session_context() as session:
            self.delete_biographies(source=source)
            msg = 'Delete source %s' % source
            self.log(msg, r_source)
            session.delete(r_source)
        
    def get_bioport_ids(self):
        session = self.get_session()
        rs = session.query(BioPortIdRecord.bioport_id).distinct().all()
        return map(lambda x: x[0], rs)

    def delete_biographies(self, source): #, biography=None): 
        with self.get_session_context() as session:
            # delete also all biographies associated with this source
            session.query(BiographyRecord).filter_by(source_id = source.id).delete()
            session.execute('delete rel from relbiographyauthor rel left outer join biography b on rel.biography_id = b.id where b.id is null')
            session.execute('delete a   from author a               left outer join relbiographyauthor rel on rel.author_id = a.id where rel.author_id is null')
            #delete also all records in person_record table
            sql = """DELETE  s from person_source s
                where s.source_id = '%s'""" % source.id 
            session.execute(sql)
            #delete all persons  that have become 'orphans' (i.e. that have no source anymore) 
            sql = """DELETE  p from person p 
                left outer join person_source s
                on s.bioport_id = p.bioport_id
                where s.bioport_id is Null"""  
            session.execute(sql)
            #delete all orphaned names and soundexes
            sql = """DELETE  n from person_name n 
                left outer join person p
                on n.bioport_id = p.bioport_id
                where n.bioport_id is Null"""  
            session.execute(sql)
            sql = "delete n   from naam n   where src = '%s'" % source.id          
            session.execute(sql)
            session.execute('delete s   from soundex s            left outer join naam n  on s.naam_id = n.id where n.id is null')
            
#            session.expunge_all()

    def delete_biography(self, biography):
        with self.get_session_context() as session:
            # delete also all biographies associated with this source
            session.query(BiographyRecord).filter_by(id = biography.id).delete()
            session.flush()
            #now update the person associated with this biography
            self.update_person(biography.get_bioport_id())
        
#    def add_naam(self, naam, bioport_id, src):
#        """add a record to the table 'naam'
#        
#        arguments:
#            naam - an instance of Naam 
#            biography - an instance of biography
#        """
#        with self.get_session_context() as session:
#            item = NaamRecord()
#            session.add(item)
#            
#            item.bioport_id = bioport_id
#            item.volledige_naam = naam.guess_normal_form()
#            item.xml = naam.to_string()
#            item.sort_key = naam.sort_key()
#            item.src = src
#            #item.src = src and unicode(src) or unicode(self.id)
#            
#            assert type(item.xml) == type(u'')
#            assert type(item.sort_key) == type(u'')
#
#            item.soundex = []
#            #item.variant_of = variant_of
#            
#            for s in naam.soundex_nl():
#                soundex = SoundexRecord()
#                soundex.soundex = s
#                item.soundex.append(soundex)
#            return item.id 
   
    def delete_names(self, bioport_id):
        session  = self.get_session()
#        session.execute('delete c FROM cache_similarity c join naam n1 on c.naam1_id = n1.id where n1.biography_id="%s"' % biography_id)
#        session.execute('delete c FROM cache_similarity c join naam n2 on c.naam1_id = n2.id where n2.biography_id="%s"' % biography_id)
        session.execute('delete s   from soundex s  left outer join naam n  on s.naam_id = n.id where n.bioport_id = "%s"' % bioport_id)
        session.execute('delete n   from naam n where bioport_id = "%s"' % bioport_id)
        session.expunge_all()

    
    def save_biography(self, 
       biography, 
       user, 
       comment,
       ):
        """save the information of the biography in the database 
        
        adds a new version for this biography in the database
        
        arguments:
            biography - is a Biography instance
            user - a string
            comment - a string
        returns: 
            None
        """
        assert user
        with self.get_session_context() as session:
            #register the biography in the bioportid registry
            #(note that this changes the XML in the biography object)
            self._register_biography(biography)
            
            #get all biographies with this id, and increment their version number with one
            ls =  self._get_biography_records(
#                source_id=biography.source_id,
#                bioport_id=biography.get_bioport_id(),
                local_id=biography.id,
                order_by='version',
                )
            ls = enumerate(ls)
            ls = list(ls)
            ls.reverse()
            for i, r_bio in ls:
                r_bio.version = i + 1 
                session.flush()
            
            r_biography = BiographyRecord(id=biography.get_id())
                
            r_biography.source_id = biography.source_id
            r_biography.biodes_document = biography.to_string()
            r_biography.source_url = unicode(biography.source_url)
            biography.version = r_biography.version = 0
            r_biography.user = user
            r_biography.comment = comment
            r_biography.time = datetime.today().isoformat()
            session.add(r_biography)
#                
        # update the information of the associated person (or add a person 
        # if the biography is new)
        default_status = self.get_source(biography.source_id).default_status
        self.update_person(biography.get_bioport_id(), default_status=default_status)
            
        msg  = 'saved biography with id %s' % (biography.id)
        self.log(msg=msg, record = r_biography)

        
    def _add_author(self, author, biography_record):   
        """
        author - a string
        biography - a biography instance
        """

    def save_person(self, person):
        """save the information of this person in the database table
        
        person:
            a Person instance
        """
        with self.get_session_context() as session:
            try:
                r = session.query(PersonRecord).filter(PersonRecord.bioport_id==person.get_bioport_id()).one()
            except NoResultFound:
                r = PersonRecord(bioport_id=person.get_bioport_id())
                session.add(r)
            person.record = r
            #XXX: is this obsolete?
            if getattr(person, 'remarks', None) is not None:
                r.remarks = person.remarks
            if getattr(person, 'status', None):
                r.status = person.status

            msg = 'Changed person'
            self.log(msg, r)

    def update_person(self,
          bioport_id, 
          default_status=STATUS_NEW,
          compute_similarities=False,
          ):
        """add or update a person table with the information contained in its biographies
        
        - bioport_id:  the id that identifies the person
        - default_status: the status given to the Person if it is a newly added person
        - compute_similarities: computes similarites (very expensive)
        """
        with self.get_session_context() as session:
            #check if a person with this bioportid alreay exists
            try:  
                r_person = session.query(PersonRecord).filter_by(bioport_id=bioport_id).one()
            except sqlalchemy.orm.exc.NoResultFound:
                #if not, we add a new one
                r_person = PersonRecord(bioport_id=bioport_id) 
                session.add(r_person)
                r_person.status = default_status
                
        person = Person(bioport_id=bioport_id, record=r_person, repository=self)
        with self.get_session_context() as session:
            merged_biography = person.get_merged_biography()
            if not merged_biography.get_biographies():
                logging.warning('NO biographies found for person with bioport id %s' % person.bioport_id)
            
            naam = merged_biography.naam()
            
            names = merged_biography.get_names() 
            if naam:
                r_person.naam = naam.guess_normal_form()
                r_person.sort_key = naam.sort_key()
                r_person.geslachtsnaam = naam.geslachtsnaam()
            else:
                msg = 'merged_biography should at least have one name defined! %s' \
                      ' - biographies: %s'  % (person.bioport_id, person.get_biographies())
                logging.warning(msg)
                r_person.naam = ''
            r_person.has_illustrations = bool(merged_biography.get_illustrations())
            r_person.search_source = person.search_source()
            r_person.sex = merged_biography.get_value('geslacht')
            try:
                birth_min, birth_max, death_min, death_max = merged_biography._get_min_max_dates()
                r_person.geboortedatum_min = format_date(birth_min)
                r_person.geboortedatum_max = format_date(birth_max)
                r_person.sterfdatum_min = format_date(death_min)
                r_person.sterfdatum_max = format_date(death_max)
            except ValueError, error:
                logging.warning('Error updating %s: %s' % (person.bioport_id, error))
#            if r_person.sterfdatum_min and r_person.sterfdatum_min == r_person.sterfdatum_max:
#                r_person.sterfjaar = to_ymd(r_person.sterfdatum_min)[0]
#            if r_person.geboortedatum_min == r_person.geboortedatum_max and r_person.geboortedatum_min:
#                r_person.geboortejaar = to_ymd(r_person.geboortedatum_min)[0]
            r_person.geboorteplaats = merged_biography.get_value('geboorteplaats')
            r_person.sterfplaats = merged_biography.get_value('sterfplaats')
            r_person.names = u' '.join([unicode(name) for name in names])
            r_person.snippet = person.snippet()
            r_person.has_contradictions = bool(person.get_biography_contradictions())
            illustrations =  merged_biography.get_illustrations()
            r_person.thumbnail = illustrations and illustrations[0].image_small_url or u''
            
            #update categories
#            r_person.categories = [RelPersonCategory(category_id=id) for state in merged_biography.get_states(type='categories')]

            session.query(RelPersonCategory).filter(RelPersonCategory.bioport_id==bioport_id).delete()
            
            for category in merged_biography.get_states(type='category'):
                category_id = category.get('idno')
                assert type(category_id) in [type(u''), type('')], category_id
                try:
                    category_id = int(category_id)
                except ValueError:
                    msg = '%s- %s: %s' % (category_id, etree.tostring(category), person.bioport_id)
                    raise Exception(msg)
                r = RelPersonCategory(bioport_id=bioport_id, category_id=category_id)
                session.add(r)
                session.flush()
                
            
            #'the' source -- we take the first non-bioport source as 'the' source
            #and we use it only for filterling later
            #XXX what is this used for??? 
            src = [s for s in merged_biography.get_biographies() if s.source_id != 'bioport']
            if src:
                src = src[0].source_id
            else:
                src = None
                
            #refresh the names 
            self.delete_names(bioport_id=bioport_id)
            self.update_name(bioport_id=bioport_id, names=names)
            
            self.update_source(bioport_id, source_ids = [b.source_id for b in person.get_biographies()])
            
            if person.get_biography_contradictions():
                r_person.has_contradictions = True
            else:
                r_person.has_contradictions = False
    
        #update the different caches to reflect any changes
        if compute_similarities:
            self.fill_similarity_cache(person=person, refresh=True)
         
    def update_persons(self):
        """Update the information of all the persons in the database.
        Return the number of processed persons.
        """
        persons = self.get_persons()
        total = len(persons)
        for index, person in enumerate(persons):
            index += 1
            logging.info("progress %s/%s" % (index, total))
            self.update_person(person.get_bioport_id())
        return total
        
   
    def _soundex_for_search(self, s):
        return soundexes_nl(s, 
            group=2, 
            length=20, 
            filter_initials=True, 
            filter_stop_words=False,
            wildcards=True,
            ) #create long phonetic soundexes

    def update_name(self, bioport_id, names):
        """update the table person_name
        
        arguments:
            names : a list of Name instances
        """
        with self.get_session_context() as session:           
            #delete existing references
            session.query(PersonName).filter(PersonName.bioport_id == bioport_id).delete()
            session.query(PersonSoundex).filter(PersonSoundex.bioport_id == bioport_id).delete()
            for name in names:
                for token in name._guess_constituent_tokens():
                    is_from_family_name = (token.ctype() in [TYPE_TERRITORIAL , TYPE_FAMILYNAME, TYPE_INTRAPOSITON])
                    r = PersonName(bioport_id=bioport_id, name=token.word(), is_from_family_name=is_from_family_name) 
                    session.add(r)
                    soundex = self._soundex_for_search(token.word())
                    for soundex in soundex:
#                        assert len(soundex) <= 1,  'token %s: soundex %s; bioport_id: %s' % (token, soundex, bioport_id)
                        r = PersonSoundex(bioport_id=bioport_id, soundex=soundex, is_from_family_name=is_from_family_name) 
                        session.add(r)
                    
    def update_soundex(self, bioport_id, names):
        """update the table person_soundex
        
        arguments:
            names : a list of Name instances
        """
        return self.update_name(bioport_id, names)
#        with self.get_session_context() as session:
#            #delete existing references
#            session.query(PersonSoundex).filter(PersonSoundex.bioport_id == bioport_id).delete()
#            for name in names:
#                full_name = name.guess_normal_form()
#                family_name = name.guess_geslachtsnaam()
#                full_name_parts =  words(full_name)
#                family_name_parts =  words(family_name)
#                for s in full_name_parts:
#                    is_from_family_name = (s in family_name_parts or s in TUSSENVOEGSELS)
#                    r = PersonSoundex(bioport_id=bioport_id, name=s, is_from_family_name=is_from_family_name) 
#                    session.add(r)
#
#                soundexes_full_name = self._soundex_for_search(full_name)
#                soundexes_family_name = self._soundex_for_search(family_name)
#                for soundex in soundexes_full_name:
#                    is_family_name = soundex in soundexes_family_name 
##                    r = PersonSoundex(bioport_id=bioport_id, soundex=soundex) 
#                    r = PersonSoundex(bioport_id=bioport_id, soundex=soundex, is_from_family_name=is_family_name) 
#                    session.add(r)   
 
    def update_source(self, bioport_id, source_ids):   
        """update the table person_source"""
        with self.get_session_context() as session:
            #delete existing references
            session.query(PersonSource).filter(PersonSource.bioport_id == bioport_id).delete()
            for source_id in source_ids:
                r = PersonSource(bioport_id=bioport_id, source_id=source_id) 
                session.add(r)

    def update_soundexes(self):
        """update the person_soundex table in the database 
        
        use "update_persons" to update the information in the db (including person_soundex)
        """
        session = self.get_session()
        i = 0
        logging.info('updating all soundexes (this can take a while)')
        session.query(PersonSoundex).delete()
        persons = self.get_persons()
        for person in persons:
            i += 1
            if not i % 10:
                logging.info('%s of %s' % (i, len(persons)))
            names = person.get_names() 
            self.update_soundex(person.bioport_id, names)
        logging.info('done')
        
    def fresh_identifier(self):
        session = self.get_session()
        # make a random string of characters from ALPHANUMERIC of lenght LENGTH
        new_bioportid_1 = ''.join([random.choice('0123456789') for i in range(LENGTH)])
        new_bioportid_2 = ''.join([random.choice('0123456789') for i in range(LENGTH)])
        new_bioportid_3 = ''.join([random.choice('0123456789') for i in range(LENGTH)])
        for new_bioportid in (new_bioportid_1, new_bioportid_2, new_bioportid_3):
            try:
                self.add_bioport_id(new_bioportid)
            except IntegrityError:
                # there is a small chance that we already have used
                # the bioport id before: in that case we try agin
                session.rollback()
            else:
                return new_bioportid
        raise ValueError("no valid id found")

    def _register_biography(self, biography): #, bioport_id=None):       
        """register the biography in the bioport registry and assign it a bioport_id if it does not have one
       
        arguments:
            biography: a Biography instance
            
        we 
            1. try to find a bioport id in the biography (in the XML document of the biography)
            2. try to find a bioport id in the registry associated with biography.get_idno()
            3. create a new bioport identifier
        """
        with self.get_session_context() as session:       
            #try to find a bioport id in the Biography
            #XXX this needs to be optimized
            if biography.get_bioport_id() :
                #if it has a bioport_id defined, it should already have been registered
                bioport_id = biography.get_bioport_id()
                try:
                    r_bioportidrecord = session.query(BioPortIdRecord
                             ).filter(BioPortIdRecord.bioport_id==bioport_id).one()
                        
                except NoResultFound:
                    msg = 'This biography seems to have a bioport_id defined that is not present in the database'
                    raise Exception(msg)
                #if this bioport_id redirects to another one, we remove that redirection (as we now attach biography to this id)
                r_bioportidrecord.redirect_to = None
            else:
                #try to find a bioport id in the reistry for this biography
                qry = session.query(RelBioPortIdBiographyRecord).filter_by(biography_id=biography.id)
                rs = qry.all()
                if len(rs) == 1:
                    #this biography is already registered w
                    r_relbioportidbiography = rs[0] 
                    bioport_id = r_relbioportidbiography.bioport_id
                else:
                    bioport_id = self.fresh_identifier()
            
            #now we update the biography as well as the registry
            if bioport_id != biography.get_bioport_id():
                biography.set_value('bioport_id', bioport_id)
            
            #update the registry  
            #if it is not connected to the new biography, we add the relation
            qry = session.query(RelBioPortIdBiographyRecord)
            qry = qry.filter_by(biography_id=biography.id)
            qry = qry.filter_by(bioport_id=bioport_id) 
            try: 
                qry.one()
            except NoResultFound:
                #delete any old information we may have in the registry about this biography
                session.query(RelBioPortIdBiographyRecord).filter(RelBioPortIdBiographyRecord.biography_id==biography.id).delete()
                    
                #now add the new relation
                session.add(RelBioPortIdBiographyRecord(bioport_id=bioport_id, biography_id=biography.id) )

            return bioport_id
    
    def count_biographies(self, source=None):
        """return the number of biographies in the database, 
        excluding those of the source 'bioport'"""
        qry = self.get_session().query(BiographyRecord)
        qry = qry.filter(BiographyRecord.version == 0)
        if source:
            qry = qry.filter(BiographyRecord.source_id==source.id)
        else:
            qry = qry.filter(BiographyRecord.source_id!='bioport')
        return qry.count()
    
    def get_biographies(self, 
        source=None,
        source_id=None,
#        person=None,
        bioport_id=None,
        local_id=None,
        order_by=None,
        version=0,
        limit=None,
        user=None,
        time_from=None,
        time_to=None,
        ): 
        """
        arguments:
            source  - an instance of Source
            person - an instance of Person
            order_by - a string - the name of a column to sort by
            local_id - the 'local id' of the biography - somethign fo the form 'vdaa/w0269', 
                corresponds to the 'id' field in the database
        returns:
            a list of Biography instances
        
        XXX:
            return a generator
        """
        if source:
            if type(source) in types.StringTypes:
                source_id = source
            else:
                source_id = source.id
    
        ls = self._get_biography_records(
            source_id=source_id,
            bioport_id=bioport_id,
            local_id=local_id,
            version=version,
            limit=limit,
            order_by = order_by,
            user=user,
            time_from=time_from,
            time_to=time_to,
        )
        bios = [Biography(id=r.id, 
                      source_id=r.source_id, 
                      repository=self.repository, 
                      biodes_document =r.biodes_document, 
                      source_url=r.source_url, 
                      record=r, 
                      version=r.version, 
                      ) 
            for r in ls]
   
        if bioport_id:
            #        first those biographies that have the present bioport_id in their id - 
            #        then the reset, by quality
            #(note that False comes before True when sorting, hence the 'not in')
            
            bios = [(('bioport/%s' % bioport_id) not in bio.id, -bio.get_quality(), bio.id, bio ) for bio in bios]
            bios.sort()
            bios = [x[-1] for x in bios]
        return bios


    def _get_biography_records(self, 
        source_id = None,
        bioport_id = None,
        local_id = None,
        limit = None,
        order_by = None,
        version=None,
        user=None,
        time_from=None,
        time_to=None,
        ):
        qry = self.get_session().query(BiographyRecord)
               
        if source_id:
            qry = qry.filter_by(source_id=source_id)
            
        if local_id:
            qry = qry.filter_by(id=local_id)
            
        if bioport_id:
            qry = qry.join((RelBioPortIdBiographyRecord, BiographyRecord.id==RelBioPortIdBiographyRecord.biography_id))
            qry = qry.filter(RelBioPortIdBiographyRecord.bioport_id==bioport_id)
       
        if version is not None:
            qry = qry.filter(BiographyRecord.version == version)
        if user:
            qry = qry.filter(BiographyRecord.user == user)
        if time_from:
            qry = qry.filter(BiographyRecord.time >= time_from)
        if time_to:
            qry = qry.filter(BiographyRecord.time <= time_to)
        if order_by == 'quality':
            qry = qry.join((SourceRecord,SourceRecord.id==BiographyRecord.source_id))
            qry = qry.order_by(sqlalchemy.desc(order_by))
            qry = qry.order_by(BiographyRecord.id)
        elif order_by == 'version':
            #order by time added and version
            qry = qry.order_by( BiographyRecord.version, sqlalchemy.desc(BiographyRecord.time))
        elif order_by:
            qry = qry.order_by(order_by)
        if limit:
            qry = qry.limit(limit)
            
        return qry.all()
    
    def get_biography(self, **args):
        """get the unique biography that satisfies **args
        
        if none, or more than one, are found, then raise an Exception
        arguments:
            see get_biographies
        returns:
            a Biography instance
        """
        ls = self.get_biographies(**args)
        assert len(ls) == 1, 'Expected to find exactly one biography with the following arguments (but found %s): %s' % (len(ls), args)
        return ls[0]

    def count_persons(self):        
        session = self.get_session()
        qry = session.query(PersonRecord)
        return qry.count()
    
    def get_persons(self, **args):
        # XXX - There seems to be a memory leak when calling session.execute()
        # this is the same problem described here:
        # http://www.mail-archive.com/sqlalchemy@googlegroups.com/msg13511.html
        # We should investigate further.
        # JG: that thread continues and says "Once I understood that there wasn't really a memory leak, I just... "
        #
        qry = self._get_persons_query(**args)
        #executing the qry.statement is MUCH faster than qry.all()
        ls = self.get_session().execute(qry.statement)
        #but - do we want to make Person objects for each of these things 
        #(yes, because we use lots of information later - for example for navigation)
        #XXX (but is is very expensive)
        result = [Person(bioport_id=r.bioport_id, repository=self.repository, record=r) for r in ls]
        return result   
    
    def _get_persons_query(self,
        bioport_id=None,
        #beroep_id=None,
        #auteur_id=None,
        beginletter=None,
        category=None,
        geboortejaar_min=None,
        geboortejaar_max=None,
        geboortemaand_min=None,
        geboortemaand_max=None,
        geboortedag_min=None,
        geboortedag_max=None,
        levendjaar_min=None,
        levendjaar_max=None,
        levendmaand_min=None,
        levendmaand_max=None,
        levenddag_min=None,
        levenddag_max=None,
        geboorteplaats = None,
        geslacht=None,
        has_illustrations=None, #boolean: does this person have illustrations?
        is_identified=None,
        match_term=None, #use for myqsl 'matching' (With stopwords and stuff)
        order_by='sort_key', 
        place=None,
        search_term=None,  #
        search_name=None, #use for mysql REGEXP matching
        search_family_name=None, #use for mysql REGEXP matching
#                            search_soundex=None, #a string - will convert it to soundex, and try to match (all) of these
        any_soundex=[], #a list of soundex expressions - try to match any of these
        search_family_name_only=False, 
        source_id=None,
        source_id2=None,
        sterfjaar_min=None,
        sterfjaar_max=None,
        sterfmaand_min=None,
        sterfmaand_max=None,
        sterfdag_min=None,
        sterfdag_max=None,
        sterfplaats = None,
        start=None,
        size=None,
        status=None,
        hide_invisible=True, #if true, do not return "invisible" persons, such as those marked as "troep"
        hide_foreigners=False, #if true, do not return persons marked as "buitenlands"
        hide_no_external_biographies=True, #if true, do not return persons that have no external biographies
        where_clause=None,
        has_contradictions=False,
        no_empty_names=True,
        ):
        """construct a sqlalchemy Query filter accordin to the criteria given
        
        returns:
            a Query instance
        
        arguments:
            search_family_name_only (Boolean): if True, consider only the geslachtsnaam (family name) when searching
        """
        session=self.get_session()
        qry = session.query(
            PersonRecord.bioport_id,
            PersonRecord.status,
            PersonRecord.remarks,
            PersonRecord.has_illustrations,
            PersonRecord.geboortedatum_min,
            PersonRecord.geboortedatum_max,
            PersonRecord.sterfdatum_min,
            PersonRecord.sterfdatum_max,
            PersonRecord.naam,
            PersonRecord.names,
            PersonRecord.geslachtsnaam,
            PersonRecord.thumbnail,
            PersonRecord.snippet,
            PersonRecord.timestamp,
            PersonRecord.has_contradictions,
            )
        
        if is_identified:
            #a person is identified if another bioport id redirects to it
            #XXX: this is not a good definition
            PBioPortIdRecord = aliased(BioPortIdRecord)
            qry = qry.join((PBioPortIdRecord, PersonRecord.bioport_id == PBioPortIdRecord.redirect_to))
#            qry = qry.join(BioPortIdRecord).join(RelBioPortIdBiographyRecord)
#            qry = qry.filter(RelBioPortIdBiographyRecord.biography_id.count() > 1)
            
#        if hide_no_external_biographies:
#            qry = qry.filter(not_(sqlalchemy.func.ifnull(PersonRecord.status.in_([9999]), False)))
        if hide_invisible:
            #we always hide the follwing categoires
            
            #(STATUS_FOREIGNER, 'buitenlands'), 
            #    (STATUS_MESSY, 'moeilijk geval (troep)'),
            #    (STATUS_REFERENCE, 'verwijslemma'), 
            #    (STATUS_NOBIOS, 'no external biographies')
            #    (STATUS_ALIVE, 'leeft nog')
            to_hide = [STATUS_FOREIGNER, STATUS_MESSY, STATUS_REFERENCE, STATUS_NOBIOS, STATUS_ALIVE]
            qry = qry.filter(not_(sqlalchemy.func.ifnull(PersonRecord.status.in_(to_hide), False)))
        if hide_foreigners:
            #  (11, 'buitenlands'), 
            qry = qry.filter(not_(sqlalchemy.func.ifnull(PersonRecord.status.in_([STATUS_FOREIGNER]), False)))
#            (1, 'nieuw'),
#            (2, 'bewerkt'),
#            (3, 'moeilijk geval'),
#            (5, 'moeilijk geval (troep)'),
#            (4, 'klaar'), 
#            (7, 'te weinig informatie'), 
#            (8, 'familielemma'), 
#            (9, 'verwijslemma'), 
#            (10, 'nader onderzoek nodig'), 
#            (11, 'buitenlands'), 
#            (12, 'nog niet bewerkt'),
#
        if beginletter:
            qry = qry.filter(PersonRecord.naam.startswith(beginletter))
        
        elif no_empty_names:
            qry = qry.filter(PersonRecord.naam != None)
            qry = qry.filter(PersonRecord.naam != "")
            
        if bioport_id: 
            qry = qry.filter(PersonRecord.bioport_id==bioport_id)
            
        if category:
            if category in ['0']:
                category = None
            qry = qry.join(RelPersonCategory)
            qry = qry.filter(RelPersonCategory.category_id==category)


        geboorte_date_filter = self._get_date_filter(locals(), 'geboorte')
        qry = qry.filter(geboorte_date_filter)
        
        sterf_date_filter = self._get_date_filter(locals(), 'sterf')
        qry = qry.filter(sterf_date_filter)
        
        levend_date_filter = self._get_date_filter(locals(), 'levend')
        qry = qry.filter(levend_date_filter)
        
        if geboorteplaats:
            if '*' in geboorteplaats:
                dafilter = PersonRecord.geboorteplaats.like(
                        geboorteplaats.replace('*', '%')
                    )
                qry = qry.filter(dafilter)
            else:
                qry = qry.filter(PersonRecord.geboorteplaats == geboorteplaats)
                
        if sterfplaats:
            if '*' in sterfplaats:
                dafilter = PersonRecord.sterfplaats.like(
                        sterfplaats.replace('*', '%')
                    )
                qry = qry.filter(dafilter)
            else:
                qry = qry.filter(PersonRecord.sterfplaats == sterfplaats)

        if geslacht:
            qry= qry.filter(PersonRecord.sex==geslacht)
            
        if has_illustrations is not None:
            qry = qry.filter(PersonRecord.has_illustrations==has_illustrations) 
        
        if match_term:
            qry = qry.filter(PersonRecord.naam.match(match_term))
            
        if search_term:
            #full-text search
            ### next code is for MATCH ###
            # Mysql uses the OR operator by default
            # with a '+' in front of each word we use the AND operator
            words = re.split('\W+', search_term)
            words_with_plus = ['+' + word for word in words]
            words_query = ' '.join(words_with_plus)
            qry = qry.filter('match (search_source) against '
                              '("%s" in boolean mode)' % words_query)
            
        qry = self._filter_search_name(qry, search_name, search_family_name_only=search_family_name_only)
        
#        qry = self._filter_soundex(qry, search_soundex, search_family_name_only=search_family_name_only)
        
        if any_soundex:
            qry = qry.join(PersonSoundex)
            qry = qry.filter(PersonSoundex.soundex.in_(any_soundex))
            
        qry = qry.join(PersonSource)
        qry = qry.filter(PersonSource.source_id != u'bioport')
                
        if source_id:
            qry = qry.filter(PersonSource.source_id==unicode(source_id))
        
        if source_id2:
            PersonSource2 = aliased(PersonSource)
            qry = qry.join(PersonSource2)
            qry = qry.filter(PersonSource2.source_id==source_id2)
        
        if status:
            if status in ['0']:
                status = None
            qry = qry.filter(PersonRecord.status == status)

#        if sterfjaar_min:
#            qry = qry.filter(PersonRecord.sterfjaar >= sterfjaar_min)
#        if sterfjaar_max:
#            qry = qry.filter(PersonRecord.sterfjaar <= sterfjaar_max)
        if where_clause:
            qry = qry.filter(where_clause)

        if order_by:
            if order_by == 'random':
                #XXX this is perhaps a slow way of doing is; for our purposes it is also enough to pick a random 
                #id, and do somethin like "where id > randomlypickednumber limit XXX"
                some_bioportid = ''.join([random.choice('0123456789') for i in range(LENGTH)])
                qry = qry.filter(PersonRecord.bioport_id > some_bioportid)
            else:
                qry = qry.order_by(order_by)        
                
        if has_contradictions:
            qry = qry.filter(PersonRecord.has_contradictions==True)
            
        if size:
            qry = qry.limit(size)
        qry = qry.distinct() #XXX: why to we need this?
        return qry
    

    def _get_date_filter(self, data, datetype):
        """
        This function builds a sqlalchemy filter using data in 'data'.
        datetype is used to extract variables from data.
        datetype can be either "geboorte" or "sterf" or "levend"
        """
        datdag_min = data[datetype + 'dag_min']
        datmaand_min = data[datetype + 'maand_min']
        datjaar_min = data[datetype + 'jaar_min']
        datdag_max = data[datetype + 'dag_max']
        datmaand_max = data[datetype + 'maand_max']
        datjaar_max = data[datetype + 'jaar_max']
        maand_min = int(datmaand_min or 1)
        dag_min = int(datdag_min or 1)
        maand_max = int(datmaand_max or 12)
        dag_max = int(datdag_max or 0) 
        date_filter = "TRUE"
        
        
        if datetype == 'levend' and not (datjaar_min or datjaar_max):
            # Everybody was alive in every period of the year, so this
            # does not make any sense
            return date_filter
        
        if datjaar_min or datjaar_max:
            jaar_min = int(datjaar_min or 1)
            jaar_max = int(datjaar_max or 9999)
            start_date = "%04i-%02i-%02i" % (jaar_min, maand_min, dag_min)
            if dag_max:
                end_date = "%04i-%02i-%02i" % (jaar_max, maand_max, dag_max)
            else:
                end_date = "%04i-%02i" % (jaar_max, maand_max)
            if datetype == 'levend':
                date_filter = and_(
                       self._apply_date_operator('geboorte', '<=', end_date), 
                       self._apply_date_operator('sterf', '>=', start_date)
                       ) 
            else:
                date_filter = and_(
                       self._apply_date_operator(datetype, '>=',  start_date),
                       self._apply_date_operator(datetype, '<=', end_date)
                       )
                
        elif (datmaand_min or datdag_min
              or datmaand_max or datdag_max):
            #the user has not specified a year, only a date 
            #basically, we are now searching for people that have a birthday (or died on a date) in a certain range
            field_min = getattr(PersonRecord, datetype + 'datum_min', None)
            field_max = getattr(PersonRecord, datetype + 'datum_max', None)
            SUBSTRING = sqlalchemy.func.SUBSTRING
            field_without_year = SUBSTRING(field_min, 6, 5)
            start_date = "%02i-%02i" % (maand_min, dag_min)
            end_date = "%02i-%02i" % (maand_max, dag_max)
            if start_date>end_date:
                date_filter = or_(field_without_year >= start_date, field_without_year <= end_date)
            else:
                date_filter = and_(field_without_year >= start_date, field_without_year <= end_date)
                
            # We want the month to be specified, i.e. at least a 7-char date
            date_filter = and_(date_filter, sqlalchemy.func.length(field_min)>=7)
            #also, we want to consider only cases in which we are sure about the date
            date_filter = and_(date_filter, field_min == field_max)
        return date_filter

        
    def _apply_date_operator(self, datetype, operator, value):
        """return a filter that on _min and _max
        
        arguments:
            datetype : one of ['geboorte', 'sterf']
            operator : one of ['<=', '>=']
            value : a string in ISO format YYYY[-MM[-DD]] that represents a date
        returns:
            a filter (to a apply to a SQL Alchemy query
        """
        if datetype == 'geboorte':
            if operator == '<=' :
                date_filter = PersonRecord.geboortedatum_max <= format_date(to_date(value, round='up'))
    #             and_(
    #                  PersonRecord.geboortedatum_min <= value,
    #                  PersonRecord.geboortedatum_max <= value)
            elif operator == '>=':
                date_filter = PersonRecord.geboortedatum_min >= format_date(to_date(value))
                #this would be the 'inclusive' version
    #            date_filter = PersonRecord.geboortedatum_max >= value
                
        elif datetype == 'sterf':
            if operator == '<=' :
                date_filter = PersonRecord.sterfdatum_max <= format_date(to_date(value, round='up'))
            elif operator == '>=':
                date_filter = PersonRecord.sterfdatum_min >= format_date(to_date(value))
        
        else:
            raise ValueError("datetype must be one of ['geboorte', 'sterf']") 
        return date_filter
    
  
    def _filter_search_name(self, qry, search_name, search_family_name_only=False):
        """Add an appropriate filter to the qry when searching for search_name
        arguments:
            qry : a sqlalchemy Query instance
            search_name : a string
        returns:
            a Query instance filtered appropriately
        """
        #if the name argument is between quotation marks, we search "exact"
        #(but we still ignore the order)
        if not search_name:
            return qry
        if search_name.startswith('"'):
            search_name = search_name[1:]
            if search_name.endswith('"'):
                search_name = search_name[:-1]
                
            for s in search_name.split():
                #changed this to a faster separate table with the "words" that we are searching for 
#                    qry = qry.filter(PersonRecord.names.op('regexp')(u'[[:<:]]%s[[:>:]]' % s))
                alias = aliased(PersonName)
                qry = qry.join(alias)
                if search_family_name_only:
                    qry = qry.filter(alias.is_from_family_name == True)
                if '?' in s or '*' in s:
                    s = s.replace('?', '_')
                    s = s.replace('*', '%')
                    qry = qry.filter(alias.name.like(s))
                else: 
                    qry = qry.filter(alias.name ==s)
        else:
            qry = self._filter_soundex(qry, search_name, search_family_name_only=search_family_name_only)
        return qry
 
    def _filter_soundex(self, 
        qry, 
        search_soundex,
        search_family_name_only=False,
        ):
        """Add a filter to the Query object qry
        
        arugments:
            search_soundex is a string
            search_family_name_only : if True, only consider the family name (geslachtsnaam)    
        returns: 
            the modified qry
        """
        if search_soundex:
            soundexes = self._soundex_for_search(search_soundex)
            if len(soundexes)==1 and  '?' in soundexes[0] or '*' in soundexes[0]:
                #we can use wildcards, but only if we have a single soundex
                s = soundexes[0]
                s = s.replace('?', '_')
                s = s.replace('*', '%')
                qry = qry.join(PersonSoundex)
                if search_family_name_only:
                    qry = qry.filter(PersonSoundex.is_from_family_name == True)
                qry = qry.filter(PersonSoundex.soundex.like(s))
            else:
                for s in soundexes:
                    alias = aliased(PersonSoundex)
                    qry = qry.join(alias)
                    qry = qry.filter(alias.soundex == s)
                    if search_family_name_only:
                        qry = qry.filter(alias.is_from_family_name == True)
        return qry

    def get_person(self, bioport_id, repository=None):
        session = self.get_session()
        qry = session.query(PersonRecord).filter(PersonRecord.bioport_id ==bioport_id)
        try:
            r = qry.one()
        except NoResultFound:
            id = self.redirects_to(bioport_id)
            if id != bioport_id:
                return self.get_person(id)
            else:
                return None
        if not repository:
            repository = self
        
        person = Person(bioport_id=bioport_id, record=r, repository=repository)
        return person

    def delete_person(self, person):
        with self.get_session_context() as session:
            try:
                r = session.query(PersonRecord).filter(PersonRecord.bioport_id==person.get_bioport_id()).one()
                session.delete(r) 
                session.query(PersonSoundex).filter(PersonSoundex.bioport_id==person.bioport_id).delete()
                msg = 'Deleted person %s' % person
                self.log(msg, r)
            except NoResultFound:
                pass
        
        #remove from cache similarity
        with self.get_session_context() as session:
            qry = session.query(CacheSimilarityPersons)
            qry = qry.filter(or_(
                         CacheSimilarityPersons.bioport_id1==person.get_bioport_id(),  
                         CacheSimilarityPersons.bioport_id2==person.get_bioport_id()
                         ))
            qry.delete()   
                    
    def get_author(self, author_id):
        session = self.get_session()
        qry = session.query(AuthorRecord)
        qry = qry.filter(AuthorRecord.id == author_id)
        return qry.one()
    
    def redirect_identifier(self, bioport_id, redirect_to):
        """add a 'redirect' instruction to this bioport_id"""
        assert bioport_id
        with self.get_session_context() as session:
            qry = session.query(BioPortIdRecord).filter_by(bioport_id=bioport_id)
            r = qry.one()
            # add a new record for the redirection
            r.redirect_to = redirect_to

    def redirects_to(self, bioport_id):
        """follow the rederiction chain to an endpoint
        
        arguments:
            a bioport identifier
        returns:
            a bioport identifier
        NB:
            returns bioport_id if no further redirection is found
        """
        orig_id = bioport_id
        chain = [orig_id]
        i = 0
        while True:
            qry = self.get_session().query(BioPortIdRecord).filter(
                BioPortIdRecord.bioport_id==bioport_id)
            i += 1
            try:
                r_bioportid = qry.one() 
                if  r_bioportid.redirect_to:
                    if r_bioportid.redirect_to in chain:
                        break
                    else:
                        chain.append(r_bioportid.redirect_to )
                else:
                    break
                
            except NoResultFound:
                break
        return chain[-1]
    
    def fill_similarity_cache(self, 
        person=None, 
        k=20, 
        refresh=False, 
        limit=None,
        start=None,
        source_id=None,
        minimal_score=None,
        ):
        """fill a table CacheSimilarityPersons with, for each name in the index, a record with the 20 most similar other names in the index
       
           arguments:
               k - the maxium number of 'most similar items'  to add
               person - an instance of Person
               refresh - throw away existing data and calculate from 0 (should only be used if function has changed)
               limit - an integer - compute only for that amount of persons
        """     
        if minimal_score is None:
            minimal_score = self.SIMILARITY_TRESHOLD
        if source_id:
            source_id = unicode(source_id)
            
        logging.info('Refreshing similarity table for %s, refresh=%s' % (source_id, refresh))
        
        #if the person argument is not given, we update for all persons
        if person:
            persons = [person]
        else:
            persons = self.get_persons(source_id=source_id, start=start)
            
        i = 0        
        with self.get_session_context() as session:
            for person in persons:
                i += 1
                if limit and i > limit:
                    break
                bioport_id = person.bioport_id
                
                #check if we have alread done this name
                qry = session.query(CacheSimilarityPersons.bioport_id1)
                qry = qry.filter_by(bioport_id1=bioport_id, bioport_id2=bioport_id) 
                
                if not refresh and qry.all():
                    #we have already done this person , and we did not explicitly call for a refresh
    #                print 'already done'
                    logging.info('[%s/%s] skipped computing similarities - already in database' % (i, len(persons)))
                    continue
                else:
                    if refresh:
                        #remove  all info that we have of this person
                        qry = session.query(CacheSimilarityPersons).filter(CacheSimilarityPersons.bioport_id1 == bioport_id).delete()
                        qry = session.query(CacheSimilarityPersons).filter(CacheSimilarityPersons.bioport_id2 == bioport_id).delete()
                        session.commit()
                    logging.info('[%s/%s] computing similarities: %s' % (i, len(persons), person))
                    #we add the identity score so that we can check later that we have 'done' this record, 
                    self.add_to_similarity_cache(bioport_id, bioport_id, score=1.0)
                
                #now get a list of potential persons
                #we create a soundex on the basis of the last name of the person
                combined_name = ' '.join([n.guess_geslachtsnaam() or n.volledige_naam() for n in person.get_names()])
    #            print combined_name
                soundexes = soundexes_nl(combined_name, 
                                         length=-1, 
                                         group=2,
                                         filter_initials=True, 
                                         filter_stop_words=False, #XXX look out withthis: 'koning' and 'heer' are also last names 
                                         filter_custom=TUSSENVOEGSELS + [w.capitalize() for w in TUSSENVOEGSELS], wildcards=False,
                                         )
                
#                logging.info('searching for persons matching any of %s' % soundexes)
                if not soundexes:
                    persons_to_compare = []
                else:
                    persons_to_compare = self.get_persons(any_soundex = soundexes)
                #compute the similarity
                
                #filter out any unwanted categories
                persons_to_compare = [x for x in persons_to_compare if x.status not in [EXCLUDE_THIS_STATUS_FROM_SIMILARITY]]
                
                logging.info('comparing to %s other persons' % len(persons_to_compare))
                
                similarity_computer = Similarity(person, persons_to_compare)
                similarity_computer.compute()
                similarity_computer.sort()
                similar_persons =  similarity_computer._persons
                for p in similarity_computer._persons[:k]:
                    if p.score > minimal_score and self._should_be_in_similarity_cache(person.bioport_id, p.bioport_id, ignore_status=True):
                        self.add_to_similarity_cache(person.bioport_id, p.bioport_id, p.score)
        logging.info('done')
        
    def add_to_similarity_cache(self,bioport_id1, bioport_id2,score):
        with self.get_session_context() as session:
            id1 = min(bioport_id1, bioport_id2)
            id2 = max(bioport_id1, bioport_id2)
            r = CacheSimilarityPersons(bioport_id1=id1, bioport_id2=id2, score=score)
            session.add(r)
            try:
                session.flush()
            except IntegrityError: 
                # this is (probably) a 'duplicate entry', 
                # caused by having already added the relation when we processed item
                # we update the record to reflect the highest score
                session.transaction.rollback()
                r_duplicate = session.query(CacheSimilarityPersons).filter_by(bioport_id1=id1, bioport_id2=id2).one()
                if score > r_duplicate.score:
                    r_duplicate.score = score
        
    def get_most_similar_persons(self, 
        start=0, 
        size=50, 
#        refresh=False, 
        #similar_to=None,
        source_id=None,
        source_id2=None,
        status=None,
        search_name=None,
        bioport_id=None,
        sex=None,
        min_score=None,
        ):
        """return pairs of persons that are similar but not yet identified or defererred
        
        returns:
            a list tuples of the form (score, person1, person2), where score is a real in [0,1] and person1, persons are PErson instances
            the result is ordered descendinly by score
        arguments:
            source_id, source_id2: ids of sources. If one is given, we return tuples where one of the persons has a biography from that source
                if both are given, we return tuples such that both person1 adn person2 ahve a biography among the sources
        """
        session = self.get_session() 
          
        qry = session.query(CacheSimilarityPersons)
        qry = qry.filter(CacheSimilarityPersons.bioport_id1 != CacheSimilarityPersons.bioport_id2)

        if bioport_id:
            qry = qry.filter(or_(CacheSimilarityPersons.bioport_id1 == bioport_id, CacheSimilarityPersons.bioport_id2==bioport_id))
        
        
        source_ids = filter(None, [source_id, source_id2])
        if source_ids:
            qry = qry.join((
                RelBioPortIdBiographyRecord, 
                 RelBioPortIdBiographyRecord.bioport_id==CacheSimilarityPersons.bioport_id1,
            ))
            qry = qry.join((BiographyRecord, 
                   BiographyRecord.id ==RelBioPortIdBiographyRecord.biography_id,
                   ))
#            qry = qry.filter(RelBioPortIdBiographyRecord.biography.source_id==source_id)
            RelBioPortIdBiographyRecord2 = aliased(RelBioPortIdBiographyRecord)
            qry = qry.join((
                RelBioPortIdBiographyRecord2, 
                 RelBioPortIdBiographyRecord2.bioport_id==CacheSimilarityPersons.bioport_id2,
            ))
            BiographyRecord2 = aliased(BiographyRecord)
            qry = qry.join((BiographyRecord2, 
                   BiographyRecord2.id ==RelBioPortIdBiographyRecord2.biography_id,
                   ))
            if len(source_ids) == 1:
                qry = qry.filter(or_(
                    BiographyRecord.source_id.in_(source_ids),
                    BiographyRecord2.source_id.in_(source_ids)
                    ))
            else:
                qry = qry.filter(and_(
                    BiographyRecord.source_id.in_(source_ids),
                    BiographyRecord2.source_id.in_(source_ids)
                    ))
                
        if search_name or sex or status:
            qry = qry.join((PersonRecord, 
               PersonRecord.bioport_id==CacheSimilarityPersons.bioport_id1
                ))
            PersonRecord2 = aliased(PersonRecord)
            qry = qry.join((PersonRecord2, 
                    PersonRecord2.bioport_id==CacheSimilarityPersons.bioport_id2
                 ))
        if search_name:
            qry = self._filter_search_name(qry, search_name)         
            
        if sex:
            qry = qry.filter(or_(PersonRecord.sex==sex, PersonRecord2.sex==sex))
        
        if status:
            qry = qry.filter(or_(PersonRecord.status==status, PersonRecord2.status == status))
        
        if min_score:
            qry = qry.filter(CacheSimilarityPersons.score > min_score)   
        
        qry = qry.distinct()
        qry = qry.order_by(desc(CacheSimilarityPersons.score))
        qry = qry.order_by(CacheSimilarityPersons.bioport_id1)
        if size:
            qry = qry.slice(start, start + size)
        else:
            qry = qry.slice(start, start + size)
        ls = [(r.score, Person(r.bioport_id1, repository=self.repository, score=r.score), Person(r.bioport_id2, repository=self, score=r.score)) for r in session.execute(qry)]
        return ls

    def _should_be_in_similarity_cache(self, bioport_id1, bioport_id2,
        ignore_status = False,
        ): 
        if self.is_antiidentified(bioport_id1, bioport_id2):
            return False
        #remove is_deferred
        elif self.is_deferred(bioport_id1, bioport_id2):
            return False
        #remove redirected items
        elif self.redirects_to(bioport_id1) != bioport_id1:
            return False
        elif self.redirects_to(bioport_id2) != bioport_id2:
            return False
        #remove items that are  
        elif not ignore_status:
            p1 = self.get_person(bioport_id1, self.repository)
            p2 = self.get_person(bioport_id2, self.repository)
            #(5, 'moeilijk geval (troep)'),
            #(7, 'te weinig informatie'), 
            #(8, 'familielemma'), 
            #(9, 'verwijslemma'), 
            if p1.status in EXCLUDE_THIS_STATUS_FROM_SIMILARITY:
                return False
            if p2.status in EXCLUDE_THIS_STATUS_FROM_SIMILARITY:
                return False
        return True
        
    def identify(self, person1, person2):    
        """identify person1 and person2
        
        arguments:
            person1, person2 - instances of Person
        returns:
            a Person instance - representing the identified person
        """
        #we need to merge the two persons, and choose one as the one to "point to"
        #we take the one that uses a biography with the highest trusworthiness
        trust1 = max([bio.get_source().quality for bio in person1.get_biographies() if bio.get_source().id != 'bioport']  + [0])
        trust2 = max([bio.get_source().quality for bio in person2.get_biographies() if bio.get_source().id != 'bioport']  + [0])
       
        if trust1 > trust2:
            new_person = person1
            old_person = person2
        else:
            new_person = person1
            old_person = person2

        new_id = new_person.bioport_id
        old_id = old_person.bioport_id
        
        if new_person.bioport_id == old_person.bioport_id:
            #these two persons are already identified
            return new_person
            
        #create a new 'merged biography' to add to the new person
        bio1 = self.repository.get_bioport_biography(new_person, create_if_not_exists=False)
        bio2 = self.repository.get_bioport_biography(old_person, create_if_not_exists=False)
        if bio1 and bio2:
            merged_bio = BiographyMerger.merge_biographies(bio1, bio2)
        else:
            merged_bio = None
            
        #now attach all biographies to the new bioportid
#        for bio in new_person.get_biographies() + old_person.get_biographies(): 
        for bio in old_person.get_biographies(): 
            new_person.add_biography(bio,
                comment='Identified %s and %s: added biography %s to %s' % (person1.name(), person2.name(), bio, new_person),
                )
        
        if merged_bio:
            new_person.add_biography(merged_bio, 
                comment='Identified %s and %s: added merged biography to %s' % (person1.name(), person2.name(), new_person)
                )
       
                 
        #mege the bioport biographies in the new person
        #XXX Uncomment when merge_bioport_biographies is well tested
#        new_person.merge_bioport_biographies()
        #if we have different bioport biographies, we need to choose one
        
        #changhe de bioportid table
        self.redirect_identifier(old_person.get_bioport_id(), new_person.get_bioport_id())
        
        #we identified so we can remove this pair from the deferred list
        self._remove_from_cache_deferidentification(new_person, old_person)
        self._remove_from_cache_similarity_persons(old_person)
        
        #now delete the old person from the Person table
        self.delete_person(old_person)
        
        self.update_person(new_person.get_bioport_id() )
       
        return new_person 

              
    def find_biography_contradictions(self):
        """Populate person.has_contradictions column of the db.
        Return the number of persons which have contradictory biographies.
        """
        with self.get_session_context() as session:
            persons = self.get_persons()
            total = len(persons)
            n = 0
            for index, person in enumerate(persons):
                logging.info("progress %s/%s" % (index + 1, total))
                query = session.query(PersonRecord)
                query = query.filter(PersonRecord.bioport_id==person.get_bioport_id())
                obj = query.one()
                if person.get_biography_contradictions():
                    n += 1
                    obj.has_contradictions = True
                else:
                    obj.has_contradictions = False
            return n
                   
    def antiidentify(self, person1, person2):
        """register the fact that the user thinks that these two persons are not the same"""
        id1, id2 = person1.get_bioport_id(), person2.get_bioport_id()       
        # add a witness record to the antiidentify table
        r_anti = AntiIdentifyRecord(bioport_id1 = min(id1, id2),bioport_id2= max(id1, id2)) 
        
        # XXX - this should be adjusted by checking if the record
        # exists first, in which case this is not executed.
        with self.get_session_context() as session:
            try:
                session.add(r_anti)
                msg = 'Anti-identified %s and %s' % (id1, id2)
                self.log(msg, r_anti)
                session.flush()
            except IntegrityError: 
                # this is (most probably) because the record already exists
                session.rollback()

        self._remove_from_cache_similarity_persons(person1, person2)
        self._remove_from_cache_deferidentification(person1, person2)

    def _remove_from_cache_deferidentification(self, person1, person2):
        # remove the persons from the "deferred" lists if they are there
        with self.get_session_context() as session:
            id1 = person1.get_bioport_id()
            id2 = person2.get_bioport_id()
            qry = session.query(DeferIdentificationRecord) 
            qry = qry.filter(DeferIdentificationRecord.bioport_id1==min(id1, id2))
            qry = qry.filter(DeferIdentificationRecord.bioport_id2==max(id1, id2))
            qry.delete()
        
    def _remove_from_cache_similarity_persons(self, person1, person2=None):
        #also remove the person  from the cache
        with self.get_session_context() as session:
            if person2:
                id1 = person1.get_bioport_id()
                id2 = person2.get_bioport_id()
                qry = session.query(CacheSimilarityPersons)
                qry = qry.filter(CacheSimilarityPersons.bioport_id1 == min(id1, id2))
                qry = qry.filter(CacheSimilarityPersons.bioport_id2 == max(id1, id2))
                qry.delete()        
            else:
                id1 = person1.get_bioport_id()
                qry = session.query(CacheSimilarityPersons)
                qry = qry.filter(or_(
                     CacheSimilarityPersons.bioport_id1 == id1,
                     CacheSimilarityPersons.bioport_id2 == id1)
                     )
                qry.delete()        
                
        
    def get_antiidentified(self):
        query = self.get_session().query(AntiIdentifyRecord)
        return query.all()
    
    def is_antiidentified(self, person1, person2):
        """return True if these two persons are on the 'anti-identified' list"""
        qry = self.get_session().query(AntiIdentifyRecord)
        if  isinstance(person1, Person):
            id1 = person1.get_bioport_id()
        else:
            id1 = person1
        if  isinstance(person2, Person):
            id2 = person2.get_bioport_id()
        else:
            id2 = person2
        qry = qry.filter(AntiIdentifyRecord.bioport_id1 == min(id1, id2))
        qry = qry.filter(AntiIdentifyRecord.bioport_id2 == max(id1, id2))
        
        if qry.count():
            return True
        else:
            return False
        
    def is_deferred(self, person1, person2):
        qry = self.get_session().query(DeferIdentificationRecord)
        if  isinstance(person1, Person):
            id1 = person1.get_bioport_id()
        else:
            id1 = person1
        if  isinstance(person2, Person):
            id2 = person2.get_bioport_id()
        else:
            id2 = person2
        qry = qry.filter(DeferIdentificationRecord.bioport_id1 == min(id1, id2))
        qry = qry.filter(DeferIdentificationRecord.bioport_id2 == max(id1, id2))
        
        if qry.count():
            return True
        else:
            return False
        
    def get_identified(self, **args):
        """get all persons that have been identified (with other persons)
        
        what we really want is the "canonical" ids of the persons that have been identified
        (not the ones that are redirecting to others, as we have now)
        """
        return self.get_persons(is_identified=True, **args)
        
    def defer_identification(self, person1, person2): 
        """register the fact that the user puts this pair at the "deferred  list """
        id1, id2 = person1.get_bioport_id(), person2.get_bioport_id()
        session = self.get_session()
        
        with self.get_session_context() as session:
            r_defer = DeferIdentificationRecord(bioport_id1 = min(id1, id2),bioport_id2= max(id1, id2)) 
            try:
                session.add(r_defer)
                msg = 'Deferred identification of %s and %s' % (id1, id2)
                self.log(msg, r_defer)
                session.flush()
            except IntegrityError:
                # this is (most probably) because the record already exists 
                session.rollback()
        
        #also remove the persons from the cache
        self._remove_from_cache_similarity_persons(person1, person2)
        
    def get_deferred(self):
        qry = self.get_session().query(DeferIdentificationRecord)
        qry = qry.filter(DeferIdentificationRecord.bioport_id1 !=DeferIdentificationRecord.bioport_id2)
        return qry.all()
    
    
    #### LOCATIONS ######
    def _update_geolocations_table(self, limit=-1):
        from geolocations import refill_geolocations_table
        this_dir = os.path.dirname(__file__)
        source_fn = os.path.join(this_dir, 'geografische_namen', 'nl.txt')
        refill_geolocations_table(source_fn=source_fn, session=self.get_session(), limit=limit)
        
    
    def get_locations(self, name=None, startswith=None, order_by='sort_name'):
        qry = self.get_session().query(Location)
        if order_by:
            qry = qry.order_by('sort_name')
        if name:
            qry = qry.filter(Location.full_name == name)
        elif startswith:
            qry = qry.filter(Location.sort_name.startswith(startswith))
            
        return qry.all() 
    
    #### OCCUPATIONS #####
    def _update_occupations_table(self):
        from occupations import fill_occupations_table
        self.metadata.create_all()
        fill_occupations_table(self.get_session())
      
    def get_occupations(self):
        qry = self.get_session().query(Occupation)
        return qry.all()
    
    def get_occupation(self,id):
        qry = self.get_session().query(Occupation).filter(Occupation.id==id)
        return qry.one()
        
    #### RUBRIEKEN ####
    def _update_category_table(self):
        from categories import fill_table
        self.metadata.create_all()
        fill_table(self.get_session())
      
    def get_categories(self):
        qry = self.get_session().query(Category)
        return qry.all()
    
    def get_places(self, place_type=None):
        """ Get all places from the database.
            If place_type is either 'sterf' or 'geboorte' it will only
            return death or birth places.
        """
        col_geboorte = PersonRecord.geboorteplaats.label('plaats')
        col_sterf = PersonRecord.sterfplaats.label('plaats')
        select = sqlalchemy.sql.expression.select
        geboorte_query = select([col_geboorte]).where(
            col_geboorte != None).distinct()
        sterf_query = select([col_sterf]).where(
            col_sterf != None).distinct()
        if place_type and place_type in ('sterf', 'geboorte'):
            if place_type == 'sterf':
                query = sterf_query
            elif place_type == 'geboorte':
                query = geboorte_query
        else:
            query = geboorte_query.union(sterf_query)
        query = query.order_by('plaats')
        session = self.get_session()
        results = session.execute(query).fetchall()
        return [el[0] for el in results]

    
    def get_category(self,id):
        qry = self.get_session().query(Category).filter(Category.id==id)
        try:
            return qry.one()
        except NoResultFound:
            msg =  'No category with id "%s" could be found' % id
            logging.warning(msg) 
    
    def get_log_messages(self, table=None, user=None, order_by='timestamp', order_desc=True):
        qry = self.get_session().query(ChangeLog)
        if table:
            qry = qry.filter(ChangeLog.table==table)
        if user:
            qry = qry.filter(ChangeLog.user==user)
        if order_by:
            if order_desc:
                qry = qry.order_by(sqlalchemy.desc(order_by))
            else:
                qry = qry.order_by(order_by)
            
        ls = qry.all()      
        
        return ls
        
    
    def log(self, msg, record, user=None):
        """write information abut the changed record to the log
        
        arguments:
            msg - a string
            record - any Table instance
            user - optional - a string
        
        NOTE:
            does not commit
        """
        if user is None: 
            user = self.user
            
        r = ChangeLog()
        r.user = user
        r.msg = msg
        r.table = record.__tablename__ 
        if hasattr(record, 'id'):
            id = record.id
        elif hasattr(record, 'bioport_id'):
            id = record.bioport_id
        else:
            id = None
#            assert 0, 'This record %s has no "id" or "bioport_id" column defined'  % record
        if type(id) == type(0):
            r.record_id_int = id
        else:
            r.record_id_str = id
        self.get_session().add(r)
    
    def get_comments(self, bioport_id):
        return self.get_session().query(Comment).filter(Comment.bioport_id==bioport_id)

    def add_comment(self, bioport_id, values):
        comment = Comment(**values)
        comment.created = datetime.now()
        self.get_session().add(comment)
        
    def get_persons_with_identical_dbnl_ids(self, start=0, size=20, refresh=False, source=None):
        session = self.get_session() 
        sql = """SELECT  SQL_CALC_FOUND_ROWS c.bioport_id1, c.bioport_id2, c.source1, c.source2, c.dbnl_id
        FROM dbnl_ids c 

LEFT OUTER JOIN antiidentical a
on 
    a.bioport_id1 =  c.bioport_id1
AND a.bioport_id2 = c.bioport_id2
LEFT OUTER JOIN defer_identification d
on 
    d.bioport_id1 =  c.bioport_id1
AND d.bioport_id2 = c.bioport_id2
LEFT OUTER JOIN
     bioportid b 
ON 
b.bioport_id = c.bioport_id1 and b.redirect_to = c.bioport_id2
LEFT OUTER JOIN
     bioportid b2
ON 
b2.bioport_id = c.bioport_id2 and b2.redirect_to = c.bioport_id1

WHERE 
c.bioport_id1 != c.bioport_id2 /*different persones */
and a.bioport_id1 is null /* not antiidentical */ 
and a.bioport_id2 is null
and d.bioport_id1 is null /*not deferred */ 
and d.bioport_id2 is null
and b.bioport_id is null /* not redirected to others */
and b.redirect_to is null
and b2.bioport_id is null /* not redirected to others */
and b2.redirect_to is null
        """
        if source:
            sql += ' AND c.source1 ="%s"  and c.source2="%s"' % (source, source)
        
        sql += ' ORDER BY c.dbnl_id'
        
        sql += ' LIMIT %s OFFSET %s' % (size, start)
        rs = session.execute(sql)
        grand_total = list(session.execute("select FOUND_ROWS()"))[0][0]
        return ([(Person(r.bioport_id1, repository=self), Person(r.bioport_id2, repository=self)) for r in rs], grand_total)

    def tmp_fixup_category_doublures(self):
        """cleanup after a bug that assigned double categories to persons
        
        this method can be removed when it is not useful anymore """
        
        for person in self.get_persons():
            ls = self.get_biographies(source='bioport', person=person)
            if not ls:
                continue
            bio = ls[0] 
            used_ids = [state.get('idno') for state in bio.get_states(type='category')]
            #check if useD_ids has doubles
            if len(set(used_ids)) != len(used_ids):
                used_ids = list(set(used_ids))
                bio.set_category(used_ids)
                self.save_biography(bio, comment='cleanup up admin')
        print 'DONE tmp_fixup_category_doublures'

    def get_versions(self, 
        amount=100, 
        user=None, 
        time_from=None, 
        time_to=None, 
        bioport_id=None,
        document_id=None,
        source_id=None,
        version=None,
        ):
        """get the amount of last changes
        
        returns:
            a list of Change objects
        """
        biographies = self.get_biographies(
            source_id=source_id,
            bioport_id=bioport_id,
            local_id=document_id,
            order_by='version',
            version=version,
            limit=amount,
            user=user,
            time_from=time_from,
            time_to=time_to,
            
            )
        return [Version(biography=bio,) for bio in biographies]
   
    def undo_version(self, document_id, version): 
        """"Make the version before the one identified by document_id and version the most current version
        
        arguments:
           document_id : a string
           version  : an integer
               document_id and version togehter uniquely identify a record in BiographyRecord table
               raises an error if such a version is not found
                    
        """
        versions = self.get_versions(document_id=document_id, version=version+1)
        assert versions
        self.repository.save_biography(versions[0].biography, comment='restored version of  %s' % versions[0].time or '[before versioning]')
        
    def unidentify(self, person):
        """Create a new person for each biography associated with person.
       
        returns:
            the new persons
        """
        bios = person.get_biographies()
        result = []
        if len(bios) == 1:
            return [person]
       
        used_ids = []
       
        for bio in bios:
            if bio.get_source().id == 'bioport':
                #we delete the bioport biographies
                self.delete_biography(bio)
            else:
                original_bioport_id = bio.get_idnos(type='bioport')[0]
                #print '1:',  original_bioport_id
                #the next three lines are there only because in a previous version, bioport_ids were not 'remembered
                if original_bioport_id in used_ids:
                    original_bioport_id = self.fresh_identifier()
                used_ids.append(original_bioport_id)
                
                #save the changes to the biography
                bio.set_value('bioport_id',original_bioport_id)
                self.save_biography(bio, 
                    user=self.user, 
                    comment='unidentified %s' % person,
                    )
               
                #remove the 'redirect' instruction from this bioport id (if there was one)
                self.redirect_identifier(bioport_id=original_bioport_id, redirect_to=None)
               
                #create a new person
                new_person = Person(bioport_id=original_bioport_id)
                new_person.repository = self.repository
                new_person.add_biography(bio)
                self.repository.save_person(new_person)
                result.append(new_person)
               
        return result                

    def detach_biography(self, biography):
        """detach the biography from the person -- i.e. create a new person for this biography"""
        #detaching a biography from a person only makes sense if this person has more than one biography
        
        if not len(self.get_biographies(bioport_id = biography.get_person().bioport_id)) > 1:
            raise Exception('Cannot detach biography %s form person %s, because this person only has one attached biography' % (biography, biography.get_person()))
        new_person = Person(bioport_id=self.fresh_identifier())
        new_person.repository = self.repository
        biography.get_person()
        comment = 'Detached biography %s from person %s and create new person %s' % (biography, biography.get_person(), new_person)
        new_person.add_biography(biography, comment=comment)
        self.repository.save_person(new_person)
        return new_person