
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


"""This package handles the data reposotiry for Bioport."""

import os
import time
import logging
import shutil

from lxml import etree
import biodes

from bioport_repository.db_definitions import STATUS_VALUES, RELIGION_VALUES
from bioport_repository.db_definitions import SOURCE_TYPES
from bioport_repository.biography import Biography
from bioport_repository.db import DBRepository
# from bioport_repository.person import Person
from bioport_repository.repocommon import BioPortException
from bioport_repository.source import BioPortSource, Source
from bioport_repository.svn_repository import SVNRepository
from bioport_repository.illustration import CantDownloadImage


class Repository(object):

    ENABLE_SVN = False
    ENABLE_DB = True

    def __init__(
        self,
        svn_repository=None,
        svn_repository_local_copy=None,
        dsn=None,
        user='Unknown User',
        images_cache_local=None,
        images_cache_url=None,
        ):

        assert user
        self.svn_repository = SVNRepository(svn_repository=svn_repository, svn_repository_local_copy=svn_repository_local_copy)
        print 'initializing %s' % self
        self.db = DBRepository(
            dsn=dsn,
            user=user,
            repository=self,
            )
        self.db.repository = self
        if images_cache_local:
            try:
                msg = 'this path (for "images_cache_local") does not exist; %s' % images_cache_local
                assert os.path.exists(images_cache_local), msg
            except:
                print msg

        self.images_cache_local = images_cache_local
        self.images_cache_url = images_cache_url
        self.user = user

    def get_bioport_ids(self):
        """return _all_ bioport_ids in the system"""
        return self.db.get_bioport_ids()

    def get_person(self, bioport_id):
        return self.db.get_person(bioport_id=bioport_id, repository=self)

    def count_persons(self, **args):
        return self.db.count_persons(**args)

    def get_persons(self, **args):
        """Get persons satisfying the given arguments

        arguments:
            order_by - a string - default is 'sort_key'

        returns: a PersonList instance - a list of Person instances
        """
        return self.db.get_persons(**args)

    def get_persons_sequence(self, *args, **kwargs):
        return self.db.get_persons_sequence(*args, **kwargs)

    def get_bioport_id(self, url_biography):
        return self.db.get_bioport_id(url_biography=url_biography)

    def delete_person(self, person):
        if self.ENABLE_DB:
            return self.db.delete_person(person)
        if self.ENABLE_SVN:
            raise NotImplementedError()

    def count_biographies(self, **args):
        return self.db.count_biographies(**args)

    def get_biographies(self, **args):
        if self.ENABLE_DB:
            return self.db.get_biographies(**args)
        elif self.ENABLE_SVN:
            raise NotImplementedError()

    def get_biography(self, local_id=None, **args):
        return self.db.get_biography(local_id=local_id, **args)

    def redirects_to(self, bioport_id):
        return self.db.redirects_to(bioport_id)

    def add_source(self, source):
        """add a source of data to the db"""
        if source.id in [src.id for src in self.get_sources()]:
            raise ValueError('A source with id %s already exists' % source.id)
        self.db.add_source(source)
        return source

    def delete_source(self, source):
        return self.db.delete_source(source)

    def get_source(self, id):  # @ReservedAssignment
        ls = [src for src in self.get_sources() if src.id == id]
        if not ls:
            raise ValueError('No source found with id %s\nAvailabe sources are %s' % (id, [s.id for s in self.get_sources()]))
        source = ls[0]
        return source

    def get_sources(self, order_by='quality', desc=True):
        """
        return: a list of Source instances
        """
        return self.db.get_sources(order_by=order_by, desc=desc)

    def get_status_value(self, k, default=None):
        items = STATUS_VALUES
        return dict(items).get(k, default)

    def get_status_values(self):
        return STATUS_VALUES

    def get_source_types(self):
        return SOURCE_TYPES

    def get_religion_values(self):
        return RELIGION_VALUES

    def get_author(self, author_id):
        if self.ENABLE_DB:
            return self.db.get_author(author_id)
        raise NotImplementedError

    def save(self, x):
        if x.__class__ == Biography:
            self.save_biography(x)
        elif x.__class__ == Source:
            self.save_source(x)
        else:
            raise TypeError('Cannot save a object %s in the repository: unknown type' % x)

    def save_source(self, source):
        source.repository = self
        if self.ENABLE_DB:
            self.db.save_source(source)
        if self.ENABLE_SVN:
            raise NotImplementedError()

    def save_person(self, person):
        if self.ENABLE_DB:
            self.db.save_person(person)
        if self.ENABLE_SVN:
            raise NotImplementedError()

    def save_biography(self, biography, comment=''):
        biography.repository = self
        if self.ENABLE_DB:
            biography = self.db.save_biography(biography, user=self.user, comment=comment)

        if self.ENABLE_SVN:
            raise NotImplementedError()

        return biography

    def detach_biography(self, biography):
        person = self.db.detach_biography(biography)
        return person

    def delete_biographies(self, source):
        sources_ids = [src.id for src in self.get_sources()]
        if source.id not in sources_ids:
            raise ValueError("no source with id %s was found" % source.id)
        else:
            if self.ENABLE_DB:
                self.db.delete_biographies(source)
            if self.ENABLE_SVN:
                raise NotImplementedError

    def delete_biography(self, biography):
        return self.db.delete_biography(biography)

    def download_biographies(self, source, limit=None):
        """Download all biographies from source.url and add them to the repository.
        Mark any biographies that we did not find (anymore), by removing the source_url property.
        Return the number of total and skipped biographies.

        arguments:
            source: a Source instance

        returns:
             a list of biography instances
        """

        # at the URL given we find a list of links to biodes files
        # print 'Opening', source.url
        assert source.url, 'No URL was defined with the source "%s"' % source.id

        logging.info('downloading data at %s' % source.url)
        logging.info('parsing source url')

        # TODO: perhaps it would be better to check on Source.__init__ if repository argument is given
        if not source.repository:
            source.repository = self
        try:
            ls = biodes.parse_list(source.url)
            if limit:
                ls = ls[:limit]
        except etree.XMLSyntaxError, error:  # @UndefinedVariable
            raise BioPortException('Error parsing data at %s -- check if this is valid XML\n%s' % (source.url, error))

        if not ls:
            raise BioPortException('The file at %s does not contain any links to biographies' % source.url)

        # we have a valid list of biographies to download
        # first we remove all previously imported biographies at this source
        logging.info('deleting existing biographies from %s' % source)
        self.delete_biographies(source=source)
        logging.info('downloading biodes files')
        total = len(ls)
        skipped = 0
        ls.sort()
        for iteration, biourl in enumerate(ls):
            iteration += 1
            if not biourl.startswith("http:"):
                # we're dealing with a fs path
                biourl = os.path.normpath(biourl)
                if not os.path.isabs(biourl):
                    biourl = os.path.join(os.path.dirname(source.url), biourl)
            if limit and iteration > limit:
                break
            logging.info('progress %s/%s: adding biography at %s' % (iteration, len(ls), biourl))
            # create a Biography object
            bio = Biography(source_id=source.id, repository=source.repository)
            bio.from_url(biourl)
            bio.save(user='', comment=u'downloaded biography from source %s' % source)

        # remove the temp directory which has been used to extract
        # the xml files
        if ls[0].startswith("/tmp/"):
            shutil.rmtree(os.path.dirname(ls[0]))

        s = '%s biographies downloaded from source %s' % (iteration, source.id)
        logging.info(s)
        source.last_bios_update = time.time()
        self.save_source(source)

