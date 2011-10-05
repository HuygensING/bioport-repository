#!/usr/bin/env python

import cProfile
import pstats
import tempfile
#import sys
#import os

from common import CommonTestCase, unittest, SQLDUMP_FILENAME

from names.name import Naam

from bioport_repository.repository import Repository
from bioport_repository.similarity.similarity import Similarity
#from bioport_repository.person import Person
from bioport_repository.biography import Biography
from bioport_repository.source import Source


def profile(s):   
    tf = tempfile.NamedTemporaryFile()
    cProfile.run(s, tf.name)
    p = pstats.Stats(tf.name)
    p.strip_dirs()
    p.sort_stats('cumulative')
#    p.sort_stats('time')
    #p.print_stats(30, 'soundex')    
    p.print_stats(30)

def setUp():
    
    global repo #define globally, so that the profile machinery can find it
    repo = Repository(
          dsn='mysql://localhost/bioport_test'
           )
    repo.db.get_session().execute(open(SQLDUMP_FILENAME).read().decode('latin1'))
    global source
    source = Source(id='bioport_test')
    repo.save_source(source)        
    sim = Similarity()
    global similarity_score 
    similarity_score = sim.similarity_score
        
def _add_person( naam, 
    geboortedatum=None,
    sterfdatum=None,
    ):
    #make a new biography
    bio = Biography( id = 'bioport_test/test_bio_%s' % naam, source_id=source.id)
        
    bio.from_args( 
          url_biografie='http://ladida/didum', 
          naam_publisher='nogeensiets', 
          url_publisher='http://pbulihser_url',
          naam=naam,
          geboortedatum=geboortedatum,
          sterfdatum=sterfdatum,
          )
        
    #save it
    repo.save_biography(bio)
    return bio.get_person()

def profile_similarity():
    print 'profiling'
    p1 = _add_person('Jan')
    p2 = _add_person('Jan Piet')
    sim = Similarity(p1, [p2] * 8000)
    sim.compute()

def profile_soundex_nl():
    n = Naam('Samuel Beckett')
    for i in range(0, 1000):
        n.soundex_nl(group=2, length=-1, cache_key='_soundex_nl_2_1')

from names.similarity import average_distance
 
def profile_average_distance():
    l1 = ['a', 'b', 'c']
    l2 = ['a', 'c', 'd', 'e', 'f']
    l3 = ['x', 'y', 'b']
    def f(x, y):
        return x == y
    for i in range(0, 10000):
        average_distance(l1, l2, f)
        average_distance(l2, l2, f)
        average_distance(l2, l3, f)
        average_distance(l3, l1, f)
        
if __name__ == "__main__":
    setUp()
    tf = tempfile.NamedTemporaryFile()
#    profile('profile_similarity()')
    profile('profile_average_distance()')
#    profile('profile_soundex_nl()')
    
