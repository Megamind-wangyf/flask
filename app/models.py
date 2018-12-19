#coding: utf-8
import hashlib
from datetime import datetime
from random import randint

from faker import Faker
from sqlalchemy.exc import IntegrityError

from app.exceptions import ValidationError
from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer
from flask import current_app, url_for


class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)

    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

    @staticmethod
    def insert_roles():
        # 这个函数并不是直接创建新的角色，而是通过角色名来查询现有的角色，再进行更新
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


class Follow(db.Model):
    __tablename__ = 'follows'

    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)  # 这个字段用于显示这个账户是否为待确认状态

    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)

    posts = db.relationship('Post', backref='author', lazy='dynamic')

    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)  # 将原始密码作为输入，输出密码散列值


    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)  # 对比数据库中密码散列值和用户输入的密码，正确返回True


    # 生成一个令牌，有效期默认一小时
    def generate_confirmation_token(self, expiration=3600):
        # 下面生成具有过期时间的JSON web签名
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})  # 为指定的数据生成一个加密签名，然后生成令牌字符串

    # 检验令牌
    def confirm(self, token):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)  # 这个方法会检验签名和过期时间，如果通过就返回原始数据
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def is_administrator(self):
        return self.can(Permission.ADMIN)

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def gravatar(self, size=100, default='identicon', rating='g'):
        url = 'https://secure.gravatar.com/avatar'
        hash = hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)



    def __repr__(self):
        return '<User %r>' % self.username

    @staticmethod
    # 这是静态方法，即此类不需要实例化就可以调用这个方法
    def generate_fake_user(count=100):
        fake = Faker()
        i = 0
        while i < count:
            u = User(email=fake.email(),
                     username=fake.user_name(),
                     password='password',
                     confirmed=True,
                     name=fake.name(),
                     location=fake.city(),
                     about_me=fake.text(),
                     member_since=fake.past_date())
            db.session.add(u)
            try:
                db.session.commit()
                i += 1
            except IntegrityError:
                db.session.rollback()


    # 从这里开始是为了实现用户关注功能的辅助方法
    def is_following(self, user):
        # 去查询是不是关注了某一个用户
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        # 去查询是不是被这个用户关注了
        return self.followers.filter_by(follower_id=user.id).first() is not None

    def follow(self, user):
        if not self.is_following(user):
            # 这里表示如果没有关注那么就关注他
            f = Follow(follower=self, followed=user)
            db.session.add(f)
            db.session.commit()

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        db.session.delete(f)
        db.session.commit()


    # 生成认证密令的令牌
    def generate_auth_token(self, expiration):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'id': self.id})


    @staticmethod
    # 这个是静态方法，因为只有解密令牌才能知道用户是谁
    def verify_auth_token(token):
        s = TimedJSONWebSignatureSerializer(current_app.app['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])


    def to_json(self):
        json_user = {
            'url': url_for('api.get_post', id=self.id, _external=True),
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts': url_for('api.get_user_posts', id=self.id, _external=True),
            'followed_posts': url_for('api.get_user_followed_posts', id=self.id, _external=True)
        }
        return json_user


    @staticmethod
    def add_self_follows():
        # 这个方法用于让所有用户都follow这个用户
        for user in User.query.all():
            if not user.is_following(user):
                user.follow(user)
                db.session.add(user)
                db.session.commit()



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Post(db.Model):
    # 建立这个模型用于储存用户的博客
    __tablename__ = 'posts'
    id = db.Column(db.INTEGER, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    @staticmethod
    def generate_fake_post(count=100):
        fake = Faker()
        user_count = User.query.count()
        for i in range(count):
            #u = User.query.offset(randint(0, user_count - 1)).first()
            u = User.query.filter(User.username == 'test').first()
            # 随机文章生成的时候，我们需要随机指定一个用户来拥有这篇文章
            # 使用offset()查询过滤器，会跳过参数中指定的记录数量，所以会获得随机的用户
            p = Post(body=fake.text(),
                     timestamp=fake.past_date(),
                     author=u)
            db.session.add(p)
        db.session.commit()


    def to_json(self):
        json_post = {
            # 这里要返回各自资源的URL，所以使用url_for生成
            'url': url_for('api.get_post', id=self.id, _external=True),
            # _external属性是为了生成完整的URL，而不是相对URL
            'body': self.body,
            'timestamp': self.timestamp,
            'author': url_for('api.get_user', id=self.id, _external=True)
        }
        return json_post

    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body=body)



















