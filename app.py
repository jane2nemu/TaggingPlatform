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
from model import PicLabel, CheckActor, session, query, queryc

app.config.from_object('config')
baseurl = "../static/imgs/"
json_url = "http://vod.aginomoto.com/Service/V3/Program?sid=%s"


def get_url(file_name):
    """获取图片信息"""
    uquery = query.filter(PicLabel.label == 0, PicLabel.title == file_name).first()
    url = baseurl + uquery.image_path
    img_hash = uquery.image_hash
    title = uquery.title
    episode = uquery.episode
    print episode
    frame_timestamp = uquery.frame_timestamp
    return url, img_hash, title, episode, frame_timestamp


def get_actors(sid):
    """获取主演名单"""
    body = urlopen(json_url % sid).read()
    json_dict = json.loads(body)
    actors = json_dict.get("program", {}).get("metadata", {}).get("cast", [])
    return actors


def get_sid(file_name):
    """获取sid"""
    uquery = query.filter(PicLabel.label == 0, PicLabel.title == file_name).first()
    if uquery:
        return uquery.sid


def get_cur_actors(sid):
    """获取未标注过演员名单"""
    actors = get_actors(sid)
    querycs = queryc.filter(CheckActor.sid == sid).all()
    for qactor in querycs:
        if qactor.status == 1:
            actors.remove(qactor.actor)
    return actors[:10] + [u"不保留", u"跳过"]


def get_home_items():
    """获取剧名列表"""
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
    if len(actors) == 2:
        """跳回选择列表页"""
        items = get_home_items()
        return render_template('base.html', items=items)
    else:
        url, img_hash, title, episode, frame_timestamp = get_url(filename)
        return render_template('home.html', url=url, acts=actors, img_hash=img_hash, title=title,
                           episode=episode, frame_timestamp=frame_timestamp)


@app.route('/get_data', methods=["POST"])
def get_data():
    if request.method == "POST":
        rdict = {
            "aname": '',
            "img_hash": '',
            "title": ''
        }
    for item in rdict:
        rdict[item] = request.values.get(item, '')
    row = query.filter_by(image_hash=rdict["img_hash"])
    row2 = queryc.filter(CheckActor.actor == rdict["aname"])
    if rdict["aname"] is not u"不保留" and rdict["aname"] is not u"跳过":
        row.update({PicLabel.aname: rdict["aname"]})
    if rdict["aname"] == u"不保留":
        row.update({PicLabel.valid: 0})
    if rdict["aname"] is not u"跳过":
        row.update({PicLabel.label: 1})
        row2.update({CheckActor.status: 1})
    session.commit()
    url, img_hash, title, episode, frame_timestamp = get_url(rdict["title"])
    return jsonify(url=url, img_hash=img_hash, title=title, episode=episode, frame_timestamp=frame_timestamp)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
