#!/usr/bin/env python

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


june21_2012 = """
ALTER TABLE `biography` ADD INDEX `ix_source_version`(`source_id`, `version`);

"""
def upgrade_march2012():
    sql = """ALTER TABLE `person` MODIFY COLUMN `geboortedatum` CHAR(12)  DEFAULT NULL,
 MODIFY COLUMN `sterfdatum` char(12)  DEFAULT NULL;
"""
    
"""

ALTER TABLE `bioport`.`biography` ADD COLUMN `user` varchar(50)  AFTER `timestamp`;
ALTER TABLE `bioport`.`biography` ADD COLUMN `comment` varchar(255)  AFTER `user`;
drop table `bioport`.`cache_similarity`
drop table `bioport`.`comment`
drop table `bioport`.`index_item`
ALTER TABLE `bioport`.`biography` ADD COLUMN `version` int  NOT NULL AFTER `id`,
 DROP PRIMARY KEY,
 ADD PRIMARY KEY (`id`, `version`);
ALTER TABLE `bioport`.`biography` ADD COLUMN `time` DATETIME  AFTER `hide`;

ALTER TABLE `bioport`.`biography` ADD INDEX `ix_time`(`time`),
 ADD INDEX `ix_user`(`user`),
 ADD INDEX `ix_version`(`version`);
ALTER TABLE `bioport`.`biography` DROP INDEX `ix_biography_id`,
 ADD INDEX `ix_biography_id` USING BTREE(`id`);

"""

"""
ALTER TABLE `bioport`.`person` ADD COLUMN `geboortedatum_max` DATETIME DEFAULT NULL,
 ADD COLUMN `sterfdatum_max` DATETIME  DEFAULT NULL,
 ADD COLUMN `geboortedatum_min` DATETIME  AFTER `geboortejaar`,
 ADD COLUMN `sterfdatum_min` DATETIME AFTER `sterfplaats`;

ALTER TABLE `bioport`.`person` DROP INDEX `ix_person_geboortedatum`
, DROP INDEX `ix_person_sterfdatum`,
 ADD INDEX `ix_person_geboortedatum_max` USING BTREE(`geboortedatum_max`),
 ADD INDEX `ix_person_sterfdatum_max` USING BTREE(`sterfdatum_max`),
 ADD INDEX `ix_geboortedatum_min`(`geboortedatum_min`),
 ADD INDEX `sterfdatum_min`(`sterfdatum_min`);

ALTER TABLE `bioport`.`person` DROP COLUMN `geboortejaar`,
 DROP COLUMN `sterfjaar`;

"""
"""
ALTER TABLE `bioport`.`antiidentical` ADD INDEX `bioport_id1`(`bioport_id1`);
ALTER TABLE `bioport`.`defer_identification` ADD INDEX `bioport_id1`(`bioport_id1`);

"""
"""
ALTER TABLE `bioport`.`person_soundex` ADD COLUMN `is_from_family_name` boolean  AFTER `soundex`;
ALTER TABLE `bioport`.`person_name` ADD COLUMN `is_from_family_name` boolean  ;
"""
"""
2009114:
Excute the following querys:

ALTER TABLE `person` MODIFY COLUMN `search_source` TEXT  CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
 ADD COLUMN `remarks` TEXT  AFTER `search_source`;

 ALTER TABLE `person` ADD COLUMN `status` INT  AFTER `search_source`;




"""

"""
ALTER TABLE source ADD COLUMN source_type INT 
"""
#
from bioport_repository.repository import *
#from bioport_repository.db_definitions import PersonView
#repo = Repository(dsn='mysql://localhost/bioport')
#repo.db.metadata.create_all() #repo.db.engine, tables=[PersonView.__tablename__])
#repo.db._update_persons_view()
#

#DSN = 'mysql://root@localhost/bioport_play'
#repo = Repository(dsn=DSN) 
#
#def upgrade_persons(repo):
#    for person in repo.get_persons():
#        print person
#        if 'bioport' in [s.id for s in person.get_sources()]:
#            print 'SET'
#            person.status = 2
#            repo.save_person(person)
#
#def set_everything_without_a_status_to_niet_bewerkt(): 
#    sql = """update person  set person.status = 12  where person.status is null"""        
#    repo.get_session.execute(sql) 
#    
