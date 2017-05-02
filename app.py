#!/usr/bin/python
# coding=utf-8
"""
create on: 2017-04-26

@auther: zj

description: labelling platform
"""

import json
import random
from urllib2 import urlopen
from flask import render_template, jsonify, request
from label_app import app
from model import PicLabel, session, query

app.config.from_object('config')
baseurl = "../static/imgs/"
json_url = "http://vod.aginomoto.com/Service/V3/Program?sid=%s"

# def check():
#     cqs = query.filter(PicLabel.label == -1).all()
#     for cq in cqs:
#         if cq.aname == '':
#             cq.label = 0
#             session.commit()


def get_url(file_name):
    """查询获取图片信息"""
    uquery = query.filter(PicLabel.label == 0, PicLabel.title == file_name).first()
    url = baseurl + uquery.image_path
    img_hash = uquery.image_hash
    title = uquery.title
    episode = uquery.episode
    print episode
    frame_timestamp = uquery.frame_timestamp
    # # 多人标注处理
    # uquery.label = -1
    # # 覆盖原表
    # session.add(uquery)
    # session.commit()
    return url, img_hash, title, episode, frame_timestamp


def get_actors(sid):
    """获取主演名单"""
    body = urlopen(json_url % sid).read()
    json_dict = json.loads(body)
    actors = json_dict.get("program", {}).get("metadata", {}).get("cast", [])
    return actors[:10] + [u"不清晰"]


def get_sid(file_name):
    """获取sid"""
    uquerys = query.filter(PicLabel.label == 0, PicLabel.title == file_name).first()
    if uquerys:
        return uquerys.sid


@app.route('/')
def home():
    """选择列表页"""
    squerys = query.order_by('title').all()
    items = []
    for sq in squerys:
        if sq.title not in items:
            items.append(sq.title)
    return render_template('base.html', items=items)


@app.route('/files/<filename>')
def files(filename):
    """标注页信息"""
    # query = session.query(PicLabel)
    sid = get_sid(filename)
    actors = get_actors(sid)
    print str(actors)
    url, img_hash, title, episode, frame_timestamp = get_url(filename)
    return render_template('home.html', url=url, acts=actors, img_hash=img_hash, title=title,
                           episode=episode, frame_timestamp=frame_timestamp)


@app.route('/get_data', methods=["POST"])
def get_data():
    if request.method == "POST":
        rdict = {
            "aname": '',
            "img_hash": '',
            "title": '',
            "episode": '',
            "frame_timestamp": ''
        }
    for item in rdict:
        rdict[item] = request.values.get(item, '')
    row = query.filter_by(image_hash=rdict["img_hash"])
    row.update({PicLabel.aname: rdict["aname"]})
    if rdict["aname"] == u"不清晰":
        row.update({PicLabel.valid: 0})
    row.update({PicLabel.label: 1})
    session.commit()
    # print ">>>title", rdict["title"]
    url, img_hash, title, episode, frame_timestamp = get_url(rdict["title"])
    return jsonify(url=url, img_hash=img_hash, title=title, episode=episode, frame_timestamp=frame_timestamp)


if __name__ == "__main__":
    app.run(host='0.0.0.0')
