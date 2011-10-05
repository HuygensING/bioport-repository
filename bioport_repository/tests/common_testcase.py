import os
#import sys
import unittest
import shutil
#import atexit
#import subprocess
from plone.memoize import instance
import sqlalchemy

from bioport_repository.repository import Repository
from bioport_repository.tests.config import DSN
from bioport_repository.biography import Biography
from bioport_repository.source import BioPortSource, Source
from gerbrandyutils import sh

from names.name import Name

THIS_DIR = os.path.split(os.path.abspath(__file__))[0]
SVN_REPOSITORY  = os.path.abspath(os.path.join(THIS_DIR, 'data/bioport_repository'))
SVN_REPOSITORY_LOCAL_COPY = os.path.abspath(os.path.join(THIS_DIR, 'data/bioport_repository_local_copy'))
IMAGES_CACHE_LOCAL = os.path.join(THIS_DIR, 'tmp')
SQLDUMP_FILENAME = os.path.join(THIS_DIR, 'data/bioport_mysqldump.sql')


class CommonTestCase(unittest.TestCase):
    
    _fill_repository = True

    @instance.clearafter
    def setUp(self):     
        if os.path.isdir(SVN_REPOSITORY):
            shutil.rmtree(SVN_REPOSITORY)
        sh('svnadmin create %s --pre-1.4-compatible' % SVN_REPOSITORY)
        if not os.path.isdir(IMAGES_CACHE_LOCAL):
            os.mkdir(IMAGES_CACHE_LOCAL)

        self.repo = Repository(
              svn_repository_local_copy = SVN_REPOSITORY_LOCAL_COPY, 
              svn_repository='file://%s' % SVN_REPOSITORY,
              db_connection=DSN,
              images_cache_local=IMAGES_CACHE_LOCAL,
              )
              
         
        self.repo.db.metadata.drop_all()
        if self._fill_repository:
            if not os.path.isfile(SQLDUMP_FILENAME):
                self.create_filled_repository_from_scratch()
            self.create_filled_repository()
        else:
            self.repo.db.metadata.create_all()

        self.db = self.repo.db
        
    def tearDown(self):
        #clean out the repository
        #get whatever data there was
        sh('rm -rf %s' % SVN_REPOSITORY ) 
        sh('rm -rf %s' % SVN_REPOSITORY_LOCAL_COPY ) 
        
        # remove also all data from the database
        self.repo.db.metadata.drop_all()
        if os.path.exists(IMAGES_CACHE_LOCAL):
            shutil.rmtree(IMAGES_CACHE_LOCAL)
        #self.repo.db.namenindex.db.metadata.drop_all()
        return
   
    def create_filled_repository(self, sources=None):
        """create  a repository filled with example data"""
        if not self._fill_repository:
            return self.repo
        sql_string = open(SQLDUMP_FILENAME).read().decode('latin1')
        import bioport_repository.tests
        testdir = os.path.dirname(bioport_repository.tests.__file__)
        datadir = os.path.join(testdir, 'data')
        sql_string = sql_string.replace('{{{test_data_dir}}}', testdir)
        self.repo.db.get_session().execute(sql_string)
        self.repo.db.get_session().flush()
        self._fill_repository = False #dont fill the repository again
        return self.repo
        
    def create_filled_repository_from_scratch(self, sources=2):
        #create a repo filled with some data
        self.repo.db.metadata.create_all()
        url = 'file://%s' % os.path.abspath(os.path.join(THIS_DIR, 'data/knaw/list.xml'))
        source = Source(id=u'knaw', url=url , description='test')
        self.repo.add_source(source)
        self.repo.download_biographies(source)
        url = 'file://%s' % os.path.abspath(os.path.join(THIS_DIR, 'data/knaw2/list.xml'))
        if sources > 1:
            source = Source(id=u'knaw2', url=url , description='test')
            self.repo.add_source(source)
            self.repo.download_biographies(source)
        self.repo.db._update_category_table()
        
        #also add Bioport source
        src = Source('bioport', repository=self.repo)
        self.repo.add_source(src)
        src.set_quality(10000)

        def parse_dsn(s):
            return sqlalchemy.engine.url._parse_rfc1738_args(s)

        dsn = parse_dsn(DSN)
        username = dsn.username or ""
        passwd = dsn.password or ""
        if not passwd:
            sh('mysqldump -u %s bioport_test > %s' % (username, SQLDUMP_FILENAME))
        else:
            sh('mysqldump -u %s -p%s bioport_test > %s' % (username, passwd, SQLDUMP_FILENAME))
        self._is_filled = True
        return self.repo
    
    def _add_source(self, source_id):
        try:
            source = self.repo.get_source(source_id)
        except ValueError: #a source with this id did not exist yet
            source = Source(id=source_id)
            self.repo.save_source(source)        
        return source
    
    def _add_person(self, 
        name=None, 
        names=None,
        geboortedatum=None,
        sterfdatum=None,
        xml_source=None,
        ):
        """helper function for adding a new person to the repository
        
        returns:
            a Person instance
        """
        #make a new biography
        
        source_id = u'bioport_test'
        source =self._add_source(source_id)
        if name:
            name = Name(name)
        if names:
            names= [Name(n) for n in names]
        
        if xml_source: 
            bio = self._create_biography(xml_source=xml_source)
        else:
            bio = self._create_biography(
                 name=name, 
                 names=names,
                 geboortedatum=geboortedatum,
                 sterfdatum=sterfdatum,
                 )
        
        #save it
        self._save_biography(bio, comment=u'added by test')
        return bio.get_person()
    
    def _create_biography(self, **args):
        source_id= u'bioport_test'
        self._add_source(source_id)
        defaults = {
            'naam_publisher':'x',
            'url_biografie': 'http://placeholder.com',
            'url_publisher': 'http://placeholder.com',
            }
        defaults.update(args)
        id = str(len(self.repo.get_biographies()))
        xml_source= args.get('xml_source')
        if xml_source:
            return Biography(repository=self.repo, source_id=source_id, id=id).from_string(xml_source)
        else:
            return Biography(repository=self.repo, source_id=source_id, id=id).from_args(**defaults)
    
    def _save_biography(self,biography, comment=u'saved by test'): 
        self.repo.save_biography(biography, comment)
        
class CommonTestCaseTest(CommonTestCase):
    
    def test_sanity(self):
        self.assertEqual(len(self.repo.get_sources()), 2)
        self.assertEqual(len(self.repo.get_biographies()), 10)
        self.assertEqual(len(self.repo.get_persons()), 10)

def create_mysqldump():      
    """create a .sql file that is used for setting up the database for each test"""
    open(SQLDUMP_FILENAME,'w').write('show tables')
    unittest.main(defaultTest='CommonTestCase.create_filled_repository_from_scratch')   
