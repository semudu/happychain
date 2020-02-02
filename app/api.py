import logging
from collections import OrderedDict
from typing import OrderedDict

import flask_excel as excel
from flask import Flask, request, jsonify

from .core.database import Database
from .core.model.content import Content
from .core.service import Service

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)


def create_app(config):
    db = Database(config)
    bip = Service(config)

    app = Flask(__name__)
    excel.init_excel(app)
    app.config.from_object(config)

    @app.route("/")
    def get():
        logging.debug("first call!")
        return "Pitika!!!"

    @app.route("/scope", methods=["POST"])
    def create_scope():
        try:
            if request.is_json:
                content = request.get_json()
                scope_name = content["name"]
                if scope_name:
                    scope_id = db.add_scope(scope_name)
                    return "Scope Created with id: %s" % scope_id, 201
                else:
                    return "Scope name is empty!", 500
        except Exception as e:
            print("Scope create exception: %s" % str(e))
            return "An error occurred", 500

    @app.route("/team", methods=["POST"])
    def create_team():
        try:
            if request.is_json:
                content = request.get_json()
                scope_id = content["scope_id"]
                team_name = content["name"]
                if team_name:
                    team_id = db.add_team(team_name, scope_id)
                    return "Team Created with id: %s" % team_id, 201
                else:
                    return "Team name is empty!", 500
        except Exception as e:
            print("Team create exception: %s" % str(e))
            return "An error occurred", 500

    @app.route("/team/<team_id>", methods=["PUT"])
    def update_team(team_id):
        try:
            if request.is_json:
                content = request.get_json()
                team_name = content["name"]
                if team_name:
                    db.update_team(team_id, team_name)
                    return "Team Updated", 200
                else:
                    return "Team name is empty!", 500
        except Exception as e:
            print("Team update exception: %s" % str(e))
            return "An error occurred", 500

    @app.route("/team/<team_id>", methods=["DELETE"])
    def delete_team(team_id):
        try:
            db.delete_team(team_id)
            return "Team Deleted.", 200
        except Exception as e:
            print("Team delete exception: %s" % str(e))
            return "An error occurred", 500

    @app.route("/team", methods=["GET"])
    def get_teams():
        try:
            return jsonify({"result": db.get_teams()})
        except Exception as e:
            print("Team retrieve exception: %s" % str(e))
            return "An error occurred", 500

    @app.route("/user/upload", methods=["GET", "POST"])
    def upload_user_list():
        if request.method == "POST":
            return jsonify({"result": request.get_array(field_name="file")})
        else:
            data = OrderedDict
            data.update({"Sheet 1": [
                ["MSISDN", "İsim", "Soyisim", "Cinsiyet (E/K)", "Doğum Tarihi (Gün/Ay/Yıl)", "Takım"],
                ["533210xxxx", "-", "-", "E", "01/01/1999", "ICT-AIAS-DAS-DMD"]]})
            return excel.make_response_from_book_dict(data, file_type="xlsx", file_name="user_list")

    @app.route("/user", methods=["POST"])
    def create_user():
        try:
            if request.is_json:
                content = request.get_json()
                first_name = content["first_name"]
                last_name = content["last_name"]
                gender = content["gender"]
                date_of_birth = content["date_of_birth"]
                msisdn = content["msisdn"]
                passwd = content["passwd"]
                team_id = content["team_id"]
                if first_name and last_name and gender and date_of_birth and msisdn and passwd and team_id:
                    db.add_user(msisdn, first_name, last_name, gender, date_of_birth, passwd, team_id)
                    return "User Created.", 201
                else:
                    return "first_name, last_name, gender, date_of_birth, msisdn, passwd or team_id is empty!", 500
        except Exception as e:
            print("User create exception: %s" % str(e))
            return "An error occurred", 500

    @app.route("/user/<id>", methods=["DELETE"])
    def delete_user(id):
        try:
            db.delete_user(id)
            return "User Deleted.", 200
        except Exception as e:
            print("User delete exception: %s" % str(e))
            return "An error occurred", 500

    @app.route("/user", methods=["GET"])
    def get_users():
        try:
            return jsonify({"result": db.get_users()})
        except Exception as e:
            print("Team create exception: %s" % str(e))
            return "An error occurred", 500

    @app.route("/bip", methods=["POST"])
    def bip_process():
        if request.is_json:
            logging.debug(request.get_json())
            bip.process_request(Content(request.get_json()))
            return 'JSON posted'
        else:
            return "Content Type must be JSON!"

    return app
