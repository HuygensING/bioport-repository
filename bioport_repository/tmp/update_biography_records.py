from bioport_repository.repository import *

DB_CONNECTION = 'mysql://root@localhost/bioport'
"""
ALTER TABLE `bioport`.`biography` ADD COLUMN `url_biography` varchar(255)  CHARACTER SET utf8 COLLATE utf8_general_ci AFTER `comment`;
ALTER TABLE `bioport`.`biography` ADD INDEX `ix_url_biography`(`url_biography`);

"""


#UPDATE ONLU THOSE WITHOUT INFO!

def update_biographies(repo):

    for bio in repo.get_biographies(limit=10):
        print bio

        if not bio.record.url_biography:
	        repo.save_biography(bio, comment=u'update new field url_biography')
#        if 'bioport' in [s.id for s in person.get_sources()]:
#            print 'SET'
#            person.status = 2
#            repo.save_person(person)

if __name__ == "__main__":

    repo = Repository(db_connection=DB_CONNECTION) 
    update_biographies(repo)