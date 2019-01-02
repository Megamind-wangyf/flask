#coding: utf-8
from flask import render_template, request, url_for, redirect, flash
from flask_login import login_user, login_required, logout_user

from app import db
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User
from . import auth
from ..email import send_email
from flask_login import current_user


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        # flash('You can now login.')
        # return redirect(url_for('auth.login'))

        # 现在我们要生成令牌然后发送邮件
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirmation of your new account', 'auth/email/confirm', user=user, token=token)
        # 这里给用户发送邮件：收件人，邮件标题，邮件模板，给模板传的参数
        flash('we have sent a confirmation email to you, please confirm it!!!')
        return redirect(url_for('main.index'))

    return render_template('auth/register.html', form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()  # 创建一个对象
    # get请求时，视图函数直接渲染模板显示表单
    # POST请求时，拓展的下面这个函数会验证表单数据
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            # next = request.args.get('next')
            # if next is None or not next.startswith('/'):
            #     next = url_for('main.index')
            # return redirect(next)
            return redirect(url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)
# 这里需要注意了，这个模板文件需要保存在auth这个文件夹中
# 但是这个文件夹又需要保存在app/templates中
# flask认为模板的路径是相对au于程序模板文件夹而言的。

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('you logged out')
    return redirect(url_for('main.index'))


# 这个是发送给用户的邮件中的路由链接
@auth.route('/confirm/<token>')
@login_required  # 这个修饰器会保护这个路由，只有用户打开链接登陆后，才可以执行下面的视图函数
def confirm(token):
    if current_user.confirmed:
        # 首先检查登录的用户是否已经确认过，如果已经确认过，就不用再做什么工作了，直接重定向到首页
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        # 直接调用user模型中的验证令牌方法，直接使用flash来显示验证结果。
        flash('you have confirmed your acount!')
    else:
        flash('The confirmation link is invalid or it has expired')
    return redirect(url_for('main.index'))


# 这个部分处理请求前验证账号是否被激活
@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))

# 如果请求验证失败，就跳转到这个路由，显示一个告诉你账户需要在邮件中确认的页面
@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


# 这个部分是告诉账户未激活账户页面的链接，用于再次发送确认邮件
@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))



