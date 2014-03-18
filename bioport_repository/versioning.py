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



class Version:
    """represents a version of a BioDes document"""
    def __init__(self, 
        biography,
        ):
        """
       
        arguments:
            biography : an instance of biography
        
        """
        self.biography = biography
        r = biography.record
        self.user = r.user
        self.time = r.time
        self.comment = r.comment
        self.document_id =  r.id
        self.version = r.version
    
    def __str__(self):
        return '<Version %s of  %s by %s of %s (%s)>' % (self.version, self.document_id, self.user, self.time, self.comment )
    def __repr__(self):
        return self.__str__()