from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
repo = Table('repo', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('repourl', String),
    Column('user_id', Integer),
)

rpstry = Table('rpstry', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('repourl', String(length=140)),
    Column('user_id', Integer),
)

file = Table('file', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('filename', String),
    Column('type', String),
    Column('user_id', Integer),
)

file = Table('file', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('filename', String(length=140)),
    Column('type', String(length=140)),
    Column('repo_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['repo'].drop()
    post_meta.tables['rpstry'].create()
    pre_meta.tables['file'].columns['user_id'].drop()
    post_meta.tables['file'].columns['repo_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['repo'].create()
    post_meta.tables['rpstry'].drop()
    pre_meta.tables['file'].columns['user_id'].create()
    post_meta.tables['file'].columns['repo_id'].drop()
