##########################################################################
# Copyright (C) 2009 - 2014 Huygens ING & Gebrandy S.R.L.
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

from bioport_repository.repository import Repository
from bioport_repository.db_definitions import  CacheSimilarityPersons, STATUS_DONE, STATUS_NEW, CATEGORY_LETTERKUNDE, STATUS_NADER_ONDERZOEK, STATUS_DIFFICULT, RelPersonReligion, PersonRecord
from bioport_repository.illustration import SMALL_THUMB_SIZE
from sqlalchemy.orm.exc import NoResultFound
import os
import transaction

LIMIT = 0
"""
dsn = 'mysql://localhost/bioport'
from bioport_repository import  helper_scripts
helper_scripts.upgrade_march2012(dsn)
"""
def upgrade_march2012(dsn, bioport_id=None, min=None, max=None):

    repository = Repository(dsn=dsn, images_cache_url='http://www.inghist.nl/media/bioport/images/')
    print 'upgrading!'
    if bioport_id:
        persons = repository.get_persons(bioport_id=bioport_id)
    else:
        persons = repository.get_persons()

    for i, person in enumerate(persons):
        if min and i < min:
            continue
        if max and i > max:
            continue
        session = repository.db.get_session()
        r_person = session.query(PersonRecord).filter_by(bioport_id=person.bioport_id).one()
#        r_person = person.record
        computed_values = person.computed_values
        r_person.geboortedatum = computed_values.geboortedatum
        r_person.sterfdatum = computed_values.sterfdatum
        r_person.thumbnail = computed_values.thumbnail
#        if r_person.thumbnail and not os.path.exists(r_person.thumbnail):
#            illustrations =  person.merged_biography.get_illustrations()
#            if illustrations:
#                fn = illustrations[0]._create_thumbnail(*SMALL_THUMB_SIZE)
#                print 'did not find %s' % r_person.thumbnail
#                print 'created %s' % fn 
#            else:
#                r_person.thumbnail = None

        print '[%s/%s] %s (%s-%s) - %s' % (i, len(persons), person, r_person.geboortedatum, r_person.sterfdatum, r_person.thumbnail)
        session.flush()
        transaction.commit()


"""a set of helper scripts to run in bin/bioport-debug"""
"""

dsn = 'mysql://localhost/bioport'
from bioport_repository import  helper_scripts
helper_scripts.update_religion(dsn)
"""
def update_religion(dsn):
    repository = Repository(dsn=dsn)
    session = repository.db.get_session()
    total = repository.count_persons()
    i = 0
    for p in repository.get_persons():
        i += 1
        print '[%s/%s] updating religion' % (i, total)
        #update the religion table
        merged_biography = p.get_merged_biography()
        bioport_id = p.get_bioport_id()
        religion = merged_biography.get_religion()
        religion_qry = session.query(RelPersonReligion).filter(RelPersonReligion.bioport_id == bioport_id)
        if religion is not None:
            religion_id = religion.get('idno')
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


"""update all persons

dsn = 'mysql://localhost/bioport'
from bioport_repository import  helper_scripts
helper_scripts.update_persons(dsn)

"""
def update_persons(dsn, start=None, size=None):
    #show everything
    import logging
    reload(logging)
    logging.basicConfig(level=logging.INFO)
    logging.info('start updating')
    repository = Repository(dsn=dsn)
    repository.db.update_persons(start=start, size=size)

"""Set all status of X to Y
dsn = 'mysql://localhost/bioport'
from bioport_repository import  helper_scripts
helper_scripts._change_states(dsn, status_old=helper_scripts.STATUS_NADER_ONDERZOEK, status_new=helper_scripts.STATUS_DIFFICULT)

"""
def _change_states(dsn, status_old, status_new):
    repository = Repository(dsn=dsn)
    print 'getting persons'
    persons = repository.get_persons(status=status_old)
    i = 0
    for person in persons:
        i += 1
        print '[%s/%s] new status is "done"' % (i, len(persons))
        person.status = status_new
        repository.save_person(person)
    print 'done!'

"""
Set all RKD artists with status "New" to status "DONE"

USAGE:
dsn = 'mysql://localhost/bioport'
from bioport_repository import  helper_scripts
helper_scripts._set_new_rkdartists_to_done(dsn)

"""
def _set_new_rkdartists_to_done(dsn):
    source_id = 'rkdartists'
    _set_new_persons_to_done(dsn, source_id)

def _set_new_dbnlers_to_done(dsn):
    source_id = 'dbnl'
    _set_new_persons_to_done(dsn, source_id)

"""
Set all RKD artists with status "New" to status "DONE"

USAGE:
dsn = 'mysql://localhost/bioport'
from bioport_repository import  helper_scripts
helper_scripts._set_new_dbnlers_to_done(dsn)

"""
def _set_new_persons_to_done(dsn, source_id):
    repository = Repository(dsn=dsn)
    print 'getting persons'
    persons = repository.get_persons(source_id=source_id, status=STATUS_NEW)
    print 'found %s persons' % len(persons)
    i = 0
    for person in persons:
        i += 1
        person.status = STATUS_DONE
        print '[%s/%s] new status is "done"' % (i, len(persons))
        repository.save_person(person)



