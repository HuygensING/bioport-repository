# person_source aanpassen
create table person_source_orig like person_source;
insert person_source_orig select * from person_source;
drop table person_source;
create table person_source like person_source_orig;
insert person_source select * from person_source_orig group by bioport_id, source_id;
alter table person_source drop column id, add primary key(bioport_id,source_id);

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

# person uitbreiden
alter table person
  add column has_name tinyint(1) default 1,
  add column birthday varchar(4),
  add column initial varchar(1),
  add column invisible tinyint(1) default 0,
  add column orphan tinyint(1) default 0,
  add key `ix_person_has_name` (`has_name`),
  add key `ix_person_birthday` (`birthday`),
  add key `ix_person_initial` (`initial`),
  add key `ix_person_invisible` (`invisible`),
  add key `ix_person_orphan` (`orphan`);
