##! /usr/bin/python    
##encoding=utf-8

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


from bioport_repository.db_definitions import Category 
import transaction


def fill_table(session):    

    categories = """ 
       1. Adel en vorstenhuizen
       2. Bedrijfsleven
       3. Beeldende kunsten & vormgeving
       4. Kerk en godsdienst
       5. Koloniale en overzeese betrekkingen en handel
       6. Krijgsmacht en oorlog
       7. Letterkunde
       8. Maatschappelijke bewegingen
       9. Rechtspraak
      10. Onderwijs & wetenschappen
      11. Politiek en bestuur
      12. Radio, TV en film
      14. Sport en vrije tijd
      15. Uitvoerende kunsten
      16. Zorg
      17. Overig
    """

    ls = categories
    ls = ls.split('\n')
    ls = [l.strip().split('.', 1) for l in ls if l.strip()]
    ls = [(int(nr), s.strip()) for nr, s in ls] 
    #print ls
    #delete existing data
    session.query(Category).delete()
#        assert 0, 'The table %s already contains information -- please empty it first' % Category.__tablename__
    for nr, name in ls:
        session.add(Category(id=nr, name=name))
    
