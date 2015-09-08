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

import os
from lxml import etree
from biography import Biography
from repocommon import BioPortException
from db_definitions import STATUS_NEW


class Source(object):
    """A source of biographical data"""
    def __init__(
        self,
        id,
        url=None,
        description=None,
        quality=0,
        default_status=STATUS_NEW,
        xml=None,
        repository=None,
        ):
        """
        arguments:
            - default_status : new biographies will get this status
        """
        self.xml = xml
        self.id = unicode(id)
        # TODO: raise a proper exception, fix database fields as well
        MAX_LENGTH = 50
        assert len(id) <= MAX_LENGTH, 'source.id cannot be more than %s characters long (it is %s - %s)' % (MAX_LENGTH, self.id, self)
        self.url = url
        self.description = description
        self.quality = quality
        self.repository = repository
        self.default_status = default_status

        # last times "download biographies" button has been pressed and
        # action completed
        self.last_bios_update = None
        if self.xml:
            self._from_xml(xml)

    def __str__(self):
        return '<Source object with id %s>' % self.id

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return type(self) == type(other) and self.id == other.id

    def path(self):
        return os.path.join(self.svn_repository.root_path, self.id)

    def _to_xml(self):
        """create an xml file with enough info to reconstruct the source

        returns:
            a string
        """
        keys = [
            'id',
            'url',
            'description',
            'quality',
            'default_status',
            'last_bios_update'
            ]
        n = etree.Element('biodes_source')  # @UndefinedVariable
        for k in keys:
            value = getattr(self, k)
            if value is not None:
                value = unicode(value)
            else:
                value = ''
            etree.SubElement(n, k).text = value  # @UndefinedVariable
        return etree.tostring(n, pretty_print=True)  # @UndefinedVariable

    def save(self):
        self.repository.save_source(self)

    def _from_xml(self, xml):
        t = etree.fromstring(xml)  # @UndefinedVariable
        for n in t:  # .getroot():
            setattr(self, n.tag, n.text)
        # hack for the quality attribute
        self.quality = int(self.quality)
        self.default_status = int(self.default_status)
        return self

    def set_value(self, **args):
        for k in args:
            setattr(self, k, args[k])

    def get_value(self, k):
        """get the value for k

        implements lazy loading lookup
        """
        try:
            return getattr(self, k)
        except AttributeError:
            self.from_repository()
            return getattr(self, k)

    def set_quality(self, v):
        self.quality = v
        self.repository.save_source(self)  # save self so it can be found and re-orderd by the repository
        ls = self.repository.get_sources(order_by='quality', desc=False)
        ls.remove(self)
        ls.insert(v, self)
        i = 0
        for s in ls:
            s.quality = i
            i += 1
            self.repository.save_source(s)

    def get_quality(self):
        return self.quality

class BioPortSource(Source):
    """The 'bioport source' is a special Source that contains the biographical descriptions
        added and edited by the bioport editors
    """
    def __init__(self, id='bioport'):
        self.id = 'bioport'
        Source.__init__(self, self.id, quality=99999)

    def new_biography(self, id):
        """create a new biography

        bio definition, these biographies are of identified people, so the id must be a valid bioport id
        """
        bio = Biography(id=id, source=self)
        bio._set_up_basic_structure()  # this gives some basic structure, but strictly speaking this is not a valid biodes document
        bio._set_bioport_id(id)
        bio.save()
        return bio

    def download_data(self):
        # this should just not be called
        raise BioPortException("No data to download: these are the biographies edited by the BioPort editors")
