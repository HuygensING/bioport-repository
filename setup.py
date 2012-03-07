from setuptools import setup

setup(name = 'bioport_repository',
      packages = ['bioport_repository', 
                  'bioport_repository/similarity',
                 ],

      install_requires=['gerbrandyutils',

                        'biodes',
                        'plone.memoize',
                        'sqlalchemy',
                        'names',
                        'simplejson',
                        'zope.sqlalchemy',
                       ],
      )
