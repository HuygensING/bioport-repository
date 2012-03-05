from pprint import pprint
from names import Name
import re
import csv
import codecs
from bioport_repository import repository

class Person():
    def __init__(self, d):
        self._d = d
    
    @property
    def sex(self):
        return self._d['sex']
    
    @property
    def birth(self):
        events =  self._d.get('event')
        if not events:
            return
        for event in events:
            if event['type'] == 'birth':
                return event['when']
    @property
    def birthyear(self):
        b = self.birth
        if b:
            return int(b[:4])
        else:
            return
     
    @property
    def death(self):
        events =  self._d.get('event')
        if not events:
            return
        for event in events:
            if event['type'] == 'death':
                return event['when']
    @property
    def deathyear(self):
        b = self.death
        if b:
            return int(b[:4])
        else:
            return
    
    @property
    def century(self): 
        y = self.birthyear
        if y:
            y = y + 20
            return (y/100) 
    @property
    def category_ids(self):
        return self._d.get('categories', [])
    @property
    def biographies(self):
        return self._d.get('biographies', [])
    
    @property
    def source_ids(self):
        result = []
        for bio in self.biographies:
            source_id = bio.get('source_id')
            result.append(source_id)
        return result
    
    @property
    def namen(self):
        return self._d.get('namen')
    
    @property 
    def voornamen(self):
        naam = self.namen[0]
        name = Name(naam)
        name._guess_constituents()
        result = []
        for token in name._tokens:
            if token.ctype() == 'voornaam':
                s = token.word()
                if not re.match('.\.', s):
                    result.append(s)
        return result
    
CENTURIES = ['total'] +  range(1, 20) + [None] 
class Analyzer:
    def __init__(self): 
        self.repo = repository.Repository(dsn='mysql://root@localhost/bioport')
    @property
    def century_counter(self):
        return dict([(c, 0) for c in CENTURIES]) 
    
    def read_data(self):
        fn = 'persons_all.py'
        self._data = eval(open(fn).read())
        return self._data
    
    def persons(self):
        for d in self._data:            
            yield Person(self._data[d])
     
    def _create_test_set(self):
        d = {}
        for k in self._data.keys()[:1000]:
            d[k] = self._data[k]
        fn = 'persons_selection.py'
        open(fn, 'w').write(unicode(d))
        
    def read_test_set(self):
        fn = 'persons_selection.py'
        self._data = eval(open(fn).read())


    
    def centuryXsex(self):
        d = dict(all =  dict(total=0,m=0, f = 0, other=0 ))
        for p in self.persons():
            if p.century not in d:
                d[p.century] = dict(total=0,m=0, f = 0, other=0 )
            d['all']['total'] += 1
            d[p.century]['total'] += 1
            if p.sex == '1':
                d['all']['m'] += 1
                d[p.century]['m'] += 1
            elif p.sex == '2':
                d['all']['f'] += 1
                d[p.century]['f'] += 1
            else:
                d['all']['other'] += 1
                d[p.century]['other'] += 1
        return d 
    
 
    def centuryXcategory(self):
        d = dict(total=dict(total_persons=0))
        for p in self.persons():
            if p.century not in d:
                d[p.century] = {}
                
            d['total']['total_persons'] += 1
            for category in p.category_ids:
                if category not in d[p.century]:
                    d[p.century][category] = 0
                if category not in d['total']:
                    d['total'][category] = 0
                d[p.century][category] += 1
                d['total'][category] += 1
        return d 
    
    def centuryXsource(self):
        d = dict(total=dict(total_persons=0))
        for p in self.persons():
            if p.century not in d:
                d[p.century] = {}
                
            d['total']['total_persons'] += 1
            for source_id in p.source_ids:
                if source_id not in d[p.century]:
                    d[p.century][source_id] = 0
                if source_id not in d['total']:
                    d['total'][source_id] = 0
                d[p.century][source_id] += 1
                d['total'][source_id] += 1
        return d 
