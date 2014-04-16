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

# 
# TODO: drop table person_view; in production db.
#

# BB When making changes to theses classes which would result in a new database scheme,
# be sure to remove data/bioport_mysqldump.sql so it will be regenerated in the tests

from sqlalchemy import Column, Integer, Unicode, ForeignKey, Boolean, UnicodeText, Float, Date
from sqlalchemy import MetaData, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.mysql import VARCHAR as MSString
from sqlalchemy.orm import relation
from sqlalchemy.types import TIMESTAMP

# define the tables

metadata = MetaData()
Base = declarative_base()

# XXX : need next to have metadata.create_all() to work. Cf. also http://stackoverflow.com/questions/20148/myisam-versus-innodb
Base.__table_args__ = {'mysql_engine':'MyIsam'}


class BiographyRecord(Base):
    """represents a version of  biodes document"""
    __tablename__ = 'biography'

    id = Column(MSString(50, binary=True, collation='utf8_bin'), primary_key=True, index=True,)  # the id consist of source_id/local_id
    version = Column(Integer, primary_key=True, default=0, autoincrement=False)
    source_id = Column(MSString(20, collation='utf8_bin'), ForeignKey("source.id"), index=True)
    url_biography = Column(Unicode(255), index=True)  # the url where the biography can be found
    source_url = Column(Unicode(255))  # the url where the biodes_document came from
    biodes_document = Column(Text(64000))

    user = Column(MSString(50))
    time = Column(DateTime)
    comment = Column(Unicode(255), default=u'')
    bioportid = relation('RelBioPortIdBiographyRecord')
    hide = Column(Boolean)
    timestamp = Column(TIMESTAMP)

    def get_bioport_id(self):
        return self.bioportid[0].bioport_id


class SourceRecord(Base):
    __tablename__ = 'source'

    id = Column(MSString(20), index=True, primary_key=True)
    url = Column(MSString(255))
    description = Column(MSString(255), nullable=True)
    quality = Column(Integer)
    xml = Column(Text(64000))
    timestamp = Column(TIMESTAMP)

    def __init__(self, id, url, description, quality=None, xml=None):
        self.id = id
        self.url = url
        self.description = description
        self.quality = quality
        self.xml = xml

#
# NOTA BENE:
#    The tables are not normalized completely.
#    The reason is that the data in the bioportid table needs to be persistent
#    while the data of the biography table in general is not
#
#


class BioPortIdRecord(Base):
    __tablename__ = 'bioportid'
    bioport_id = Column(MSString(50), ForeignKey("bioportid.bioport_id"), primary_key=True)
    redirect_to = Column(MSString(50))
    timestamp = Column(TIMESTAMP)
    biographies = relation('RelBioPortIdBiographyRecord')
    person = relation('PersonRecord')


class RelBioPortIdBiographyRecord(Base):
    __tablename__ = 'relbioportidbiography'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bioport_id = Column(MSString(50), ForeignKey('bioportid.bioport_id'), index=True)
    biography_id = Column(MSString(50, collation='utf8_bin'), ForeignKey("biography.id"), index=True, unique=True)
    timestamp = Column(TIMESTAMP)
    biography = relation(BiographyRecord)
    bioportid = relation(BioPortIdRecord)

class AuthorRecord(Base):
    """XXX the author table serves as a cache and since we mostly look for persons,
    it makes sense to make the relation with the person table directly"""
    __tablename__ = 'author'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(MSString(255), nullable=False, unique=True)
    biographies = relation('RelBiographyAuthorRecord', cascade="all, delete-orphan")

class RelBiographyAuthorRecord(Base):
    __tablename__ = 'relbiographyauthor'
    biography_id = Column(MSString(50, collation='utf8_bin'), ForeignKey('biography.id'), primary_key=True)
    author_id = Column(Integer, ForeignKey('author.id'), primary_key=True)
    author = relation(AuthorRecord, cascade='all')

class SoundexRecord(Base):
    __tablename__ = 'soundex'
    id = Column(Integer, primary_key=True)
    naam_id = Column(Integer, ForeignKey('naam.id'))
    soundex = Column(Unicode(100))


