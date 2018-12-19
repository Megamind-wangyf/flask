# -*- coding: utf-8 -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:   #这是基类，包含了通用设置
    SECRET_KEY = '3432552'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') #这里不像单一脚本里面使用app.config['MAIL_USERNAME']=...这样的字典结构


    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
                   ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <flasky@example.com>'
    FLASKY_ADMIN = 'wangyf@cmgos.com'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FLASKY_POSTS_PER_PAGE = 20
    @staticmethod
    def init_app(app):  #这个的参数是程序实例，在这个方法中，可以执行对当前环境的配置初始化。
        pass


class DevelopmentConfig(Config): #三个子类之一
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://dbuser:qwer1234@10.0.21.62:5432/flaskapp'


class TestingConfig(Config):  #三个子类之一
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite://'


class ProductionConfig(Config):  #三个子类之一
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')


config = {        #为四种模式分别指定一个配置类
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}