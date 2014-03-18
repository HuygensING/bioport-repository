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

#this is the singleton implementation of wikipedia (http://en.wikipedia.org/wiki/Singleton_pattern#Python)
class Singleton(type):
    def __init__(self, name, bases, dict):
        super(Singleton, self).__init__(name, bases, dict)
        self.instance = None
 
    def __call__(self, *args, **kw):
        if self.instance is None:
            self.instance = super(Singleton, self).__call__(*args, **kw)
 
        return self.instance
    
#USAGE: 
#class MyClass(object):
#    __metaclass__ = Singleton
# 
#print MyClass()
#print MyClass()

#class SortOfSingleton(type):
#    def __init__(self, name, bases, dict):
#        super(Singleton, self).__init__(name, bases, dict)
#        self.instance = {}
# 
#    def __call__(self, *args, **kw):
#        if self.instance is None:
#            self.instance = super(Singleton, self).__call__(*args, **kw)
# 
#        return self.instance

class BioPortException(Exception):
    pass

def is_valid_bioport_id(s):
    return s.isdigit()
