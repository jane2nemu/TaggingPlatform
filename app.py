#!/usr/bin/python
# coding=utf-8
"""
create on: 2017-04-26

@auther: zj

description: labelling platform
"""

import json
from urllib2 import urlopen
from flask import render_template, jsonify, request
from label_app import app
from model import PicLabel, CheckActor, session, query, queryc, DBSession
import sqlalchemy
from sqlalchemy import or_
import os
import hashlib

app.config.from_object('config')
baseurl = "../static/imgs/"
json_url = "http://vod.aginomoto.com/Service/V3/Program?sid=%s"

def get_url(file_name):
    """获取图片信息"""
    session = DBSession()
    session.expire_on_commit = False
    # offset_limit = session.query(PicLabel).filter(PicLabel.label == 0, PicLabel.title == file_name).count()
    # offset_row = int(hashlib.sha1(os.urandom(10)).hexdigest(), 16) % offset_limit
    # #offset_row = random.randint(0, offset_limit)
    # uquery = session.query(PicLabel).filter(PicLabel.label == 0, PicLabel.title == file_name).offset(offset_row).first()

    curq = session.query(PicLabel).filter(PicLabel.current == 1, PicLabel.title == file_name).first()
    if not curq:
        uquery = session.query(PicLabel).filter(PicLabel.title == file_name, PicLabel.label == 0).order_by(PicLabel.episode,
                                                                                                           PicLabel.frame_timestamp).first()
    else:
        session.query(PicLabel).filter(PicLabel.image_hash == curq.image_hash).update({PicLabel.current: 0})
        uquerys = session.query(PicLabel).filter(
            PicLabel.title == file_name).filter(or_(PicLabel.label == 0,
                                                    PicLabel.image_hash == curq.image_hash)).order_by(PicLabel.episode,PicLabel.frame_timestamp).all()
        for idx, uquery in enumerate(uquerys):
            if uquery.image_hash == curq.image_hash:
                index = idx
        length = len(uquerys)
        uquery = uquerys[(index + 1) % length]
    session.query(PicLabel).filter(PicLabel.image_hash == uquery.image_hash).update({PicLabel.current: 1})
    session.commit()
    session.close()
    try:
        url = baseurl + uquery.image_path
        img_hash = uquery.image_hash
        title = uquery.title
        episode = uquery.episode
        #print episode
        frame_timestamp = uquery.frame_timestamp
        return url, img_hash, title, episode, frame_timestamp
    except:
        return None


def get_sid(file_name):
    """获取sid"""
    session = DBSession()
    session.expire_on_commit = False
    uquery = session.query(PicLabel).filter(PicLabel.label == 0, PicLabel.title == file_name).first()
    session.commit()
    session.close()
    if uquery:
        return uquery.sid


def get_actors(sid):
    """获取至少10个主演名单"""
    session = DBSession()
    session.expire_on_commit = False
    uquerys = session.query(CheckActor)
    uquery = uquerys.filter(CheckActor.sid == sid).all()
    session.commit()
    session.close()
    actors = [act.actor for act in uquery]
    return actors #[:10]


def get_cur_actors(sid):
    """获取未标注过主演名单"""
    actors = set(get_actors(sid))

    session = DBSession()
    session.expire_on_commit = False
    #querycs = session.query(CheckActor).filter(CheckActor.sid == sid).all()
    querycs = {obj.aname for obj in session.query(PicLabel.aname).filter(PicLabel.sid == sid).distinct() if obj.aname}
    session.commit()
    session.close()
    actors = actors - querycs

    '''
    for qactor in querycs:
        if qactor.status == 1:
            try:
                actors.remove(qactor.actor)
            except:
                continue
    '''

    return list(actors) + [u"不保留", u"上一张", u"跳过"]


