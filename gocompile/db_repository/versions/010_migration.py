from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
language = Table('language', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('filetype', String(length=140)),
    Column('compile', String(length=140)),
    Column('location', String(length=140)),
    Column('run', String(length=140)),
    Column('syntax', String(length=140)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['language'].columns['location'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['language'].columns['location'].drop()
