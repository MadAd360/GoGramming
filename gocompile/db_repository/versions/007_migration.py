from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
error = Table('error', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('path', String(length=140)),
    Column('filename', String(length=140)),
    Column('type', Text),
    Column('repo_id', Integer),
)

language = Table('language', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('filetype', String(length=140)),
    Column('compile', String(length=140)),
    Column('run', String(length=140)),
    Column('syntax', String(length=140)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['error'].create()
    post_meta.tables['language'].columns['syntax'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['error'].drop()
    post_meta.tables['language'].columns['syntax'].drop()