class PersonRecord(Base):
    """This is basically a 'cache' table for searching for persons in the database, together with some meta-data

    The data are a combination of the data from the biographies associated with a bioport id
    """

    __tablename__ = 'person'

    bioport_id = Column(
        MSString(50),
        ForeignKey('bioportid.bioport_id'),
        primary_key=True,
        index=True,
        unique=True,
        )

    geboortedatum_min = Column(Date, index=True)
    geboortedatum_max = Column(Date, index=True)
    sterfdatum_min = Column(Date, index=True)
    sterfdatum_max = Column(Date, index=True)


    geboortedatum = Column(MSString(12), index=True)
    geboorteplaats = Column(MSString(255), index=True)
    sterfdatum = Column(MSString(12), index=True)
    sterfplaats = Column(MSString(255), index=True)
    naam = Column(MSString(255), index=True)
    
    
    geslachtsnaam = Column(MSString(255), index=True)
    names = Column(UnicodeText)
    sort_key = Column(MSString(50), index=True)
    sex = Column(Integer, index=True)
    bioport_id_record = relation(BioPortIdRecord)

    search_source = Column(UnicodeText)
    snippet = Column(UnicodeText)
    remarks = Column(UnicodeText)
    thumbnail = Column(MSString(255))
    status = Column(Integer, index=True)

    has_illustrations = Column(Boolean)
    has_contradictions = Column(Boolean)

    timestamp = Column(TIMESTAMP)

    # BB
    has_name = Column(Boolean, index=True)  # if naam != null && != ''
    birthday = Column(MSString(4), index=True)  # if geboortedatum_min = geboortedatum_max, then extract geboortedag
    deathday = Column(MSString(4), index=True)
    initial = Column(MSString(1), index=True)  # eerste letter van naam
    invisible = Column(Boolean, index=True)  # person.status IN (11, 5, 9, 9999, 14, 15)
    orphan = Column(Boolean, index=True)  # person is orphan when the only source linking to it is 'bioport' 
    # /BB


class PersonSoundex(Base):
    __tablename__ = 'person_soundex'
    id = Column(Integer, primary_key=True)
    bioport_id = Column(MSString(50), ForeignKey('person.bioport_id'), index=True,)
    soundex = Column(Unicode(20), index=True)
    is_from_family_name = Column(Boolean)


class PersonName(Base):
    __tablename__ = 'person_name'
    id = Column(Integer, primary_key=True)
    bioport_id = Column(MSString(50), ForeignKey('person.bioport_id'), index=True,)
    name = Column(Unicode(20), index=True)
    is_from_family_name = Column(Boolean)


class PersonSource(Base):
    __tablename__ = 'person_source'
    bioport_id = Column(MSString(50), ForeignKey('person.bioport_id'), primary_key=True)
    source_id = Column(Unicode(20), primary_key=True)
#    bioport_id = Column(MSString(50), ForeignKey('person.bioport_id'), index=True, primary_key=True)
#    source_id = Column(Unicode(20), index=True, primary_key=True)

class NaamRecord(Base):
    __tablename__ = 'naam'  
    id = Column(Integer, primary_key=True)

    soundex = relation(SoundexRecord)  # , backref="naam.id")
    sort_key = Column(Unicode(100))
    snippet = Column(UnicodeText)
    birth = Column(Unicode(10))
    death = Column(Unicode(10))
    url = Column(Unicode(255))
    src = Column(Unicode(255))
    xml = Column(UnicodeText)
    volledige_naam = Column(Unicode(255))
    url_description = Column(UnicodeText)
    territoriale_titel = Column(Unicode(255))
    variant_of = Column(Integer, ForeignKey('naam.id'))
    varianten = relation("NaamRecord")
    variant_of_record = relation("NaamRecord",
             remote_side="NaamRecord.id",
             )
    bioport_id = Column(MSString(50), ForeignKey('person.bioport_id'), index=True)
    person = relation(PersonRecord,
                         lazy=False,  # load eagerly
                         )
#    sqlalchemy.schema.ForeignKeyConstraint(['id'], ['soundex.naam_id'], ondelete="CASCADE")

class SimilarityCache(Base):
    __tablename__ = 'cache_similarity'
    naam1_id = Column(Integer, ForeignKey('naam.id'), index=True, primary_key=True, autoincrement=False)
    naam2_id = Column(Integer, ForeignKey('naam.id'), index=True, primary_key=True, autoincrement=False)
    score = Column(Float, index=True)
