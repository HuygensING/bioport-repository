
"""

CREATE TABLE `bioport`.`relpersonreligion` (
  `id` integer  NOT NULL AUTO_INCREMENT,
  `bioport_id` integer  NOT NULL,
  `religion_id` integer  NOT NULL,
  PRIMARY KEY (`id`),
  INDEX `nix_bioport_id`(`bioport_id`),
  INDEX `ix_religion_id`(`religion_id`)
)
"""

"""
2009114:
Excute the following querys:

ALTER TABLE `person` MODIFY COLUMN `search_source` TEXT  CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
 ADD COLUMN `remarks` TEXT  AFTER `search_source`;

 ALTER TABLE `person` ADD COLUMN `status` INT  AFTER `search_source`;


 """
from bioport_repository.repository import Repository
DB_CONNECTION = 'mysql://root@localhost/bioport_play'
repo = Repository(dsn=DB_CONNECTION) 

def upgrade_persons(repo):
    for person in repo.get_persons():
        print person
        if 'bioport' in [s.id for s in person.get_sources()]:
            print 'SET'
            person.status = 2
            repo.save_person(person)
            
            
            
def upgrade_20100115():            
    pass
"""
Delete  from naam;
ALTER TABLE `bioport`.`naam` ADD COLUMN `bioport_id` varchar(50)  NOT NULL AFTER `biography_id`;

ALTER TABLE `bioport`.`naam` ADD INDEX `bioport_id`(`bioport_id`);
ALTER TABLE `bioport`.`naam` DROP COLUMN `biography_id`;
ALTER TABLE `bioport`.`naam` MODIFY COLUMN `volledige_naam` VARCHAR(255) NOT NULL ;
ALTER TABLE `bioport`.`person` MODIFY COLUMN `geboortedatum` VARCHAR(11)  CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
 MODIFY COLUMN `sterfdatum` VARCHAR(11)  CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL;
drop table cache_similarity;
delete from cache_similarity_persons;
"""

"""
delete cache_similarity_persons   FROM cache_similarity_persons  
inner join relbioportidbiography r1
on bioport_id1 = r1.bioport_id
inner join biography b1
on r1.biography_id = b1.id
inner join relbioportidbiography r2
on bioport_id2 = r2.bioport_id
inner join biography b2
on b2.id = r2.biography_id
where b2.source_id = b1.source_id
and bioport_id1 != bioport_id2
"""



"""
ALTER TABLE `bioport`.`person` ADD COLUMN `category` integer  AFTER `search_source`,
 ADD INDEX `ix_person_category`(`category`);
"""

"""
ALTER TABLE `bioport`.`person` ADD COLUMN `has_illustrations` BOOLEAN  AFTER `category`;
"""

"""
ALTER TABLE `bioport`.`person` MODIFY COLUMN `search_source` LONGTEXT  DEFAULT NULL;
"""

"""
ALTER TABLE `bioport`.`person` DROP COLUMN `category`;
"""

"""
ALTER TABLE `bioport`.`person` ADD FULLTEXT INDEX `ix_search_source`(`search_source`);
 """
 
"""
 ALTER TABLE `bioport`.`person` ADD COLUMN `sex` int  AFTER `sterfdatum`;
"""

"""
ALTER TABLE `bioport`.`person` ADD INDEX `ix_sex`(`sex`);
"""

"""
ALTER TABLE `bioport`.`person` ADD COLUMN `birth_place` varchar(255)  AFTER `bioport_id`,
 ADD COLUMN `birth_year` int  AFTER `birth_place`,
 ADD COLUMN `death_year` int  AFTER `geboortedatum`,
 ADD COLUMN `death_place` varchar(255)  AFTER `death_year`,
 ADD COLUMN `names` longtext  AFTER `sex`;
"""

"""
ALTER TABLE `bioport`.`person` CHANGE COLUMN `birth_place` `geboorteplaats` VARCHAR(255)  CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL,
 CHANGE COLUMN `birth_year` `geboortejaar` INTEGER  DEFAULT NULL,
 CHANGE COLUMN `death_year` `sterfjaar` INTEGER  DEFAULT NULL,
 CHANGE COLUMN `death_place` `sterfplaats` VARCHAR(255)  CHARACTER SET latin1 COLLATE latin1_swedish_ci DEFAULT NULL;

"""

"""
ALTER TABLE `bioport`.`person`
add index ix_geboorteplaats (geboorteplaats),
add index ix_geboortejaar (geboortejaar),
add index ix_sterfjaar (sterfjaar),
add index ix_sterfplaats (sterfplaats),
add index ix_names (names)
"""

"""
ALTER TABLE `bioport`.`relpersoncategory` ADD INDEX `ix_uniqueness`(`bioport_id`, `category_id`)
, AUTO_INCREMENT = 47857;
"""
"""
ALTER TABLE `bioport`.`person` ADD COLUMN `geslachtsnaam` varchar(255)  AFTER `naam`,
 ADD COLUMN `snippet` longtext  AFTER `search_source`,
 ADD INDEX `ix_geslachtsnaam`(`geslachtsnaam`);
"""
"""
ALTER TABLE `bioport`.`person` ADD COLUMN `thumbnail` varchar(255)  AFTER `snippet`;
"""
