#!/usr/bin/env python

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

"""save all xml files in a BIG ZIP file"""


"""
Run with:
    fab export_data:local


"""
import sys
import codecs
import os
import tarfile
import datetime
from bioport_repository.repository import Repository

DIR_NAME = '/tmp/bioport_export/'
TARFILE_NAME = '/tmp/bioport_export_%s.tar.gz' % unicode(datetime.date.today()).replace(' ', '_')

DSN = 'mysql://root@localhost/bioport'

def export_data(dsn):
    rr = repository = Repository(dsn=dsn)
    if not os.path.exists(DIR_NAME):
        os.makedirs(DIR_NAME)
    for fn in os.listdir(DIR_NAME):
        os.remove(os.path.join(DIR_NAME, fn))

    print 'writing biographies to %s' % DIR_NAME
    persons = repository.get_persons()
    for j, person in enumerate(persons):
        print 'writing %s/%s (of persons)' % (j, len(persons))
        for i, biography in enumerate(person.get_biographies()):
            fn = '%s_%s.xml' % (biography.get_bioport_id(), str(i + 1).zfill(2))
            biography.set_idno(biography.source_id, 'source', where='filedesc')
            codecs.open(os.path.join(DIR_NAME, fn), 'w', 'utf8').write(biography.to_string())


def create_tar_file():
    #create a zip file  

    print 'creating tar.gz'
    tar = tarfile.open(TARFILE_NAME, "w:gz")
    for name in os.listdir(DIR_NAME):
        tar.add(os.path.join(DIR_NAME, name), arcname=name)
    tar.close()
    print 'Output written to ', TARFILE_NAME


if __name__ == "__main__":
    dsn = sys.argv[1]
    export_data(dsn)
    create_tar_file()
