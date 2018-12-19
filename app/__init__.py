# coding:utf-8
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
from flask_pagedown import PageDown

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
pagedown = PageDown()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'  # 设置登录页面的端点，路由在蓝本中定义，所以要加上蓝本的名字

def create_app(config_name): # 程序的工厂函数
    app = Flask(__name__)
    app.config.from_object(config[config_name])  # config提供from_object()这个方法导入配置

    config[config_name].init_app(app)  # 初始化拓展
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)


    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    # 这里加上了prefix，注册后蓝本中定义的所有路由都会加上这个前缀
    # 所有views中定义的/login会变成/auth/login

    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

    return app