SimilarityCache.naam1 = relation(NaamRecord, primaryjoin=NaamRecord.id == SimilarityCache.naam1_id)
SimilarityCache.naam2 = relation(NaamRecord, primaryjoin=NaamRecord.id == SimilarityCache.naam2_id)

class CacheSimilarityPersons(Base):
    __tablename__ = 'cache_similarity_persons'
    bioport_id1 = Column(MSString(50), ForeignKey('bioportid.bioport_id'), index=True, primary_key=True, autoincrement=False)
    bioport_id2 = Column(MSString(50), ForeignKey('bioportid.bioport_id'), index=True, primary_key=True, autoincrement=False)
    score = Column(Float, index=True)

class AntiIdentifyRecord(Base):
    __tablename__ = 'antiidentical'
    bioport_id1 = Column(MSString(50),
                        ForeignKey('bioportid.bioport_id'),
                        primary_key=True)
    bioport_id2 = Column(MSString(50),
                        ForeignKey('bioportid.bioport_id'),
                        primary_key=True)

    timestamp = Column(TIMESTAMP)

class DeferIdentificationRecord(Base):
    __tablename__ = 'defer_identification'
    bioport_id1 = Column(MSString(50),
                        ForeignKey('bioportid.bioport_id'),
                        primary_key=True)
    bioport_id2 = Column(MSString(50),
                        ForeignKey('bioportid.bioport_id'),
                        primary_key=True)
    timestamp = Column(TIMESTAMP)
    timestamp = Column(TIMESTAMP)


class Location(Base):
    __tablename__ = 'location'
    id = Column(Integer, primary_key=True, autoincrement=True)
    ufi = Column(Integer)
    uni = Column(Integer)
    long = Column(Float)
    lat = Column(Float)
    adm1 = Column(MSString(2), index=True)
    sort_name = Column(MSString(100), index=True)
    full_name = Column(MSString(100), index=True)  #


    """
NL.00    Netherlands (general)
NL.01    Provincie Drenthe
NL.02    Provincie Friesland
NL.03    Gelderland
NL.04    Groningen
NL.05    Limburg
NL.06    North Brabant
NL.07    North Holland
NL.09    Utrecht
NL.10    Zeeland
NL.11    South Holland
NL.15    Overijssel
NL.16    Flevoland
"""
    provinces = {
        '00':'Netherlands (general)',
		'01':'Drenthe',
		'02':'Friesland',
		'03':'Gelderland',
		'04':'Groningen',
		'05':'Limburg',
		'06':'Noord Brabant',
		'07':'Noord Holland',
		'09':'Utrecht',
		'10':'Zeeland',
		'11':'Zuid Holland',
		'15':'Overijssel',
		'16':'Flevoland',
        }
    def province(self):
        return self.provinces[self.adm1]

class Occupation(Base):
    __tablename__ = 'occupation'
    id = Column(Integer, primary_key=True)
    name = Column(MSString(100), index=True)  # *   

class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(MSString(100), index=True)  # *      

class ChangeLog(Base):
    __tablename__ = 'changelog'
    id = Column(Integer, primary_key=True)
    table = Column(MSString(50), index=True)
    record_id_int = Column(Integer, index=True)
    record_id_str = Column(MSString(255), index=True)
    msg = Column(Text)
    user = Column(MSString(50))
    timestamp = Column(TIMESTAMP)

class DBNLIds(Base):
    """this is a temporary class used for identifying vdaa and nnbw entries"""
    __tablename__ = 'dbnl_ids'
    bioport_id1 = Column(MSString(50), ForeignKey('bioportid.bioport_id'), index=True, primary_key=True, autoincrement=False)
    bioport_id2 = Column(MSString(50), ForeignKey('bioportid.bioport_id'), index=True, primary_key=True, autoincrement=False)
    source1 = Column(MSString(5))
    source2 = Column(MSString(5))
    dbnl_id = Column(MSString(20))
    score = Column(Float, index=True)

class RelPersonCategory(Base):
    __tablename__ = 'relpersoncategory'
#     id = Column(Integer, primary_key=True, autoincrement=True)
    bioport_id = Column(Integer, ForeignKey('person.bioport_id'), primary_key=True)
    category_id = Column(Integer, ForeignKey('category.id'), primary_key=True)
    persons = relation(PersonRecord, backref='categories')

