from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
post = Table('post', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('body', String),
    Column('timestamp', DateTime),
    Column('user_id', Integer),
)

language = Table('language', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('filetype', String),
    Column('run', String),
    Column('syntax', String),
    Column('interpreted', Boolean),
    Column('includetype', Boolean),
    Column('modulename', String),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['post'].drop()
    pre_meta.tables['language'].columns['includetype'].drop()
    pre_meta.tables['language'].columns['run'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['post'].create()
    pre_meta.tables['language'].columns['includetype'].create()
    pre_meta.tables['language'].columns['run'].create()
