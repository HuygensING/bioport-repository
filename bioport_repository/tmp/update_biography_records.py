from bioport_repository.repository import *

DB_CONNECTION = 'mysql://root@localhost/bioport'


#ÜPDATE NLŸU THOSE WITHOUT INFO!

def update_biographies(repo):

    for bio in repo.get_biographies():
        print bio
        repo.save_biography(bio, comment=u'update new field url_biography')
#        if 'bioport' in [s.id for s in person.get_sources()]:
#            print 'SET'
#            person.status = 2
#            repo.save_person(person)

if __name__ == "__main__":
    repo = Repository(db_connection=DB_CONNECTION) 
    update_biographies(repo)