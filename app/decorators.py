# coding:utf-8
from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission


def permission_required(permission):
    # 用来检查常规权限
    def decorator(f):
        @wraps(f)
        # 使用装饰器时，被装饰后的函数已经是另外一个函数了，函数名等函数属性会发生变化
        # 这样的改变会对测试有所影响，所以这个wraps装饰器可以消除这样的副作用。
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)  # 用户没有权限就返回403错误码，即HTTP禁止错误
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    # 专门用来检查管理员权限
    return permission_required(Permission.ADMIN)(f)