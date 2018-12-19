# coding:utf-8
# 跟前面在auth中创建蓝本的方式一样
from flask import Blueprint

api = Blueprint('api', __name__)

from . import authentication, comments, decorators, errors, posts, users