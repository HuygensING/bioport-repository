#Introduction
#============
#
#This aim of this package is to offer a simple but flexible way to
#configure SQLAlchemy's scoped session support using the Zope component
#architecture. This package is based on ``zope.sqlalchemy``, which
#offers transaction integration between Zope and SQLAlchemy.
#
#We sketch out two main scenarios here:
#
#* one database per Zope instance.
#
#* one database per site (or Grok application) in a Zope instance
#  (and thus multiple databases per Zope instance).
#
#GloballyScopedSession (one database per Zope instance)
#======================================================
#
#The simplest way to set up SQLAlchemy for Zope is to have a single
#thread-scoped session that's global to your entire Zope
#instance. Multiple applications will all share this session. The
#engine is set up with a global utility.
#
#We use the SQLAlchemy ``sqlalchemy.ext.declarative`` extension to
#define some tables and classes::
#
#  >>> from sqlalchemy import *
#  >>> from sqlalchemy.ext.declarative import declarative_base
#  >>> from sqlalchemy.orm import relation
#
#  >>> Base = declarative_base()
#  >>> class User(Base):
#  ...     __tablename__ = 'test_users'
#  ...     id = Column('id', Integer, primary_key=True)
#  ...     name = Column('name', String(50))
#  ...     addresses = relation("Address", backref="user")
#  >>> class Address(Base):
#  ...     __tablename__ = 'test_addresses'
#  ...     id = Column('id', Integer, primary_key=True)
#  ...     email = Column('email', String(50))
#  ...     user_id = Column('user_id', Integer, ForeignKey('test_users.id'))
#
#So far this doesn't differ from the ``zope.sqlalchemy`` example. We
#now arrive at the first difference. Instead of making the engine
#directly, we can set up the engine factory as a (global) utility. This
#utility makes sure an engine is created and cached for us.
#
from z3c.saconfig import EngineFactory
TEST_DSN = ''
#  >>> engine_factory = EngineFactory(TEST_DSN)
engine_factory = EngineFactory(TEST_DSN)
#
#You can pass the parameters you'd normally pass to
#``sqlalchemy.create_engine`` to ``EngineFactory``. 
#
#We now register the engine factory as a global utility using
#``zope.component``. Normally you'd use either ZCML or Grok to do this
#confirmation, but we'll do it manually here::::
#
from zope import component
from z3c.saconfig.interfaces import IEngineFactory
# XXX we probably want to set this up via zcml, to have conflict check etc
component.provideUtility(engine_factory, provides=IEngineFactory)
#
#Note that setting up an engine factory is not actually necessary in
#the globally scoped use case. You could also just create the engine as
#a global and pass it as ``bind`` when you create the
#``GloballyScopedSession`` later.
#
#Let's look up the engine by calling the factory and create the tables
#in our test database::
#
engine = engine_factory()
#Base.metadata.create_all(engine)
#
#Now as for the second difference from ``zope.sqlalchemy``: how the
#session is set up and used. We'll use the ``GloballyScopedSession``
#utility to implement our session creation::
#
from z3c.saconfig import GloballyScopedSession
#
#We give the constructor to ``GloballyScopedSession`` the parameters
#you'd normally give to ``sqlalchemy.orm.create_session``, or
#``sqlalchemy.orm.sessionmaker``::
#
#  >>> utility = GloballyScopedSession(twophase=TEST_TWOPHASE)
utility = GloballyScopedSession()
#
#``GlobalScopedSession`` looks up the engine using ``IEngineFactory``
#if you don't supply your own ``bind``
#argument. ``GloballyScopedSession`` also automatically sets up the
#``autocommit``, ``autoflush`` and ``extension`` parameters to be the
#right ones for Zope integration, so normally you wouldn't need to
#supply these, but you could pass in your own if you do need it.
#
#We now register this as an ``IScopedSession`` utility::
#  
from z3c.saconfig.interfaces import IScopedSession
component.provideUtility(utility, provides=IScopedSession)
# 
#We are done with configuration now. As you have seen it involves
#setting up two utilities, ``IEngineFactory`` and ``IScopedSession``,
#where only the latter is really needed in this globally shared session
#use case. 
#
#After the ``IScopedSession`` utility is registered, one can import the
#``Session`` class from z3c.saconfig.  This ``Session`` class is like
#the one you'd produce with ``sessionmaker`` from
#SQLAlchemy. `z3c.saconfig.Session`` is intended to be the only
#``Session`` class you'll ever need, as all configuration and Zope
#integration is done automatically for you by ``z3c.saconfig``,
#appropriate the context in Zope where you use it. There is no need to
#create ``Session`` classes yourself with ``sessionmaker`` or
#``scoped_sesion`` anymore.
#
#We can now use the ``Session`` class to create a session which will
#behave according to the utility we provided::
#
from z3c.saconfig import Session
session = Session()
#
#Now things go the usual ``zope.sqlalchemy`` way, which is like
#``SQLAlchemy`` except you can use Zope's ``transaction`` module::
#
#  >>> session.query(User).all()
#  []    
#  >>> import transaction
#  >>> session.add(User(name='bob'))
#  >>> transaction.commit()
#
#  >>> session = Session()
#  >>> bob = session.query(User).all()[0]
#  >>> bob.name
#  u'bob'
#  >>> bob.addresses
#  []