class RelPersonReligion(Base):
    __tablename__ = 'relpersonreligion'
#     id = Column(Integer, primary_key=True, autoincrement=True)
    bioport_id = Column(Integer, ForeignKey('person.bioport_id'), primary_key=True)
    religion_id = Column(Integer, primary_key=True)  # , ForeignKey('category.id'), index=True)   
    persons = relation(PersonRecord, backref='religions')

class Comment(Base):
    """This table holds comments submitted by portal users
    """
    __tablename__ = 'comment'
    id = Column(Integer, primary_key=True, autoincrement=True)
    bioport_id = Column(
                        MSString(50),
                        ForeignKey('bioportid.bioport_id'),
                        index=True,
                        unique=True,
                        )
    text = Column(Text)
    created = Column(DateTime, index=True)
    submitter = Column(MSString(20), default='Anonymous')
    email = Column(MSString(40))

STATUS_NEW = 1
STATUS_DIFFICULT = 3
STATUS_DONE = 4
STATUS_MESSY = 5
STATUS_REFERENCE = 9
STATUS_NADER_ONDERZOEK = 10
STATUS_FOREIGNER = 11
STATUS_ALIVE = 14
STATUS_NOBIOS = 9999
STATUS_ONLY_VISIBLE_IF_CONNECTED = 15
STATUS_VALUES = [
    (0, '(geen status toegekend)'),
    (STATUS_NEW, 'nieuw'),  #
#    (2, 'bewerkt'), #XXX TO DELETE
    (STATUS_DIFFICULT, 'moeilijk geval'),
#    (STATUS_MESSY, 'moeilijk geval (troep)'), #XXX TO DELETE
    (STATUS_DONE, 'klaar'),
    (7, 'te weinig informatie'),
    (8, 'familielemma'),
    (STATUS_REFERENCE, 'verwijslemma'),
#    (STATUS_NADER_ONDERZOEK, 'nader onderzoek nodig'),  #XXX TO DELETE --> moeilijk geval
    (STATUS_FOREIGNER, 'buitenlands'),
    (12, 'nog niet bewerkt'),
    (13, 'portrait'),
    (STATUS_NOBIOS, 'no external biographies'),
    (STATUS_ALIVE, 'leeft nog'),
    (STATUS_ONLY_VISIBLE_IF_CONNECTED, 'alleen gekoppeld zichtbaar'),
]


RELIGION_VALUES = [
# 'Christelijke hoofdstromingen in Ndl.:
	(1, 'Anglicaans',),
	(2, 'Doopsgezind',),
	(3, 'Gereformeerd',),
	(4, 'Luthers',),
	(5, 'Nederlands hervormd',),
	(6, 'Oud-katholiek',),
	(7, 'Remonstrants',),
	(8, 'Rooms katholiek',),
	(9, 'Vrijzinnig hervormd',),
	(10, 'Waals',),
# 	'Anders, nl.:',
    (None, '-----------'),

#   'Heterodoxe stromingen:
	(11, 'Baptist',),
	(12, 'Collegianten',),
	(13, 'Herrnhutter',),
	(14, 'Jehova\'s getuige',),
	(15, 'Joods',),
	(16, 'Labadist',),
	(17, 'Leger des heils',),
	(18, 'Mormoon',),
	(19, 'Pietistisch',),
	(20, 'Pinksterbeweging',),
	(21, 'Rozenkruiser',),

# 	'Niet-westerse stromingen:
    (None, '-----------'),

	(22, 'Boeddhist',),
	(23, 'Confuciaans',),
	(24, 'Hindoestaans',),
	(25, 'Islamitisch',),
	(26, 'Theosofisch',),
	(27, 'Winti',),

    (None, '-----------'),

# 	Niet-religieuze overtuigingen:

	(28, 'Agnost',),
	(29, 'Antroposoof',),
	(30, 'Holistisch',),
	(31, 'Vrijmetselaar',),

    (None, '-----------'),
	(99, 'Anders...',),
]

CATEGORY_LETTERKUNDE = 7

def strstatus(code):
    """Return the status string corresponding to the status code in
    STATUS_VALUES.
    """
    return dict(STATUS_VALUES)[code]

