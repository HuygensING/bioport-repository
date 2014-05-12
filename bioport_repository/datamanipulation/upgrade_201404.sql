# antiidentical
show create table antiidentical;
select * from antiidentical limit 5;
alter table antiidentical add column bioport_id1_long int(11), add column bioport_id2_long int(11);
update antiidentical set bioport_id1_long = cast(bioport_id1 as unsigned);
update antiidentical set bioport_id2_long = cast(bioport_id2 as unsigned);
select * from antiidentical limit 5;
alter table antiidentical
  drop column bioport_id1,
  drop column bioport_id2, 
  change column bioport_id1_long bioport_id1 int(11) not null,
  change column bioport_id2_long bioport_id2 int(11) not null,
  add primary key (`bioport_id1`,`bioport_id2`),
  add key `ix_cache_antiidentical_bioport_id1` (`bioport_id1`),
  add key `ix_cache_antiidentical_bioport_id2` (`bioport_id2`)
;
show create table antiidentical;
select * from antiidentical limit 5;

# bioportid
show create table bioportid;
select * from bioportid limit 5;
alter table bioportid add column bioport_id_long int(11), add column redirect_to_long int(11);
update bioportid set bioport_id_long = cast(bioport_id as unsigned);
update bioportid set redirect_to_long = cast(redirect_to as unsigned);
select * from bioportid limit 5;
alter table bioportid
  drop column bioport_id,
  drop column redirect_to, 
  change column bioport_id_long bioport_id int(11) not null,
  change column redirect_to_long redirect_to int(11) default null,
  add primary key (`bioport_id`)
;
show create table bioportid;
select * from bioportid limit 5;

#cache_similarity_persons
show create table cache_similarity_persons;
select * from cache_similarity_persons limit 5;
alter table cache_similarity_persons add column bioport_id1_long int(11), add column bioport_id2_long int(11);
update cache_similarity_persons set bioport_id1_long = cast(bioport_id1 as unsigned);
update cache_similarity_persons set bioport_id2_long = cast(bioport_id2 as unsigned);
select * from cache_similarity_persons limit 5;
alter table cache_similarity_persons
  drop column bioport_id1,
  drop column bioport_id2, 
  change column bioport_id1_long bioport_id1 int(11) not null,
  change column bioport_id2_long bioport_id2 int(11) not null,
  add primary key (`bioport_id1`,`bioport_id2`),
  add key `ix_cache_similarity_persons_bioport_id1` (`bioport_id1`),
  add key `ix_cache_similarity_persons_bioport_id2` (`bioport_id2`)
;
select * from cache_similarity_persons limit 5;
show create table cache_similarity_persons;

#comment
show create table comment;
select * from comment limit 5;
alter table comment add column bioport_id_long int(11);
update comment set bioport_id_long = cast(bioport_id as unsigned);
select * from comment limit 5;
alter table comment
  drop column bioport_id,
  change column bioport_id_long bioport_id int(11) not null,
  add unique key `ix_comment_bioport_id` (`bioport_id`)
;
select * from comment limit 5;
show create table comment;

#dbnl_ids
show create table dbnl_ids;
select * from dbnl_ids limit 5;
alter table dbnl_ids add column bioport_id1_long int(11), add column bioport_id2_long int(11);
update dbnl_ids set bioport_id1_long = cast(bioport_id1 as unsigned);
update dbnl_ids set bioport_id2_long = cast(bioport_id2 as unsigned);
select * from dbnl_ids limit 5;
alter table dbnl_ids
  drop column bioport_id1,
  drop column bioport_id2, 
  change column bioport_id1_long bioport_id1 int(11) not null,
  change column bioport_id2_long bioport_id2 int(11) not null,
  add primary key (`bioport_id1`,`bioport_id2`),
  add key `ix_dbnl_ids_bioport_id1` (`bioport_id1`),
  add key `ix_dbnl_ids_bioport_id2` (`bioport_id2`)
;
select * from dbnl_ids limit 5;
show create table dbnl_ids;

#defer_identification
show create table defer_identification;
select * from defer_identification limit 5;
alter table defer_identification add column bioport_id1_long int(11), add column bioport_id2_long int(11);
update defer_identification set bioport_id1_long = cast(bioport_id1 as unsigned);
update defer_identification set bioport_id2_long = cast(bioport_id2 as unsigned);
select * from defer_identification limit 5;
alter table defer_identification
  drop column bioport_id1,
  drop column bioport_id2, 
  change column bioport_id1_long bioport_id1 int(11) not null,
  change column bioport_id2_long bioport_id2 int(11) not null,
  add primary key (`bioport_id1`,`bioport_id2`),
  add key `ix_defer_identification_bioport_id1` (`bioport_id1`),
  add key `ix_defer_identification_bioport_id2` (`bioport_id2`)
