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

import os
import re
import types
import logging
import string
from datetime import datetime
import transaction

from lxml import etree

from names.common import html2unicode
from sqlalchemy.orm.exc import DetachedInstanceError
from biodes import BioDesDoc
from bioport_repository.illustration import Illustration
from bioport_repository.datamanipulation.data_extraction import BioDataExtractor
from bioport_repository.db_definitions import BiographyRecord


def create_biography_id(source_id, local_id):
    """generate an id for this biography on the basis of source_id and local_id

    local_id is expected to be unique in the source_id namespace
    """
    biography_id = u'%s/%s' % (source_id, local_id)
    if len(biography_id) > 50:
        logging.warning('Ids can be maximally 50 characters long; this one ' \
                        'is %s: "%s"\nShorted it to 50 characters' % (len(biography_id), biography_id))
        biography_id = biography_id[:50]
    return biography_id


class Biography(object, BioDesDoc):

    def __init__(self,
        id=None,
        source_id=None,
        biodes_document=None,
        source_url=None,
        repository=None,
        record=None,
        version=None,
        ):
        """
        arguments:
            id - a 'local id': should be unique with the biographies in the
            source, and preferably as persistent as possible
        """
        self.id = id
        self.repository = repository
        self._record = record
        self.source_id = source_id
        self.biodes_document = biodes_document
        self.source_url = source_url
        if self.biodes_document:
            self.id = self.create_id()
        self.version = version

    def __str__(self):
        s = '<BioPort Biography %s - version %s>' % (self.id, self.version)
        return s
    __repr__ = __str__

    def __eq__(self, other):
        return self.id == other.id

    def from_url(self, url):
        self.source_url = url
        BioDesDoc.from_url(self, url)
        self.create_id()
        return self

    def get_root(self):
        try:
            return self.root
        except AttributeError:
            if not self.biodes_document:
                self._set_up_basic_structure()
                self.biodes_document = etree.tostring(self.root)
                return self.root
            else:
                self.root = etree.fromstring(self.biodes_document)
                return self.root

    def get_source(self):
        """return the source of this biography

        returns:
            a Source instance
        """
        try:
            return self._source
        except AttributeError:
            self._source = self.repository.get_source(self.source_id)
            return self._source
        
    @property
    def record(self):
        try:
            self._record.source_id
        except AttributeError:
            raise
        except DetachedInstanceError:
            self.repository.db.get_session().merge(self._record)

        return self._record

    def get_text_without_markup(self):
        """get the text of the biography, but remove any HTML codes"""
        text_node = self.xpath('biography/text')
        if text_node:
            assert len(text_node) == 1
            text_node = text_node[0]
            text = u'\n'.join([n.text for n in text_node.getiterator() if n.text])


            for tagname in ('head', 'style', 'script'):
                start, end = "<%s>" % tagname, "</%s>" % tagname
                expr = u"%(start)s.*?%(end)s" % locals()
                text = re.compile(expr, re.IGNORECASE | re.DOTALL).sub('', text)
            text = re.compile('<.*?>', re.DOTALL).sub('', text) #need to compile for DOTALL to work
            text = html2unicode(text)
            text = text.strip()
            return text
        else:
            return u''

    def get_text_with_highlight(self):
        """
        """
        text = self.get_text_without_markup()
        if not text:
            return u""
        else:
            # highlight years
            text = re.sub(r'(\d{4})', r'<span class="highlight">\1</span>', text)
            words = text.split(' ')
            if len(words) > 200:
                text = u' '.join(words[:200])
                css_id = abs(hash(self.id))
                extra_text_id = "%s-extra-text" % css_id
                toggler_id = "%s-extra-text-toggler" % css_id
                text += u"""\
<i id="%(toggler_id)s">
    <b>[<a onclick="jQuery('#%(extra_text_id)s').toggle(150);
                    jQuery('#%(toggler_id)s').hide();">...</a>]
    </b>
</i>""" % locals()
                extra_text = u'<span id="%s" style="display:none;">%s</span>' \
                            % (extra_text_id, u' '.join(words[200:]))
                text += extra_text
            return text

    def snippet(self, size=200):
        """
        arguments:
            size : (maximum) number of characters to show
        """
        text = self.get_text_without_markup()
        if not text:
            return u''

        if len(text) < size:
            return text
        else: #we have a text that is longer than size, so we shorten it 
            s = text[:size]
            s = string.rsplit(s, maxsplit=1)[0]
            if len(s) < len(text):
                s += u'...'
            return s

    def get_snippet(self, source_id):
        """get a snippet for a certain source

        (this is a hack for bioport biographies, that can override snippets of sources...)
        """
        ls = self.get_element_biography().xpath('snippet[@source_id="%s"]' % source_id)
        if ls:
            return ls[0].text

    def set_snippet(self, source_id, snippet):
        """set a snippet for a certain source

        (this is a hack for bioport biographies, that can override snippets of sources...)
        """
        ls = self.get_element_biography().xpath('snippet[@source_id="%s"]' % source_id)
        if ls:
            element = ls[0]
        else:
            element = etree.SubElement(self.get_element_biography(), 'snippet') #@UndefinedVariable
            element.set('source_id', source_id)
        if snippet:
            snippet = unicode(snippet)
            element.text = snippet
        else:
            element.text = u''

    def create_id(self):
        """return an ID for the biography

        this id is based on:
        - the local_id defined in the XML file
        - if this is not found, on the source_url

        """
        if self.id:
            return self.id
        else:
            local_id = self.get_value('local_id')
            # if the xml file does not contain an id we determine it
            # from the file name
            if local_id is None:
                local_id = self.source_url.split('/')[-1]
            assert local_id, """The biography at %s does not have a local_id defined""" % self.source_url
            self.id = create_biography_id(self.source_id, local_id)
            return self.id

    def get_id(self):
        return self.id

    def path(self):
        """create a standard path where this biography can be found"""
        p = os.path.join(self.svn_repository.root_path, self.source.id, self.id)
        return p

    def get_versions(self):
        """get all versions of this biography

        returns:
            a list of BioDesDocument instances
        """
        pass

    def get_bioport_id(self):
        ls = self.get_value('bioport_id')
        if ls:
            return ls[-1]
        else:
            #try to find the bioport_id in the repository based on the local_id
            bioport_id = self.repository.db.get_bioport_id(biography_id=self.create_id())
            return bioport_id

    def get_person(self):
        try:
            return self._person
        except:
            bioport_id = self.get_bioport_id()
            self._person = self.repository.get_person(bioport_id=bioport_id)
        return self._person

    def save(self, user, comment=''):
        db = self.repository.db
        self.create_id()
        with db.get_session_context() as session:
            bioport_id = self.get_bioport_id()
            default_status = self.get_source().default_status
            person = self.get_person()
            if not person:
                bioport_id = self.get_bioport_id()
                if not bioport_id:
                    bioport_id = db.fresh_identifier()
                    person = db.add_person(bioport_id=bioport_id, default_status=default_status, checkforprexistingsbio=False)
                else:
                    person = db.get_person(bioport_id)
                    if not person:
                        person = db.add_person(bioport_id=bioport_id, default_status=default_status, checkforprexistingsbio=False)
                self.set_value('bioport_id', bioport_id)
                self._person = person

            #register the biography in the bioportid registry
            #(note that this changes the XML in the biography object)
            db._register_biography(self)

            #get all biographies with this id, and increment their version number with one
            ls = db._get_biography_query(
                local_id=self.id,
                order_by='version',
                )
            ls = enumerate(ls)
            ls = list(ls)
            ls.reverse()
            for i, r_bio in ls:
                r_bio.version = i + 1
                session.object_session(r_bio).flush()

            # for some reason sqlalchemy does not always write changes to db
            # (and we get an integreity error because id-version is not unique)
            # TODO: fix bug described in lines above in a more elegant way

            # create a new version
            self._record = r_biography = BiographyRecord(id=self.get_id())
            session.add(r_biography)
            session.flush()

            r_biography.source_id = self.source_id
            r_biography.biodes_document = self.to_string()
            r_biography.source_url = unicode(self.source_url)
            r_biography.url_biography = self.get_value('url_biography')
            self.version = r_biography.version = 0
            r_biography.user = user
            r_biography.comment = comment
            r_biography.time = datetime.today().isoformat()
            r_biography.source_id

        # update the information of the associated person 
        #  (or add a person if the biography is new)
        person = self.get_person()

        person.save()

        msg = 'saved biography with id %s' % (self.id)
        if comment:
            msg += '; %s' % comment

        db.log(msg=msg, record=r_biography)

    def naam(self):
        """
        get the first Naam of this biography

        returns:
            a Naam instance
        """
        namen = self.get_value('namen')
        if namen:
            return namen[0]
        else:
            return None

    def guess_value(self, k):
        """Do your best to 'guess' a decent value for the given k

        if the value is already defined in the biodes document, we return that value

        arguments
        - k - a string - possible values for k are given in the list '_guessable_values'

        returns:
            a value - could be a string, a list, of an XML fragment, depending on what k is
        """
        extractor = BioDataExtractor(self)
        return extractor.guess_value(k)

    def title(self):
        if self.naam():
            return self.naam().volledige_naam()

    def get_category_ids(self):
        return [c.get('idno') for c in self.get_states(type='category')]

    def set_category(self, category_ids=[]):
        """set the categories of the biography to the given set

        overwrites any existing categories"""
        for el in self.get_states(type='category'):
            el.getparent().remove(el)

        if type(category_ids) != types.ListType:
            category_ids = [category_ids]

        category_ids = set([str(id) for id in category_ids]) #filter out any duplicates

        for category_id in category_ids:
            assert  category_id.isdigit(), 'category_id should be a digit (not %s)' % category_id
            #look for the category
            category = self.repository.get_category(category_id)
            if category is None:
                pass #it would have been better to raise an error here, but the application expects us to ignore non-valid arguments
