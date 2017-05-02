# coding=utf-8
"""
create on: 2017-04-26

@auther: zj

description: model.py
"""

from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('mysql+mysqlconnector://whaley:yelahw@172.16.16.134/ota20?charset=utf8mb4', echo=False)

DBSession = sessionmaker(bind=engine)
session = DBSession()
Base = declarative_base()


class PicLabel(Base):
    __tablename__ = 'screenshot'

    id = Column(Integer, primary_key=True)
    sid = Column(String(255))
    title = Column(String(255))
    episode = Column(Integer)
    video_type = Column(String(255))
    image_hash = Column(String(255))
    frame_timestamp = Column(String(255))
    image_path = Column(String(255))
    aname = Column(String(255))
    label = Column(Integer)
    valid = Column(Integer)
    create_date = Column(DateTime)
    update_date = Column(DateTime)

query = session.query(PicLabel)

# def init_db():
#     '''
#     初始化数据库
#     :return:
#     '''
#     BaseModel.metadata.create_all(engine)
#
#
# def drop_db():
#     '''
#     删除所有数据表
#     :return:
#     '''
#     BaseModel.metadata.drop_all(engine)
#
#
# drop_db()
# init_db()



