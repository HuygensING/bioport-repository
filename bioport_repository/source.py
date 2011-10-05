
import os
from svn_repository import SVNRepository, SVNEntry
from lxml import etree
from biography import Biography
from repocommon import BioPortException
from db_definitions import STATUS_NEW
import urllib
import time
    
class Source(object):
    """A source with biographical data"""
    
    def __init__(self, id,url=None, description=None, quality=0, default_status=STATUS_NEW, xml=None, repository=None):
        self.xml = xml
        self.id = unicode(id)
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
        n = etree.Element('biodes_source') #@UndefinedVariable
        for k in keys:
            value = getattr(self, k)
            if value is not None:
                value = unicode(value)
            else:
                value = ''
            etree.SubElement(n, k).text = value #@UndefinedVariable
        return etree.tostring(n, pretty_print=True) #@UndefinedVariable

    def _from_xml(self, xml):
        t = etree.fromstring(xml) #@UndefinedVariable
        for n in t: #.getroot():
            setattr(self, n.tag, n.text)
        #hack for the quality attribute
        self.quality = int(self.quality)
        return self
    
## DISABLED - sources are stored in the DB    
#    def from_repository(self):
#        
#        xml_fn =  os.path.join(self.path(), '_source_information.xml')
#        print xml_fn
#        if not os.path.exists(xml_fn):
#            self._to_repository()
#        try:
#            parser = etree.XMLParser(no_network=False)
#            t = etree.parse(xml_fn, parser)
#        except:
#            print open(xml_fn).read()
#            raise
#        for n in t.getroot():
#            setattr(self, n.tag, n.text)
#        #hack for the quality attribute
#        self.quality = int(self.quality)
#        return self
# 
        
    def set_value(self,**args):
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
        self.repository.save_source(self)  #save self so it can be found and re-orderd by the repository
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
    #this is the 'bioport source' : the biographical descriptions added and edited by the bioport editors
    def __init__(self, id='bioport'):
        self.id = 'bioport'
        Source.__init__(self, self.id, quality=99999)
    
    def new_biography(self, id):
        """create a new biography
               
        bio definition, these biographies are of identified people, so the id must be a valid bioport id
        """
        bio = Biography(id=id, source=self) 
        bio._set_up_basic_structure() #this gives some basic structure, but strictly speaking this is not a valid biodes document
        bio._set_bioport_id(id)
        bio.save()
        return bio
           
    def download_data(self):
        raise BioPortException("No data to download: these are the biographies edited by the BioPort editors")
        pass
    