;
select * from defer_identification limit 5;
show create table defer_identification;

#naam
show create table naam;
select * from naam limit 5;
alter table naam add column bioport_id_long int(11);
update naam set bioport_id_long = cast(bioport_id as unsigned);
select * from naam limit 5;
alter table naam
  drop column bioport_id,
  change column bioport_id_long bioport_id int(11) not null,
  add key `ix_naam_bioport_id` (`bioport_id`)
;
select * from naam limit 5;
show create table naam;

#person
show create table person;
select * from person limit 5;
alter table person add column bioport_id_long int(11);
update person set bioport_id_long = cast(bioport_id as unsigned);
select * from person limit 5;
alter table person
  drop column bioport_id,
  change column bioport_id_long bioport_id int(11) not null,
  add primary key (`bioport_id`)
;
select * from person limit 5;
show create table person;

# person uitbreiden
alter table person
  add column has_name tinyint(1) default 1,
  add key `ix_person_has_name` (`has_name`),
  add column birthday varchar(4),
  add key `ix_person_birthday` (`birthday`),
  add column deathday varchar(4),
  add key `ix_person_deathday` (`deathday`),
  add column initial varchar(1),
  add key `ix_person_initial` (`initial`),
  add column invisible tinyint(1) default 0,
  add key `ix_person_invisible` (`invisible`),
  add column orphan tinyint(1) default 0,
  add key `ix_person_orphan` (`orphan`);

#person_name
show create table person_name;
select * from person_name limit 5;
alter table person_name add column bioport_id_long int(11);
update person_name set bioport_id_long = cast(bioport_id as unsigned);
select * from person_name limit 5;
alter table person_name
  drop column bioport_id,
  change column bioport_id_long bioport_id int(11) not null,
  add key `ix_person_name_bioport_id` (`bioport_id`)
;
select * from person_name limit 5;
show create table person_name;

#person_soundex
show create table person_soundex;
select * from person_soundex limit 5;
alter table person_soundex add column bioport_id_long int(11);
update person_soundex set bioport_id_long = cast(bioport_id as unsigned);
select * from person_soundex limit 5;
alter table person_soundex
  drop column bioport_id,
  change column bioport_id_long bioport_id int(11) not null,
  add key `ix_person_soundex_bioport_id` (`bioport_id`)
;
select * from person_soundex limit 5;
show create table person_soundex;

# person_source aanpassen
create table person_source_orig like person_source;
insert person_source_orig select * from person_source;
drop table person_source;
create table person_source like person_source_orig;
insert person_source select * from person_source_orig group by bioport_id, source_id;
alter table person_source drop column id, add primary key(bioport_id,source_id);

#person_source
show create table person_source;
select * from person_source limit 5;
alter table person_source add column bioport_id_long int(11);
update person_source set bioport_id_long = cast(bioport_id as unsigned);
select * from person_source limit 5;
alter table person_source
  drop column bioport_id,
  change column bioport_id_long bioport_id int(11) not null,
  add key `ix_person_source_bioport_id` (`bioport_id`)
;
select * from person_source limit 5;
show create table person_source;

#relbioportidbiography
show create table relbioportidbiography;
select * from relbioportidbiography limit 5;
alter table relbioportidbiography add column bioport_id_long int(11);
update relbioportidbiography set bioport_id_long = cast(bioport_id as unsigned);
select * from relbioportidbiography limit 5;
alter table relbioportidbiography
  drop column bioport_id,
  change column bioport_id_long bioport_id int(11) not null,
  add key `ix_relbioportidbiography_bioport_id` (`bioport_id`)
;
select * from relbioportidbiography limit 5;
show create table relbioportidbiography;

# relpersoncategory aanpassen
create table relpersoncategory_orig like relpersoncategory;
insert relpersoncategory_orig select * from relpersoncategory;
drop table relpersoncategory;
create table relpersoncategory like relpersoncategory_orig;
insert relpersoncategory select * from relpersoncategory_orig group by bioport_id, category_id;
alter table relpersoncategory drop column id, add primary key(bioport_id,category_id);

# relpersonreligion aanpassen
create table relpersonreligion_orig like relpersonreligion;
insert relpersonreligion_orig select * from relpersonreligion;
drop table relpersonreligion;
create table relpersonreligion like relpersonreligion_orig;
insert relpersonreligion select * from relpersonreligion_orig group by bioport_id, religion_id;
alter table relpersonreligion drop column id, add primary key(bioport_id,religion_id);

