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


import transaction
from vdaa_and_nnbw_doubles import doubles
from bioport_repository.repository import * #@UnusedWildImport
from bioport_repository.db import DBNLIds
from sqlalchemy.exc import IntegrityError


DSN = 'mysql://root@localhost/bioport'
repo = Repository(dsn=DSN) 


def identify_doubles(doubles=doubles, repo=repo):
    doubles = doubles.values()
    total = len(doubles)
    i = 0
#    doubles = doubles[:10]
    for ls in doubles:
        #find the biography for each item in the list
        i += 1
        print i, 'of', total, ':', ls
        bios = [repo.get_biography(local_id=id) for id in ls]
        
        #find the person for each biography
        persons = [bio.get_person() for bio in bios]
        #identify the persons
        p1 = persons[0]
        for p2 in persons[1:]:
            print 'identifying', p1, p2
            repo.identify(p1, p2)

def doubles_in_suggestions_list(doubles=doubles, repo=repo):
    doubles = doubles.values()
    total = len(doubles)
    i = 0
#    doubles = doubles[:10]
    for ls in doubles:
        #ls is a list of lcoal ids
        #find the biography for each item in the list
        i += 1
        print i, 'of', total, ':', ls
        bios = [repo.get_biography(local_id=id) for id in ls]
        
        #find the person for each biography
        persons = [bio.get_person() for bio in bios]
        #add to similiarty cache
        p1 = persons[0]
        for p2 in persons[1:]:
            print 'add to similairty cache', p1, p2
            repo.db.add_to_similarity_cache(p1.bioport_id, p2.bioport_id, 1.0)

def update_table_dbnl_ids(doubles=doubles, repo=repo):
    db = repo.db
    session = db.get_session()
    total = len(doubles)
    i = 0
#    doubles = doubles[:10]
    session.query(DBNLIds).delete()
    for dbnl_id in doubles:
        ls = doubles[dbnl_id]
        #ls is a list of lcoal ids
        #find the biography for each item in the list
        i += 1
        print i, 'of', total, '-', dbnl_id, ':', ls
        bios = [repo.get_biography(local_id=id) for id in ls]
        while bios:
            bio = bios[0]
            person = bio.get_person()
            bioport_id = person.bioport_id
            bios = bios[1:]
            for bio1 in bios:
                person1 = bio1.get_person()
                bioport_id1 = person1.bioport_id
                
                id1 = min(bioport_id, bioport_id1)
                id2 = max(bioport_id, bioport_id1)
                print 'add to dbnl_ids',id1, id2
                session.add(DBNLIds(bioport_id1=id1, bioport_id2=id2, source1=bio.source_id, source2=bio1.source_id, dbnl_id=dbnl_id))
                try:
                    transaction.commit()
                except IntegrityError:
                    transaction.abort()
            
                

if __name__ == '__main__':
    update_table_dbnl_ids(doubles)
    
    
