#! /usr/bin/python    
#encoding=utf-8

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

# occupations
#this is the beroepenlijst van DBNL
#
from bioport_repository.db_definitions import Occupation 
    
def fill_occupations_table(session):
    beroepen = """12    advocaat/jurist
    22    agrariër
    23    ambachtsman
    24    ambtenaar
    25    arbeider/werkman
    40    archivaris
    1    beeldend kunstenaar
    15    boekdrukker/uitgever
    2    boekhandelaar
    26    classicus
    27    diplomaat
    17    doopsgezind predikant/leraar
    28    filosoof
    10    herv./geref. predikant
    29    historicus
    21    joods geestelijke
    30    journalist
    3    koopman/zakenman/indust.
    31    kunsthistoricus
    16    leraar
    33    letterkundige (NIET-neerl.)
    18    luthers predikant
    34    magistraat
    5    medicus
    6    militair
    7    musicus
    8    natuurwetenschapper
    11    onderwijzer
    9    politicus/staatsman
    19    remonstr. predikant/leraar
    20    rk-geestelijke
    13    schilder
    14    toneelspeler
    35    vakbondsman
    36    vertaler
    37    wiskundige
    38    zeevarende
    39    zielsverzorger/psychol/ps.ther."""
    ls = beroepen
    ls = ls.split('\n')
    ls = [l.strip().split('   ') for l in ls if l.strip()]
    ls = [(int(nr), s.strip()) for nr, s in ls] 
    if session.query(Occupation).all():
        assert 0, 'The table %s already contains information -- please empty it first' % Occupation.__tablename__
    for nr, name in ls:
        session.add(Occupation(id=nr, name=name))
#    transaction.commit()
    