#      def sourceXvariousdata(self): 
#        d = dict() #total=dict(total_persons=0))
#        for p in self.persons():
#            for source_id in p.source_ids:
#                if source_id not in d:
#                    d[source_id] = dict(total=0, sex ={'m':0, 'f':0, None:0}, category={}, century={}) 
#                d[source_id]['total'] += 1
#                d[source_id]['century'][p.century] = d[source_id]['century'].get(p.century, 0) + 1
#                if p.sex == '1':
#                    sex = 'm'
#                elif p.sex == '2':
#                    sex = 'f'
#                else:
#                    sex = None
#                d[source_id]['sex'][sex] = d[source_id]['sex'].get(sex, 0) + 1
#                for category_id in p.category_ids:
#                    d[source_id]['category'][category_id] = d[source_id]['sex'].get(category_id, 0) + 1
#    
#        fn = 'sourceXvariousdata.csv'  
#        writer = csv.writer(codecs.open(fn, 'w', 'utf8'))
#        cols = ['source'] + ['total'] + ['male',  'female', 'sexe onbekend'] +  CENTURIES
#        writer.writerow(cols)
#        for source_id in d:
#            x = d[source_id]
#            r = [source_id, x['total'], x['sex']['m'], x['sex']['f'], x['sex'][None] ]
#            r +=  [x['century'].get(c,0) for c in CENTURIES]
#            writer.writerow(r)
#            
#        return d 
    def sourceXtotals(self): 
        fn = 'sourceXtotals.csv'  
        cols = ['source', 'source_description'] + ['total'] + ['male',  'female', 'sexe onbekend']
        writer = csv.writer(codecs.open(fn, 'w', 'utf8'))
        writer.writerow(cols)
        for source in self.repo.get_sources():
            if source.id == 'bioport':
                continue
            row = []
            row.append(source.id)
            row.append(source.description)
            row.append(self.repo.count_persons(source_id=source.id))
            row.append(self.repo.count_persons(source_id=source.id, geslacht=1))
            row.append(self.repo.count_persons(source_id=source.id, geslacht=2))
            print row
            writer.writerow(row)
        
        return
    
    def sourceXcentury(self):
        fn = 'sourceXcentury.csv'  
        centuries = range(14,20)
        
        cols = ['source', 'source_description'] + ['total'] + ['%se eeuw' % (c + 1) for c in centuries]
        writer = csv.writer(codecs.open(fn, 'w', 'utf8'))
        writer.writerow(cols)
        for source in self.repo.get_sources():
            if source.id == 'bioport':
                continue
            row = []
            row.append(source.id)
            row.append(source.description)
            row.append(self.repo.count_persons(source_id=source.id))
            for c in centuries:
                row.append(self.repo.count_persons(source_id=source.id, 
                               geboortejaar_min = unicode((c*100)-20),
                               geboortejaar_max = unicode((c*100)+80)
                    ))
            print row
            writer.writerow(row)
        
        return
    def sourceXcategory(self):
        fn = 'sourceXcategory.csv'  
        categories = self.repo.get_categories()
        print dir(categories[0])
        cols = ['source', 'source_description', 'total'] + [c.name for c in categories]
        writer = csv.writer(codecs.open(fn, 'w', 'utf8'))
        writer.writerow(cols)
        print cols
        for source in self.repo.get_sources():
            if source.id == 'bioport':
                continue
            row = []
            row.append(source.id)
            row.append(source.description)
            row.append(self.repo.count_persons(source_id=source.id))
            for c in categories:
                row.append(self.repo.count_persons(source_id=source.id, 
                               category=c.id
                    ))
            print row
            writer.writerow(row)
        
        return        
    def centuryXage(self):
        d = dict(total=dict(total_persons=0))
        for p in self.persons():
            if p.century not in d:
                d[p.century] = {}
                
            d['total']['total_persons'] += 1
            for category in p.category_ids:
                if category not in d[p.century]:
                    d[p.century][category] = 0
                if category not in d['total']:#        return d 
                    d['total'][category] = 0
                d[p.century][category] += 1
                d['total'][category] += 1
        return d 
    
    def voornamen_voor_els(self):
        d = dict() #total=0) 
        for p in self.persons():
            if p.sex == '2':
                for naam in p.voornamen:
                    if naam not in d:
                        d[naam] = self.century_counter
                    d[naam]['total'] += 1
                    d[naam][p.century] += 1
        self.save(d, 'voornamen_voor_els.csv')
        #write these data to a nice sheet
        return d 

    def save(self,d, fn):
        writer = csv.writer(codecs.open(fn, 'w', 'utf8'))
        headers = ['naam'] + CENTURIES
        writer.writerow(headers)
        
         
        for name in d:
            writer.writerow([name] + [d[name][c] for c in CENTURIES])
        
        return

       
if __name__ == '__main__':
    analyzer = Analyzer()
    print 'reading data'
#    analyzer.read_data()
    print 'done'    
#    analyzer._create_test_set()= d[naam].get('total', 0) +
    analyzer.read_test_set()
    print 'done'
    print 'sourceXvariousdata'
    pprint(analyzer.sourceXcategory())
    pprint(analyzer.sourceXtotals())
    pprint(analyzer.sourceXcentury())
#    print 'centuryXsource'
#    pprint(analyzer.centuryXsource())
#    print 'centuryXsex'
#    pprint(analyzer.centuryXsex())
#    print 'centuryXcategory'
#    pprint(analyzer.centuryXcategory())
#    print 'voornamen'
#    pprint(analyzer.voornamen_voor_els())
    print 'done'    