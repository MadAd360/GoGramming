from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
file = Table('file', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('filename', String(length=140)),
    Column('type', String(length=140)),
    Column('user_id', Integer),
)

repo = Table('repo', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('repourl', String(length=140)),
    Column('user_id', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['file'].create()
    post_meta.tables['repo'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['file'].drop()
    post_meta.tables['repo'].drop()
