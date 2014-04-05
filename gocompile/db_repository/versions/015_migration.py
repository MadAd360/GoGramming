from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
language = Table('language', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('filetype', String),
    Column('compile', String),
    Column('run', String),
    Column('syntax', String),
    Column('location', String),
    Column('file', Boolean),
    Column('interpreted', Boolean),
    Column('includetype', Boolean),
)

language = Table('language', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('modulename', String(length=140)),
    Column('filetype', String(length=140)),
    Column('interpreted', Boolean, default=ColumnDefault(False)),
    Column('run', String(length=140)),
    Column('includetype', Boolean, default=ColumnDefault(False)),
    Column('syntax', String(length=140)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['language'].columns['compile'].drop()
    pre_meta.tables['language'].columns['file'].drop()
    pre_meta.tables['language'].columns['location'].drop()
    post_meta.tables['language'].columns['modulename'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['language'].columns['compile'].create()
    pre_meta.tables['language'].columns['file'].create()
    pre_meta.tables['language'].columns['location'].create()
    post_meta.tables['language'].columns['modulename'].drop()
