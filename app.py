from flask import Flask, request, jsonify, abort
import db_session
from datetime import datetime, timedelta
from items import Items
from history import History


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


@app.route('/imports', methods=["POST"])
def imports():
    ids = ""
    items = request.json['items']
    date = datetime.strptime(request.json['updateDate'], "%Y-%m-%dT%H:%M:%SZ")
    db_sess = db_session.create_session()
    try:
        for item in items:
            old_item = db_sess.query(Items).filter(Items.id == item.get("id", None)).first()
            if old_item:
                if ids.find(item["id"]) != -1:
                    db_sess.close()
                    abort(400)
                ids += item["id"] + " "
                if item.get("url", None):
                    old_item.url = item["url"]
                if item.get("parentId", None):
                    par = db_sess.query(Items).filter(Items.parentId == item["parentId"]).first()
                    if par.type == "FOLDER":
                        old_item.parentId = item["parentId"]
                if item.get("size", 0) <= 0:
                    db_sess.close()
                    abort(400)
                if item.get("size", None):
                    old_item.size = item["size"]
                old_item.date = date
                db_sess.add(History(item_id=old_item.id, body=str(old_item.get_dict()), date=date))
                db_sess.commit()
            else:
                if ids.find(item["id"]) != -1:
                    db_sess.close()
                    abort(400)
                ids += item["id"] + " "
                new_item = Items()
                if item.get("id", None) and item.get("type", None):
                    new_item.id = item["id"]
                    new_item.type = item['type']
                    new_item.date = date
                    if not item.get("size", None):
                        if item["type"] != "FOLDER":
                            abort(400)
                    else:
                        new_item.size = item['size']
                    if item.get("url", None):
                        new_item.url = item["url"]
                    if item.get("parentId", None):
                        par = db_sess.query(Items).filter(Items.id == item["parentId"]).first()
                        if par.type != "FOLDER":
                            db_sess.close()
                            abort(400)
                        par.date = date
                        while par.parentId:
                            par = db_sess.query(Items).filter(Items.id == par.parentId).first()
                            par.date = date
                        new_item.parentId = item["parentId"]
                else:
                    db_sess.close()
                    abort(400)
                db_sess.add(History(item_id=new_item.id, body=str(new_item.get_dict()), date=date))
                db_sess.add(new_item)
                db_sess.commit()
        db_sess.close()
    except ValueError:
        db_sess.close()
        abort(400)

    return {"code": 200}


@app.route('/delete/<item_id>', methods=["DELETE"])
def delete(item_id):
    db_sess = db_session.create_session()
    try:
        item = db_sess.query(Items).filter(Items.id == item_id).first()
        if not item:
            db_sess.close()
            abort(404)
        if item.type == "FOLDER":
            folders = [item.id]
            while folders:
                for child in db_sess.query(Items).filter(Items.parentId == folders[0]).all():
                    if child.type == 'FOLDER':
                        folders.append(child.id)
                    db_sess.query(History).filter(History.item_id == child.id).delete()
                    db_sess.delete(child)
                    db_sess.commit()
                folders.pop(0)
        db_sess.query(History).filter(History.item_id == item.id).delete()
        db_sess.delete(item)
        db_sess.commit()
        db_sess.close()
    except ValueError:
        db_sess.close()
        abort(400)
    return {"code": 200}


@app.route('/nodes/<item_id>', methods=["GET"])
def nodes(item_id):
    db_sess = db_session.create_session()
    try:
        item = db_sess.query(Items).filter(Items.id == item_id).first()
        if not item:
            db_sess.close()
            abort(404)
        out = item.get_dict()
        if out["type"] == "FOLDER":
            out["children"] = []
            folders = [out]
            while folders:
                for child in db_sess.query(Items).filter(Items.parentId == folders[0]["id"]).all():
                    child = child.get_dict()
                    child["children"] = None
                    folders[0]["children"].append(child)
                    if child["type"] == 'FOLDER':
                        folders.append(child)
                        folders[0]["children"][-1]["children"] = []
                folders.pop(0)
            for folder in [out] + out["children"]:
                if folder["type"] != "FOLDER":
                    continue
                folder["size"] = 0
                children = folder["children"][:]
                for child in children:
                    if child["type"] == 'FOLDER':
                        children += child["children"]
                    else:
                        folder["size"] += child["size"]
        else:
            out["children"] = None
        db_sess.close()
        return out
    except ValueError:
        db_sess.close()
        abort(400)


@app.route('/updates', methods=["GET"])
def updates():
    try:
        date = datetime.strptime(request.args.get('date'), "%Y-%m-%dT%H:%M:%SZ") - timedelta(hours=24)
        db_sess = db_session.create_session()
        files = db_sess.query(Items).filter(Items.date >= date, Items.type != "FOLDER").all()
        return jsonify([file.get_dict() for file in files])
    except ValueError:
        abort(400)


@app.route('/node/<item_id>/history', methods=["GET"])
def node(item_id):
    try:
        datestart = datetime.strptime(request.args.get('dateStart'), "%Y-%m-%dT%H:%M:%SZ")
        dateend = datetime.strptime(request.args.get('dateEnd'), "%Y-%m-%dT%H:%M:%SZ")
        db_sess = db_session.create_session()
        if not db_sess.query(History).filter(History.item_id == item_id).first():
            abort(404)
        if datestart and dateend:
            files = db_sess.query(History).filter(History.item_id == item_id,
                                                  datestart <= History.date, History.date <= dateend).all()
            return jsonify([file.get_dict() for file in files])
        else:
            files = db_sess.query(History).filter(History.item_id == item_id).all()
            return jsonify([file.get_dict() for file in files])
    except ValueError:
        abort(400)


if __name__ == '__main__':
    db_session.global_init("blog.db")
    app.run(debug=True, port=80, host="0.0.0.0")
