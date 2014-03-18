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

#
#
# INLEESMODULE GEOGRAFISCHE DATA TBV BIOPORT
#
# gegevens komen van 
#   http://earth-info.nga.mil/gns/html/cntry_files.html
#
# het zijn de NETHERLANDS gegevens in "Reading Order", die staan hier: 
#   http://earth-info.nga.mil/gns/html/cntyfile/nl.zip
# 
# de codes zijn hier gedocumenteerd:
#   http://earth-info.nga.mil/gns/html/gis_countryfiles.htm
#

#import sqlalchemy
import csv
import os

this_dir = os.path.dirname(__file__)
from bioport_repository.db_definitions import Location



"""
NL.00    Netherlands (general)
NL.01    Provincie Drenthe
NL.02    Provincie Friesland
NL.03    Gelderland
NL.04    Groningen
NL.05    Limburg
NL.06    North Brabant
NL.07    North Holland
NL.09    Utrecht
NL.10    Zeeland
NL.11    South Holland
NL.15    Overijssel
NL.16    Flevoland
"""


def refill_geolocations_table(source_fn, session, limit=-1):
    reader = csv.reader(open(source_fn), delimiter='\t')

    i = 0
    j = 0
    for l in reader:
        i += 1
        if i == 1:# the first line contains headers
            continue 
        
    #    assert l[23] == l[24], 'line %s: %s != %s' % (i, l[23], l[24])
    #    if l[23] != l[24]: print 'line %s: %s != %s' % (i, l[23], l[24])
        fc = l[9]
    #    if fc == 'S':
    #        print i, l[23]
        if fc in ['P']: #this is a place
    #        if l[13] == '02':
    #            print i, l[12], l[13], l[23]
            if l[12] != 'NL':
                print i, l[12], l[13], l[23]
                assert 0, 'Het zijn allemaal NL plaatsen'
    
            r = Location(
                ufi = l[1], #unique
                uni = l[2], #unique as well
                lat = l[3], #latitude
                long = l[4], #longitude
    #            cc1 = l[12],
                adm1 = l[13],  #provincie (als 2 cijferige code, i.e. 02 == friesland)
                sort_name = l[22],
                full_name = l[23],
                #full_name_nd, l[24] bevat the full_name, maar dan zonder diacritische tekents
            )
            #if l[23] == 'Noordeinde':
            #    print l[13], l[23]
            session.add(r)
            j += 1
            if limit > -1 and j >= limit:
                break

