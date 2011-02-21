from bioport_repository.repository import Repository
from bioport_repository.db_definitions import  CacheSimilarityPersons, STATUS_DONE, STATUS_NEW, CATEGORY_LETTERKUNDE
LIMIT = 0

"""
Set all RKD artists with status "New" to status "DONE"

USAGE:
dsn = 'mysql://localhost/bioport'
from bioport_repository import  helper_scripts
helper_scripts._set_new_rkdartists_to_done(dsn)

"""
def _set_new_rkdartists_to_done(dsn):
    source_id = 'rkdartists'
    _set_new_persons_to_done(dsn,source_id)

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
    repository = Repository(db_connection=dsn)
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
    repository = Repository(db_connection=dsn)
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
    repository = Repository(db_connection=dsn)
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
    repository = Repository(db_connection=dsn)
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
                session.commit()
        except Exception, error:
            print error
            session.rollback()
    session.commit()
    print 'deleted %s items' % j 
    print 'committing...'
    print 'done.'
 
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
    repository = Repository(db_connection=dsn)
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