#         logging.info('deleting orphaned persons')
#         self.delete_orphaned_persons(source_id=source.id)
        return total, skipped

    def delete_orphaned_persons(self, **args):
        # remove all elements from the person table that do not have any biographies associated with them anymore
        for p in self.get_persons(**args):
#             logging.info('%s'% p)
            if not p.get_biographies():
                self.delete_person(p)
        return

    def download_illustrations(self, source, overwrite=False, limit=None):
        """Download the illustrations associated with the biographies in the source.

        arguments:
            - source:  a Source instance
            - overwrite: Boolean. If overwrite is true, then we download also if we already have this image.
                default is False.
        returns:
            (total, skipped)
        """
        if not self.images_cache_local:
            raise Exception('Cannot download illustrations, self.images_cache_local has not been set')
        bios = self.get_biographies(source=source)
        total = 0
        skipped = 0
        for i, bio in enumerate(bios):
            logging.info('[%s/%s] downloading illustrations' % (i + 1, len(bios)))
            total += 1
            if limit and total > limit:
                break
            for ill in bio.get_illustrations():
                try:
                    ill.download(overwrite=overwrite)
                except CantDownloadImage, err:
                    skipped += 1
                    logging.warning("Can't download image: %s" % str(err))
        # remove the temp directory which has been used to extract
        # the xml files
        if source.url and source.url.endswith("tar.gz"):
            afile = bio.source_url.replace('file://', '')
            directory = os.path.dirname(afile)
            if os.path.isdir(directory):
                shutil.rmtree(directory)

        return total, skipped

    def get_most_similar_persons(self, **args):
        """get the most similar pairs of person, name we can find

           similar_to : a  bioport id
        returns:
            a list of triples (score, person1, person2)
        """
        return self.db.get_most_similar_persons(**args)

    def identify(self, person1, person2):
        """Identify the persons in this list (because they are really the same person)

        arguments:
            persons - a list of Person instances
        returns:
            a new Person instance representing the identified person
        """
        # the oldest identifier will be the canonical one
        return self.db.identify(person1, person2)

    def identify_persons(self, source_id, min_score):
        logging.info('Identifying all persons from {source_id} that are similar with a score of at least {min_score}'.format(source_id=source_id, min_score=min_score))
        for _score, person1, person2 in self.get_most_similar_persons(source_id=source_id, min_score=min_score, size=None):
            self.identify(person1, person2)

    def antiidentify(self, person1, person2):
        self.db.antiidentify(person1, person2)

