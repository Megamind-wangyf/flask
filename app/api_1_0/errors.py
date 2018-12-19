from flask import jsonify

from app.api_1_0 import api
from app.exceptions import ValidationError


def bad_request(message):
    response = jsonify({'error': 'Bad Request', 'message': message})
    response.status_code = 400
    return response


def unauthorized(message):
    response = jsonify({'error': 'unauthorized', 'message': message})
    response.status_code = 401
    return response


def forbidden(message):
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response


def method_not_allow(message):
    response = jsonify({'error': 'method not allow', 'message': message})
    response.status_code = 405
    return response



@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])