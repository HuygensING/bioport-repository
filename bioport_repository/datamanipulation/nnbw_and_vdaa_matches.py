#!/usr/bin/env python

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


import sqlalchemy

from bioport_repository.db_definitions import DBNLIds
from bioport_repository.repository import Repository


base_url_nnbw = 'http://www.inghist.nl/media/bioport/bronnen/nnbw/bio'
base_url_vdaa = 'http://www.inghist.nl/media/bioport/bronnen/vdaa/bio'
base_url_nnbw = 'file:///home/jelle/projects_active/nnbw/bioport/output/bio'
base_url_vdaa = 'file:///home/jelle/projects_active/vdaa/bioport/output/bio'


def create_dictionary(repository, source, limit):
    bios = repository.get_biographies(source=source, limit=limit)
    
    d = {}
    i = 0
    for bio in bios:
        i += 1
        if i > limit: 
            break
        dbnl_id = bio.get_idno('dbnl_id')
        bio_id = bio.get_idno('id')
        
        if dbnl_id in d:
            d[dbnl_id].append(bio_id)
        else:
            d[dbnl_id] = [bio_id]
            
        try:
            print i, dbnl_id
        except:
            print i
    return d 

def create_list_of_doubles(repository, limit):
    errors = {}
    print 'create list of dbnl ids used in nnbw'
    nnbw_ids = create_dictionary(repository, 'nnbw', limit=limit)
    print 'done!'
    print 'create list of dbnl ids used in vdaa'
    vdaa_ids = create_dictionary(repository, 'vdaa', limit=limit)
    print 'done!'
    
    #merge the two dictionarys
    new_d = {} 

    for id in vdaa_ids:
        new_d[id] = vdaa_ids[id]
    for id in nnbw_ids:
        new_d[id] = new_d.get(id, []) + nnbw_ids[id]
   
    for d in new_d:
        if len(new_d[d]) > 1:
            bio_ids = new_d[d]
            if len(bio_ids) > 4:
                #here somethign really went wrong
                if d not in errors:
                    errors[d] = bio_ids
            while bio_ids:
                bio_id, bio_ids = bio_ids[0], bio_ids[1:4]
                for bio_id2 in bio_ids:
                    yield (d, bio_id, bio_id2)
                    
    print 'HERE SOMETHING REALLY WENT WRONG'
    print len(errors), 'errors.... '
    for d in errors:
        bio_ids = errors[d]
        print 'We have %s biographies for the DBNL id %s'  % (len(bio_ids), d) 
        print bio_ids
        
def delete_list_of_doubles(repository):
    session = repository.db.get_session()
    session.query(DBNLIds).delete()
    transaction.commit()
    
def insert_list_of_doubles(repository, limit):    
    session = repository.db.get_session()
    i = 0
    for dbnl_id, local_id1, local_id2 in create_list_of_doubles(repository, limit=limit):
        bio1 = repository.get_biography(local_id=local_id1)
        bio2 = repository.get_biography(local_id=local_id2)
        id1 = bio1.get_bioport_id()
        id2 = bio2.get_bioport_id()
        id1, id2 = min(id1, id2), max(id1,id2)
        session.add(DBNLIds(bioport_id1 = id1, bioport_id2=id2, source1=local_id1.split('/')[0], source2=local_id2.split('/')[0], dbnl_id=dbnl_id))
        try:
            transaction.commit()
            i += 1
            print i, 'added', id1, id2, '(local ids:', local_id1, local_id2, ')'
        except sqlalchemy.exc.IntegrityError:
            print 'this is strange, these ids alreay seem to have been added', id1, id2, local_id1, local_id2
            transaction.abort()
if __name__ == "__main__":
    repository = Repository(
              dsn='mysql://root@localhost/bioport'
               )
    delete_list_of_doubles(repository)
    insert_list_of_doubles(repository, limit=100000) 
            
