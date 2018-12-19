# coding: utf-8

from ..models import User, AnonymousUser
from flask import g
import app
from flask_httpauth import HTTPBasicAuth
from app.api_1_0.errors import *

# 由于用户认证的功能只在API蓝本中实现，所以这个拓展的初始化只需要在这个蓝本包中初始化
auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(email_or_token, password):
    # 新版本认证中，认证参数可以是邮箱或者令牌
    if email_or_token == '':
        g.current_user = AnonymousUser()
        return True
    if password == '':
        # 如果密码为空，那么我们就假定这是令牌认证
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(email=email_or_token).first()
    if not user:
        return False
    # 把通过认证的用户保存在Flask的全局对象g中，这样视图函数便可以进行访问
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


# 认证密令不正确，我们自定义这个错误响应
@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
# API蓝本中所有的路由都能进行自动认证
def before_request():
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        # 这个函数是附加认证，拒绝已经通过认证但是没有确认账户的用户
        return forbidden('Uncomfirmed account')


@api.route('/token')
# 用于生成认证令牌的路由
def get_token():
    if g.current_user.is_anonymous() or g.token_used:
        # 为了避免客户端使用旧的令牌申请新的令牌，检查token_used变量
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token(expiration=3600), 'expiration': 3600})





















