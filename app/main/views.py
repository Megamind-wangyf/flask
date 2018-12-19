#coding:utf-8
from flask import render_template, session, redirect, url_for, current_app, abort, flash, request
from flask_login import login_required, current_user

from .. import db
from ..models import User, Permission, Post
from ..email import send_email
from . import main
from .forms import NameForm, EditProfileForm, PostForm


# @main.route('/', methods=['GET', 'POST'])  # 路由装饰器由蓝本提供
# def index():
#     form = NameForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(username=form.name.data).first()
#         if user is None:
#             user = User(username=form.name.data)
#             db.session.add(user)
#             db.session.commit()
#             session['known'] = False
#             if current_app.config['FLASKY_ADMIN']:
#                 send_email(current_app.config['FLASKY_ADMIN'], 'New User',
#                            'mail/new_user', user=user)
#         else:
#             session['known'] = True
#         session['name'] = form.name.data
#         return redirect(url_for('.index'))
#     # 在程序的路由中，url_for()默认使用视图函数的名字，比如index()视图函数的URL可以用url_for('index)获取
#     # 但是蓝本中flask会在全部断点加上一个命名空间即蓝本的名字，所以应该使用main.index
#     # .index是一种简写端点，是当前请求所在的蓝本
#     return render_template('index.html',
#                            form=form, name=session.get('name'),
#                            known=session.get('known', False))


# 这个路由用于主页显示博客列表，并且在列表上方显示一个写博客表单
@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        # current_user由flask login提供，通过线程内的代理对象实现
        # 数据库需要真正的用户对象，所以使用current_user._get_current_object()
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index'))
    # posts = Post.query.order_by(Post.timestamp.desc()).all()
    # 下面将上一行修改为分页显示所有博客
    page = request.args.get('page', 1, type=int)
    # 渲染的页数从请求的查询字符串request.args中获取，默认渲染第一页
    pagination = Post.query.order_by(Post.timestamp.desc()).\
        paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    # 这里把all()换成了sqlalchemy中的paginate()方法
    # 页数是第一个参数，也是唯一必须的参数
    # per_page显示一页显示的个数，默认是显示20个记录
    # 最后一个参数用于如果请求的页数超出了请求范围，那么404
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, Permission=Permission, pagination=pagination)


# 为每个用户定义个人资料页面路由
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    # 在数据库中搜索URL指定的用户名
    if user is None:
        abort(404)
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts, Permission=Permission)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        flash(form.name.data)
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        db.session.commit()
        flash('your profile has been updated')
        return redirect(url_for('.user', username=current_user.username))
    # 这里相当于提交之前，所有为表单的所有字段设置了初始值
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)



@main.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    return render_template('post.html', post=post)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('you have updated your blog')
        return redirect(url_for('main.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form, Permission=Permission)


# 用户在其他用户的页面点击follow，调用follow/username路由
@main.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('invalid user')
        return redirect(url_for('main.index'))
    # 这里其实不是很必要，因为如果已经关注了，页面都不会显示这个按钮
    if current_user.is_following(user):
        flash('you already follow this user')
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    flash('ok, you followed this user now')
    return redirect(url_for('main.user', username=username))


@main.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    current_user.unfollow(user)
    flash('ok, you have cancled to follow this user')
    return redirect(url_for('main.user', username=username))


@main.route('/followers/<username>')
@login_required
def followers(username):
    flash('not finished')
    return redirect(url_for('main.user', username=username))


@main.route('/following/<username>')
@login_required
def following(username):
    flash('not finished')
    return redirect(url_for('main.user', username=username))