#                raise KeyError('No category found with this ID: %s' % category_id)
            if category:
                name = category.name
                self.add_state(type='category', idno=str(category_id), text=name)

    def get_quality(self):
        return self.get_source().get_quality()

    def get_illustrations(self, default=[]):

        figures = BioDesDoc.get_illustrations(self)
        images_cache_local = ''
        images_cache_url = ''
        prefix = self.get_source().id
        if self.repository:
            images_cache_local = self.repository.images_cache_local
            images_cache_url = self.repository.images_cache_url
        result = []
        for figure in figures:
            url, caption = figure
            if not caption:
                caption = 'illustratie uit %s' % self.get_source().description
            if (not url.startswith('http://')) and (not url.startswith('file://')):
                #this is a relative url
                url = '/'.join((os.path.dirname(self.source_url), url))
                if not url.startswith('file://'):
                    url = 'file://' + url
            result.append(Illustration(
                 url=url,
                 images_cache_local=images_cache_local,
                 images_cache_url=images_cache_url,
                 prefix=prefix,
                 caption=caption,
                 link_url=self.get_value('url_biografie'),
                 ))
        return result

    def get_source_description(self):
        source = self.get_source()
        if source.id in ['dbnl']:
            return self.get_value('naam_publisher')
        else:
            return source.description


    def set_religion(self, idno):
        els = self.get_states(type='religion')
        #we expect only one 'religion' state
        assert len(els) < 2
        if els and not idno:
            #remove the state
            self.remove_state(0, 'religion')
        else:
            self.add_or_update_state(type='religion', idno=str(idno))

    def get_religion(self):
        els = self.get_states(type='religion')
        if els:
            assert len(els) == 1
            return els[0]

