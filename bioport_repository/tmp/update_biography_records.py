from bioport_repository.repository import *
#
# run as:
# bin/python-console src/bioport_repository/bioport_repository/tmp/update_biography_records.py
#
#DB_CONNECTION = 'mysql://root@localhost/bioport'
#DB_CONNECTION = 'mysql://jge:MilanO8@localhost/bioport'
#DB_CONNECTION = 'mysql://jge:MilanO8@sql.inghist.nl/bioport'
"""
ALTER TABLE `bioport`.`biography` ADD COLUMN `url_biography` varchar(255)  CHARACTER SET utf8 COLLATE utf8_general_ci AFTER `comment`;
ALTER TABLE `bioport`.`biography` ADD INDEX `ix_url_biography`(`url_biography`);

"""
def get_dsn():
    values = [
        ('1','localhost jelle','mysql://root@localhost/bioport' ),
        ('2','dev', 'mysql:jge:MilanO8@dev.inghist.nl/bioport'),
        ('3','sql (production!)', 'mysql:jelle:MilanO8@sql.inghist.nl/bioport'),
    ]
    msg = "\n".join(['%s: %s (%s)' % x for x in values])
    answer = raw_input('Choose DSN:\n %s\n' % msg)
    result = [x[2] for x in values if x[0] == answer]
    if result:
        return result[0]
    else:
        raise Exception('Please choose one of the options')

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
                else:
                    print i, '-not saving - field already filled', bio
        
if __name__ == "__main__":

    dsn = get_dsn()
    print dsn
    repo = Repository(db_connection=dsn)
    update_biographies(repo)
