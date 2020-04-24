import threading
from collections import OrderedDict
from flask import Blueprint, request, jsonify
from flask_basicauth import BasicAuth

from app.channel import run_bip_command
from app.commons.common import import_user_array, database
from app.commons.log import get_logger

import flask_excel as excel

api = Blueprint('api', __name__, None)
api.config = {}
basic_auth = BasicAuth(api)

logger = get_logger(__name__)


@api.record
def record_params(setup_state):
    app = setup_state.app
    api.config = dict([(key, value) for (key, value) in app.config.items()])


@api.route("/")
def get():
    return "Pitika!!!"


@api.route("/transaction/received/team/<team_id>/limit/<limit>")
@basic_auth.required
def get_team_transactions(team_id, limit):
    try:
        return jsonify({"result": database.get_received_messages_by_team(team_id, limit)})
    except Exception as e:
        print("Transactions retrieve exception: %s" % str(e))
        return "An error occurred", 500


@api.route("/scope", methods=["POST"])
@basic_auth.required
def create_scope():
    try:
        if request.is_json:
            content = request.get_json()
            scope_name = content["name"]
            if scope_name:
                scope_id = database.add_scope(scope_name)
                return "Scope Created with id: %s" % scope_id, 201
            else:
                return "Scope name is empty!", 500
    except Exception as e:
        print("Scope create exception: %s" % str(e))
        return "An error occurred", 500


@api.route("/scope", methods=["GET"])
@basic_auth.required
def get_scopes():
    try:
        return jsonify({"result": database.get_scopes()})
    except Exception as e:
        print("Team retrieve exception: %s" % str(e))
        return "An error occurred", 500


@api.route("/team", methods=["POST"])
@basic_auth.required
def create_team():
    try:
        if request.is_json:
            content = request.get_json()
            scope_id = content["scope_id"]
            team_name = content["name"]
            if team_name:
                team_id = database.add_team(team_name, scope_id)
                return "Team Created with id: %s" % team_id, 201
            else:
                return "Team name is empty!", 500
    except Exception as e:
        print("Team create exception: %s" % str(e))
        return "An error occurred", 500


@api.route("/team/<team_id>", methods=["PUT"])
@basic_auth.required
def update_team(team_id):
    try:
        if request.is_json:
            content = request.get_json()
            team_name = content["name"]
            scope_id = content["scope_id"]
            if team_name:
                database.update_team(team_id, team_name, scope_id)
                return "Team Updated", 200
            else:
                return "Team name is empty!", 500
    except Exception as e:
        print("Team update exception: %s" % str(e))
        return "An error occurred", 500


@api.route("/team/<team_id>", methods=["DELETE"])
@basic_auth.required
def delete_team(team_id):
    try:
        database.delete_team(team_id)
        return "Team Deleted.", 200
    except Exception as e:
        print("Team delete exception: %s" % str(e))
        return "An error occurred", 500


@api.route("/team", methods=["GET"])
@basic_auth.required
def get_teams():
    try:
        return jsonify({"result": database.get_teams()})
    except Exception as e:
        print("Team retrieve exception: %s" % str(e))
        return "An error occurred", 500


@api.route("/user/upload", methods=["GET", "POST"])
@basic_auth.required
def upload_user_list():
    try:
        if request.method == "POST":
            user_array = request.get_array(field_name="file")
            if user_array is not None:
                result = jsonify({"result": import_user_array(user_array)})
            else:
                return "file not found."

            return result
        else:
            data = OrderedDict
            data.update({"Sheet 1": [
                ["MSISDN", "İsim", "Soyisim", "Cinsiyet (E/K)", "Doğum Tarihi (Gün.Ay.Yıl)", "Takım"],
                ["533210xxxx", "-", "-", "E", "01.01.1999", "ICT-AIAS-DAS-DMD"]]})

            return excel.make_response_from_book_dict(data, file_type="xlsx", file_name="user_list")
    except Exception as e:
        print("User import exception: %s" % str(e))
        return "An error occurred", 500


@api.route("/user", methods=["POST"])
@basic_auth.required
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
                database.__add_user(msisdn, first_name, last_name, gender, date_of_birth, passwd, team_id)
                return "User Created.", 201
            else:
                return "first_name, last_name, gender, date_of_birth, msisdn, passwd or team_id is empty!", 500
    except Exception as e:
        print("User create exception: %s" % str(e))
        return "An error occurred", 500


@api.route("/user/<user_id>", methods=["DELETE"])
@basic_auth.required
def delete_user(user_id):
    try:
        database.delete_user(user_id)
        return "User Deleted.", 200
    except Exception as e:
        print("User delete exception: %s" % str(e))
        return "An error occurred", 500


@api.route("/user", methods=["GET"])
@basic_auth.required
def get_users():
    try:
        return jsonify({"result": database.get_users()})
    except Exception as e:
        print("Team create exception: %s" % str(e))
        return "An error occurred", 500


@api.route("/bip", methods=["POST"])
def bip_process():
    try:
        if request.is_json:
            t = threading.Thread(target=run_bip_command, args=(request.get_json(),))
            t.start()
        return "", 200

    except Exception as e:
        print("Bip process exception: %s" % str(e))
        return "", 500
