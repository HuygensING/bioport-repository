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

from names.similarity import Similarity
from names.common import to_ymd

class Similarity(Similarity):
    """compares a person to a list of persons"""
    def __init__(self, person=None, persons=None):
        """
        
        arguments:
            person:  an instance of Person
            persons: a list of Person's
        """
        self._computed =False
        self._person = person
        self._persons = persons
    
    def compute(self):
        """compute the similarity scores between self._person and each element of self._persons
        
        save the score as an attribute on each Person in self._persons
        returns self._persons"""
        if self._computed:
            return self._persons
        for person in self._persons:
            person.score = self.similarity_score(self._person, person)
        self._computed = True
        return self._persons
    
    
    @classmethod
    def _decennium(cls, s):
        """ """
        if s:
            ymd= to_ymd(s)  
            y, _m, _d = ymd
            return y
    
    @classmethod
    def are_surely_equal(cls, p1, p2):
        """return True if we are sure these two persons are the same
        
        (for example, if they have a name in common, plus dates of birth and death"""
        return  cls.similarity_score(p1, p2) == 1.0
    
    
    @classmethod
    def similarity_score(cls, p1, p2):
        """compute how similar these two persons are"""
        #people with the same birth dates gat a high score
        birth1 = p1.get_value('birth_date')
        birth2 = p2.get_value('birth_date')
        death1 = p1.get_value('death_date')
        death2 = p2.get_value('death_date')
        same_dates = 1.0
        if birth1 and birth2:
            if p1._are_dates_equal(birth1, birth2):
                same_dates *=  1.0
            elif birth1[:3] == birth2[:3]:
                same_dates *= 0.8 
            else:
                same_dates *= 0.5
        else:
            same_dates *= 0.9 
    
        if death1 and death2:
            if p1._are_dates_equal(death1, death2):
                same_dates *=  1.0
            #we have all data available
            elif death1[:3] == death2[:3]:
                same_dates *= 0.8 
            else:
                same_dates *= 0.5 
        else:
            same_dates *= 0.9 
        
        if not (birth1 and birth2) and not (death1 and death2):
            same_dates *= 0.9 
            
        #compare the names
        ratios = []
        for n1 in p1.get_names():
            for n2 in p2.get_names():
                ratios.append(cls.ratio(n1, n2))
        if ratios:
            ratio = max(ratios)
        else:
            ratio = 0.0
        final_score = (ratio + same_dates) / 2.0
        return final_score
        
    def sort(self):
        self.compute()
        ls = [(p.score, p) for p in self._persons]
        ls.sort(reverse=True)
        self._persons = [p[1] for p in ls]
        return self._persons

    

    
    
        
