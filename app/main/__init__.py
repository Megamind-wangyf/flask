#coding: utf-8
from flask import Blueprint
# 实例化一个蓝本对象
main = Blueprint('main', __name__)  # 两个参数：蓝本的名字和蓝本所在的包或者模块

from . import views, errors  # 末尾导入