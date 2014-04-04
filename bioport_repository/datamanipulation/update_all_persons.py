
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

"""do a resave on all persons to set the added fields"""

from bioport_repository.repository import Repository

DSN = 'mysql://histest:test@localhost/histest'

def resave_persons(dsn):
    repository = Repository(dsn=dsn)

    print 'resaving persons'
    persons = repository.get_persons(full_records=True, hide_invisible=False, no_empty_names=False)
    print len(persons)
    for j, person in enumerate(persons):
        print 'resaving %s/%s (of persons)' % (j, len(persons))
        person.save()

if __name__ == "__main__":
#     dsn = sys.argv[1]
    resave_persons(DSN)
