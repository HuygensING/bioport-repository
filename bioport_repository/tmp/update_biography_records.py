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

from bioport_repository.repository import * #@UnusedWildImport
#
# run as:
# bin/python-console src/bioport_repository/bioport_repository/tmp/update_biography_records.py
#
"""
ALTER TABLE `bioport`.`biography` ADD COLUMN `url_biography` varchar(255)  CHARACTER SET utf8 COLLATE utf8_general_ci AFTER `comment`;
ALTER TABLE `bioport`.`biography` ADD INDEX `ix_url_biography`(`url_biography`);

"""
def get_dsn():
    values = [
        ('1','localhost jelle','mysql://root@localhost/bioport' ),
        ('2','dev', 'mysql://jge:MilanO8@dev.inghist.nl/bioport'),
        ('3','sql (production!)', 'mysql://jelle:MilanO8@sql.inghist.nl/bioport'),
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
                    transaction.commit()
                else:
                    print i, '-not saving - field already filled', bio
        
if __name__ == "__main__":
    dsn = get_dsn()
    print dsn
    repo = Repository(dsn=dsn)
    update_biographies(repo)
