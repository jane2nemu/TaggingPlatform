# coding=utf-8
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import json
from urllib2 import urlopen

engine1 = create_engine('mysql+mysqlconnector://whaley:yelahw@172.16.16.134/ota20?charset=utf8', echo=False)
engine2 = create_engine('mysql+mysqlconnector://root:123@127.0.0.1/test', echo=False)
DBSession1 = sessionmaker(bind=engine1)
DBSession2 = sessionmaker(bind=engine2)
session1 = DBSession1()
session2 = DBSession2()
Base = declarative_base()

json_url = "http://vod.aginomoto.com/Service/V3/Program?sid=%s"


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

query1 = session1.query(PicLabel)

class Check(Base):
    __tablename__ = 'check'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }
    id = Column(Integer)
    sid = Column(String(255), primary_key=True)
    actor = Column(String(255), primary_key=True)
    status = Column(Integer, default=0)

query2 = session2.query(Check)


sids = set()

squerys = query1.all()
for sq in squerys:
    if sq.sid not in sids:
        sids.add(sq.sid)


sid_actors = {"g68sacc3hjb2": [u"殷桃",u"张译",u"陶泽如",u"张佳宁",u"高姝瑶",u"吴其江",u"林伊婷"],
              "5i234fcd3f6l": [u"杨旭文",u"李一桐",u"陈星旭",u"孟子义",u"赵立新"],
              "g6n8acuve5gh": [u"陈晓",u"袁姗姗",u"郭晓东",u"蒋梦婕",u"张哲瀚",u"米热",u"臧洪娜",u"蔡文静"]
              }
sa_keys = sid_actors.keys()

for sid in sids:
    print ">>>>sid ", sid
    body = urlopen(json_url % sid).read()
    json_dict = json.loads(body)
    actors = json_dict.get("program", {}).get("metadata", {}).get("cast", [])
    if not actors:
        if sid in sa_keys:
            actors = sid_actors[sid]
    for actor in actors:
        if not query2.filter(Check.sid == sid, Check.actor == actor).first():
            print actor
            session2.add(Check(sid=sid, actor=actor))
            session2.commit()