def get_home_items():
    """获取剧名列表"""

    session = DBSession()

    sid_actor_num ={obj.sid:obj.num for obj in session.query(CheckActor.sid, sqlalchemy.sql.label('num',sqlalchemy.func.count(CheckActor.actor))).group_by(CheckActor.sid).all()}
    sid_label_num = {obj.sid:obj.num for obj in session.query(PicLabel.sid, sqlalchemy.sql.label('num',sqlalchemy.func.count(PicLabel.aname))).distinct().group_by(PicLabel.sid).all()}
    #sid_need_tag = {obj.sid for obj in session.query(CheckActor.sid, CheckActor.status).all() if not obj.status}
    sid_title = {obj.sid:obj.title for obj in session.query(PicLabel.sid, PicLabel.title).distinct()}
    nonempty_sid = {obj.sid for obj in session.query(PicLabel.sid).filter(PicLabel.label == 0).distinct()}
    session.commit()
    session.close()

    items = []
    for k, v in sid_title.items():
        if k not in sid_label_num: sid_label_num[k] = 0
        if sid_actor_num[k] > sid_label_num[k] and k in nonempty_sid: badge = 0
        else: badge = 1
        items.append({v: badge})


    '''
    querycs = session.query(CheckActor.sid).distinct()
    items = []
    for qs in querycs:
        title = query.filter(PicLabel.sid == qs.sid).first().title
        if title not in items:
            badge = 0
            status_set = queryc.filter(CheckActor.sid == qs.sid).all()
            cnt = 0
            for st in status_set:
                if st.status == 1:
                    cnt = cnt + 1
            if cnt == len(status_set):
                badge = 1
            items.append({title: badge})
    '''
    return items


@app.route('/')
def home():
    """选择列表页"""
    items = get_home_items()
    return render_template('base.html', items=items)


@app.route('/files/<filename>')
def files(filename):
    """标注页信息"""
    sid = get_sid(filename)
    actors = get_cur_actors(sid)
    if len(actors) == 3:
        """跳回选择列表页"""
        items = get_home_items()
        return render_template('base.html', items=items)
    else:
        img_obj = get_url(filename)
        # loop_limit = 10
        # while not img_obj and loop_limit > 0:
        #     img_obj = get_url(filename)
        #     loop_limit -= 1
        url, img_hash, title, episode, frame_timestamp = img_obj
        return render_template('home.html', url=url, acts=actors, img_hash=img_hash, title=title,
                           episode=episode, frame_timestamp=frame_timestamp)


@app.route('/get_data', methods=["POST"])
def get_data():
    #if request.method == "POST":
    rdict = {
        "aname": '',
        "img_hash": '',
        "title": ''
    }
    for item in rdict:
        rdict[item] = request.values.get(item, '')

    row_update_dict = {}
    row2_update_dict = {}

    if rdict["aname"] == u"不保留":
        row_update_dict['valid'] = 0
        row_update_dict['label'] = 1
    elif rdict["aname"] == u"上一张":
        session = DBSession()
        session.expire_on_commit = False
        session.query(PicLabel).filter(PicLabel.image_hash == rdict["img_hash"]).update({PicLabel.current: 0})
        uquerys = session.query(PicLabel).filter(PicLabel.title == rdict["title"]).filter(or_(PicLabel.label == 0,
                                                                                              PicLabel.image_hash == rdict["img_hash"])).order_by(PicLabel.episode,
                                                                                                                                                  PicLabel.frame_timestamp).all()
        for idx, uquery in enumerate(uquerys):
            if uquery.image_hash == rdict["img_hash"]:
                index = idx
        length = len(uquerys)
        uquery = uquerys[(length + index - 2) % length]
        session.query(PicLabel).filter(PicLabel.image_hash == uquery.image_hash).update({PicLabel.current: 1})
        session.commit()
        session.close()
    elif rdict["aname"] != u"跳过" and rdict["aname"] != u"上一张":
        row_update_dict['aname'] = rdict['aname']
        row_update_dict['label'] = 1
        # row2_update_dict['status'] = 1

    session = DBSession()
    try:
        if row_update_dict: session.query(PicLabel).filter_by(image_hash=rdict["img_hash"]).update(row_update_dict)
        if row2_update_dict:  session.query(CheckActor).filter(CheckActor.actor == rdict["aname"]).update(row2_update_dict)
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()


    #url, img_hash, title, episode, frame_timestamp = get_url(rdict["title"])
    #return jsonify(url=url, img_hash=img_hash, title=title, episode=episode, frame_timestamp=frame_timestamp)
    return jsonify({'error_code': 0})


if __name__ == "__main__":
    app.run(host='0.0.0.0')
