##! /usr/bin/python    
##encoding=utf-8

# occupations
#this is the bereoepnlijst van DBNL
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
    