#    OBSOLETE - or better, this should be handled undoing separate identify transactions
    def unidentify(self, person):
        return self.db.unidentify(person)

    def get_antiidentified(self):
        """return a list of anti-identified perons"""
        return self.db.get_antiidentified()

    def is_antiidentified(self, person1, person2):
        """return True if these two persons are on the 'anti-identified' list"""
        return self.db.is_antiidentified(person1, person2)

    def defer_identification(self, person1, person2):
        self.db.defer_identification(person1, person2)

    def get_deferred(self):
        return self.db.get_deferred()

    def get_identified(self, **args):
        return self.db.get_identified(**args)

    def redirect_identifier(self, bioport_id, redirect_to):
        """make sure that:
        1. all biographies associated with bioport_id will be associated with redirect_to
        2. the repository redirecs all references to bioport_id to redirect_to

        arguments:
            bioport_id - a bioport id
            redirect_to - a bioport id
        returns:
            None
        """
        if self.ENABLE_DB:
            self.db.redirect_identifier(bioport_id, redirect_to)
        if self.ENABLE_SVN:
            raise NotImplementedError

    def get_bioport_biography(self, person, create_if_not_exists=True):
        """get, or if it does not yet exist, create, a biodes document that represents the interventions
        of the editors in the biographical portal

        arguments:
            person - an instance of Person
        returns:
            an instance of Biography
        """
        source = BioPortSource()

        if source.id not in [s.id for s in self.get_sources()]:
            src = Source('bioport', repository=self)
            self.add_source(src)
            src.set_quality(10000)

        ls = self.get_biographies(source=source, bioport_id=person.get_bioport_id())
        ls = list(ls)  # turn generator into list
        if not ls:
            if create_if_not_exists:
                # create a new biography
                return self._create_bioport_biography(person)
            else:
                return
        else:
            # disabled warning - this is not so bad after all
#            if len(ls) != 1:
#                logging.warning( 'There was more than one Bioport Biography found for the person with bioport_id %s' %
#                          person.get_bioport_id())
            # if we have more than one biography, we take the one that has the same bioport_id as the person
            # (if such exists) - otherwise, arbitrarily, the one with the highest id
            return ls[0]
            if len(ls) == 1:
                return ls[0]

            ls_with_our_bioid = [b for b in ls if person.get_bioport_id() in b.id]
            if ls_with_our_bioid:
                if not len(ls_with_our_bioid) == 1:
                    raise Exception()
                return ls_with_our_bioid[0]
            else:
#                ls = [(b.id, b) for b in ls]
#                ls.sort(reverse=True) #we sort reverse, because that is also how we sort in "get_biographies"
#                ls = [b for (x, b) in ls]
                return ls[0]

    def _create_bioport_biography(self, person):
        source = BioPortSource(id='dummy')
        bio = Biography(id='%s/%s' % (source.id, person.get_bioport_id()), source_id=source.id)
        bio._set_up_basic_structure()
        bio.set_value(local_id=person.get_bioport_id())
        bio.set_value(bioport_id=person.get_bioport_id())
        self.save_biography(bio, u'created Bioport biography')
        return bio

    def get_identifier(self, bioport_id):
        if self.ENABLE_DB:
            self.db.get_identifier()
        if self.ENABLE_SVN:
            raise NotImplementedError

    def get_occupations(self):
        return self.db.get_occupations()

    def get_occupation(self, bioport_id):
        return self.db.get_occupation(bioport_id)

    def get_category(self, bioport_id):
        return self.db.get_category(bioport_id)

    def get_categories(self):
        # we wrap the category objects, so that when the session closes, sqlalchemy does not complain about the memoized objects
        return self.db.get_categories()

    def get_places(self, *args, **kwargs):
#        logging.info('call get_places(%s, %s)' % (args, kwargs))
        return self.db.get_places(*args, **kwargs)

    def get_log_messages(self, **args):
        return self.db.get_log_messages(**args)

    def get_versions(self, **args):
        """get the amount of last changes

        returns:
            a list of versioning.Version objects
        """
        return self.db.get_versions(**args)

    def undo_version(self, document_id, version):
        """undo all changes to the document with document_id, from version onwards"""
        return self.db.undo_version(document_id, version)


class AttributeDict(dict):

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.__dict__ = self
