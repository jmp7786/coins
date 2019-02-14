import sys
from os.path import dirname
from configs.common import conf

sys.path.append(dirname(__file__)+'/..')

from sqlalchemy import create_engine
engine = create_engine('mysql://{}:{}@{}:{}/{}?charset=utf8'.format(conf['MYSQL']['id'], conf['MYSQL']['pw'], conf['MYSQL']['host'], conf['MYSQL']['port'], conf['MYSQL']['db']), echo=True, pool_pre_ping=True)

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()
