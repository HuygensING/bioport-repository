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

#
# THIS CODE IS DEAD, NOT USED, IGNORE
#

#import pysvn
#from pysvn import ClientError
import os
from repocommon import Singleton
from repocommon import  BioPortException
import time


#from svn import repos, core, fs
#some docs here;
#http://pysvn.tigris.org/docs/pysvn_prog_guide.html

class SVNRepository(object):
    """interface to svn repository"""
    __metaclass__ = Singleton
    def __init__(self, svn_repository=None, svn_repository_local_copy=None):
        """
        arguments:
            path - the path to the local copy
            url - the url of the reposotyr 
        
        """
        #XXX
        return
    
        self.root_path = svn_repository_local_copy
        url = svn_repository 
            
        self.url = url
            
#        self.client = pysvn.Client()
#        repository = repos.open(root_path)
#        self.fs_ptr = repos.fs(repository)
    
    def __repr__(self):
        return '<SVNRepository instance at %s>' % self.root_path
    
#    def ls(self, path='.', recurse=False):
#        #get the elements from the repository that are under source control
#        ls = self.client.ls(
#            os.path.join(self.root_path, path),
#            recurse=recurse,
#            )
#        
#        #ls = [l[0].repos_path for l in ls]
#        return ls
   
    def ls(self, path= '.', recurse=False): 
        if recurse:
            raise NotImplementedError('Recursion is not yet implementend')
        p = self.absolute_path(path)
        ls = os.listdir(p)
        ls = [p for p in ls if not p.startswith('.')]
        return ls
    
    def absolute_path(self, path):
        if path.startswith(self.root_path):
            p = path
        else:
            p = os.path.join(self.root_path, path)
            
        p = os.path.abspath(p)
        return p
    
    def get_file(self, path):
        """ """
        p = os.path.join(self.root_path, path)
        f = open(p)
        return f
    def save_file(self, path,s):
        
        p = os.path.join(self.root_path, path)
        f = open(p, 'w') 
        f.write(s)
        f.close()
        
        if not   self.status(p).is_versioned:
            self.client.add(p)
    def create_dir(self, path, log_message):
        """ """
        p = os.path.join(self.root_path, path)
        
        #create the path if it does not already exist
        if not os.path.exists(p):
            os.mkdir(p) 
            self.client.add(p)
        else:
#            print 'Path %s already exists in repository %s\n' % (path, self.root_path)
            pass
    def create_file(self, path,s, log_message='--'):
        self.save_file(path, s)      
    
    def checkout(self):
        try:
            self.client.checkout(url = self.url, path=self.root_path)
        except:
            print self.root_path 
            raise
    def commit(self, log_message, path=None): 
        if not path:
            path = self.root_path
        self.client.checkin([path], log_message )
   
    def update(self, path=''):
        p = os.path.join(self.root_path, path)
        self.client.update([p] )
        

    def add(self, path):
        self.client.add(path)

            
        #XXX this might be an efficiency bottleneck later
#        self.client.checkin([p], log_message )
                           
    def remove(self, path, log_message='-'):
        p = os.path.join(self.root_path, path)
        try:
#            self.client.checkin([p], 'ci before remove to avoid conflicts') 
            self.client.remove([p])
                
        except:
#            statuses = self.client.status(p, recurse=False)
            #assert 0, [s['is_versioned'] for s in statuses]
            #status = [s for s in statuses if s['path'] == p][0]
            #assert 0, status['is_versioned']
            self.client.update([p])
            self.client.checkin([p], 'ci before remove to avoid conflicts') 
            self.client.remove([p])
#        self.client.checkin([p], log_message)

    def status(self, path):
        changes = self.client.status(self.root_path)
        status = [f for f in changes if f.path == self.absolute_path(path)]
        if not status:
            raise BioPortException('Could not find information about %s in the repository')
        status = status[0]
        return status
    
    def status_readable(self, path):
        """return a humanreadable description of the status of this item"""
        status = self.status(path)
        d = {
             'text_status': status.text_status,
             'is_versioned': status.is_versioned,
             'entry.commit_time': status.entry.commit_time,
             'entry.commit_time (formatted)': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(status.entry.commit_time)),
             'entry.commit_author': status.entry.commit_author,
             
             }
        return 'Status of %s\n%s\n' % (
                path, 
                d,
                )
    def get_sources(self, order_by=None):
        """
        return:
            a list of Source instances
        """
        #XXX should get them from the db, of course
        #we get the data from the repository
        dirnames = self.svn_repository.ls()
#        dirnames = [self.svn_repository.absolute_path(d) for d in dirnames]
        from bioport_repository.source import Source
        ls = [Source(d) for d in dirnames]
        if order_by == 'quality':
            ls = [(s.get_value('quality'), s) for s in ls]
            ls.sort(reverse=True)
            ls = [s[1] for s in ls]
        return ls
    
    def delete_source(self, source):
        self.svn_repository.client.checkin([source.path()], log_message='Checkin source %s before removing' % source.id)
        self.svn_repository.client.remove([source.path()])
        self.svn_repository.client.checkin([source.path()], log_message='Remove source %s' % source.id)
    
class SVNEntry:
    def __init__(self):
        self.svn_repository = SVNRepository()
        
    def svn_status(self):
        return self.svn_repository.status(self.path())
    
    def svn_status_readable(self):
        return self.svn_repository.status_readable(self.path())
        
    def last_commit(self):
        """when was this """
        if self.svn_status().entry:
            return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(self.svn_status().entry.commit_time))
        else:
            return 'not committed'
    def last_commit_by(self):
        return self.svn_status().entry.commit_author
    
#    def youngest_revision_number(self):
#        return fs.youngest_rev(self.fs_ptr)
#    
#    def get_root(self):
#        root = fs.revision_root(fs_ptr, self.youngest_revision_number())
#        return root
#    
#    def read_file(self, path):
#        stream = fs.file_contents(self.get_root(), path)
#        stream = core.Stream(stream)
#        return stream.read()
#    
#    def properties(self,path):
#        return fs.node_proplist(self.get_root(),path)
#    
#    def save_file(self,path, s):
#        #begin transaction
#        txn = fs.begin_txn(self.fs_ptr, self.youngest_revision_number())
#        txn_root = fs.txn_root(txn)
#       
#        #abort
#        #fs.abort_txn(txn))
#        #make the file (how to check exi
#        fs.make_file(txn_root, path)
#        fs.commit_txn(txn)
#        
#    def delete_file(self,path):
#       txn = fs.begin_txn(self.fs_ptr, self.youngest_revision_number())
#        txn_root = fs.txn_root(txn)
#       
#        #abort
#        #fs.abort_txn(txn))
#        fs.delete(txn_root, path)
#        fs.commit_txn(txn)
#  
