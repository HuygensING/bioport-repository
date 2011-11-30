from bioport_repository.repository import * #@UnusedWildImport
"""
2009114:
Excute the following querys:

ALTER TABLE `person` MODIFY COLUMN `search_source` TEXT  CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
 ADD COLUMN `remarks` TEXT  AFTER `search_source`;

 ALTER TABLE `person` ADD COLUMN `status` INT  AFTER `search_source`;


 """


DB_CONNECTION = 'mysql://root@localhost/bioport_play'
repo = Repository(db_connection=DB_CONNECTION) 

def upgrade_persons(repo):
    for person in repo.get_persons():
        print person
        if 'bioport' in [s.id for s in person.get_sources()]:
            print 'SET'
            person.status = 2
            repo.save_person(person)
