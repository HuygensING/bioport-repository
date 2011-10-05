from bioport_repository.repository import *

DB_CONNECTION = 'mysql://root@localhost/bioport'
DB_CONNECTION = 'mysql://jge:MilanO8@localhost/bioport'
"""
ALTER TABLE `bioport`.`biography` ADD COLUMN `url_biography` varchar(255)  CHARACTER SET utf8 COLLATE utf8_general_ci AFTER `comment`;
ALTER TABLE `bioport`.`biography` ADD INDEX `ix_url_biography`(`url_biography`);
>>>>>>> .r23944

"""


#UPDATE ONLU THOSE WITHOUT INFO!

def update_biographies(repo):

    i = 0
    session = repo.db.get_session()
    for src in repo.get_sources():
      src_id = src.id
      if src_id != 'bioport':
       for bio in repo.get_biographies(limit=None, source_id=src_id):
        i += 1
        if not bio.record.url_biography:
            print i, '-saving', bio
            bio.record.url_biography = bio.get_value('url_biography')
            session.commit()
#            repo.save_biography(bio, comment=u'update new field url_biography')
        else:
            print i, '-not saving - field already filled', bio
#        if 'bioport' in [s.id for s in person.get_sources()]:
#            print 'SET'
#            person.status = 2
#            repo.save_person(person)

if __name__ == "__main__":

    repo = Repository(db_connection=DB_CONNECTION) 
    update_biographies(repo)