"""
Set all DNBL with no category the category 'letterkunde'

USAGE:
dsn = 'mysql://localhost/bioport'
from bioport_repository import  helper_scripts
reload(helper_scripts)
helper_scripts._set_dbnl_to_letterkunde(dsn)

"""

def _set_dbnl_to_letterkunde(dsn):
    repository = Repository(dsn=dsn)
    print 'getting persons'
    i = 0
    persons = repository.get_persons(source_id='dbnl')
    for person in persons:
        i += 1
        print '[%s/%s]' % (i, len(persons))
        bio = person.get_bioport_biography()
        if not bio.get_category_ids():
            print 'set category'
            bio.set_category([CATEGORY_LETTERKUNDE])
            repository.save_biography(bio, comment=u'Set category to "letterkunde"')


"""
Set the status of all person with a biography of a certain source

USAGE:
dsn = 'mysql://localhost/bioport'
from bioport_repository.helper_scripts import _set_status_of_persons_in_source
_set_status_of_persons_in_source(dsn, source_id='dbnl')
"""


def _set_status_of_persons_in_source(dsn, source_id, status=STATUS_DONE):
    repository = Repository(dsn=dsn)
    db = repository.db
    bios = db.get_biographies(source_id=source_id)
    i = 0
    for biography in bios:
        i += 1
        person = biography.get_person()
        person.status = STATUS_DONE
        print '[%s/%s]' % (i, len(bios))
        repository.save_person(person)


"""
remove all items fro the similarity table that should not be there to begin with

USAGE:
from bioport_repository.helper_scripts import _remove_irrelevent_items_from_similarity_table
dsn = 'mysql://localhost/bioport'
_remove_irrelevent_items_from_similarity_table(dsn)
"""

def _remove_irrelevent_items_from_similarity_table(dsn):
    repository = Repository(dsn=dsn)
    db = repository.db
    session = db.get_session()
    qry = session.query(CacheSimilarityPersons)
    i = 0
    j = 0
    k = 0
    total = qry.count()
    for r in qry:
        i += 1
        print 'progress %s/%s' % (i, total)
        try:
            if not db._should_be_in_similarity_cache(r.bioport_id1, r.bioport_id2):
                print 'deleting %s form similiaryt cache' % r
                j += 1
                k += 1
                session.delete(r)
                transaction.commit()
        except Exception, error:
            print error
            transaction.abort()
    transaction.commit()
    print 'deleted %s items' % j
    print 'committing...'
    print 'done.'

"""
identify any two persons such that:

    one is from source
    score > score
USAGE:

dsn = 'mysql://localhost/bioport'
from bioport_repository import helper_scripts
helper_scripts.identify_persons(dsn, source_id='pdc', min_score=0.8647)

"""

def identify_persons(dsn, source_id, min_score):
    repository = Repository(dsn=dsn)
    i = 0
    for score, person1, person2 in repository.get_most_similar_persons(source_id=source_id, size=200):
        if score > min_score:
            i += 1
            print i, score, person1, person2
            repository.identify(person1, person2)
        else:
            break

    print 'done (%s persons)' % i

"""
identify any two persons that have dbnl biographies witht he same dbnl id

USAGE:

dsn = 'mysql://localhost/bioport'
from bioport_repository.helper_scripts import identify_dbnl_biographies
identify_dbnl_biographies(dsn)
"""
def identify_dbnl_biographies(dsn):
    """search in the database for all biographies that have an idno of type 'dbnl_id'
       and identify all persons that have the same dbnl_id
    """
    repository = Repository(dsn=dsn)
    #create a dictionary of all dbnl_ids and corresponding bioport_ids
    dct = {}
    def get_bios():
        for source_id in ['dbnl', 'nnbw', 'vdaa']:
            for biography in repository.get_biographies(source=source_id):
                yield biography

    i = 0
    #construct a dictionary dbnl_id --> [bioportids]
    for biography in get_bios():
        i += 1
        print i
        if LIMIT and i > LIMIT:
            break
        dbnl_id = biography.get_idno(type='dbnl_id')
        if dbnl_id and dbnl_id not in ['None']:
            bioport_id = biography.get_bioport_id()
            if bioport_id not in dct.get(dbnl_id, []):
                dct[dbnl_id] = dct.get(dbnl_id, []) + [bioport_id]

    #remove any keys that have just one biograpphy 
    for k in dct.keys():
        if len(dct[k]) < 2:
            del dct[k]

    #now identify any two persons that have the saem dbnl_id
    total = len(dct)
    i = 0
    for dbnl_id in dct:
        i += 1
        print '%s/%s' % (i, total)
        bioport_ids = dct[dbnl_id]
        bioport_id1 = bioport_ids[0]
        person1 = repository.get_person(bioport_id1)
        for bioport_id2 in bioport_ids[1:]:
            person2 = repository.get_person(bioport_id2)
            print 'identifying', person1, person2
            if person1 and person2: #this to avoid a misterious bug that i cannot be bothered to investiage
                if not repository.is_antiidentified(person1, person2):
                    person1 = repository.identify(person1, person2)
            else:
                person1 = person2
        #just to make sure, we set all values to none
        bioport_id1 = bioport_id2 = person1 = person2 = None



#if __name__ == '__main__':
#    DSN ='mysql://localhost/bioport'
#    _set_category_of_dbnl_to_klaar(DSN)
