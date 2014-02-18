from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
error = Table('error', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('path', String),
    Column('filename', String),
    Column('type', Text),
    Column('repo_id', Integer),
)

error = Table('error', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('path', String(length=140)),
    Column('filename', String(length=140)),
    Column('message', Text),
    Column('repo_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['error'].columns['type'].drop()
    post_meta.tables['error'].columns['message'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['error'].columns['type'].create()
    post_meta.tables['error'].columns['message'].drop()
