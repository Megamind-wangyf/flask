# coding: utf-8
from flask import jsonify, request, g, url_for, current_app
from flask_login import login_required

from app import db
from app.api_1_0 import api
from app.api_1_0.errors import forbidden
from app.auth import auth
from app.decorators import permission_required
from app.models import Post, Permission


@api.route('/posts/')
def get_posts():
    # 对大型资源来说，获取集合的GET请求消耗很大，所以我们可以对集合进行分页
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_posts', page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_posts', page=page+1)
    return jsonify({
        'posts': [post.to_json() for post in posts],
        'prev': prev,
        'next': next,
        'count': pagination.total
    })



@api.route('/posts/<int:id>')
@login_required
def get_post(id):
    # 返回单篇博客文章
    post = Post.qyery.get_or_404(id)
    return jsonify(post.to_json())


@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE)
def new_post():
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    # 模型写入数据库以后，会返回201状态码，并把location首部的值设为刚创建的这个资源的URL
    return jsonify(post.to_json()), 201, {'Location': url_for('api.get_post', id=post.id, _external=True)}


@api.route('/posts/', methods=['PUT'])
@permission_required(Permission.WRITE)
def edit_post(id):
    # 用来更新现有资源
    post = Post.query.get_or_404(id)
    if g.current_user != post.author and \
        not g.current_user.can(Permission.WRITE):
        return forbidden('insufficient permission')
    post.body = request.json.get('body', post.body)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json())