#coding: utf-8
from flask import render_template, request, jsonify
from . import main


@main.app_errorhandler(404)  # 注册程序全局的错误处理程序
def page_not_found(e):
    # 使用HTTP内容协商处理错误
    if request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html:
        # 根据首部的值来决定客户端希望接受的响应格式
        response = jsonify({'errror': 'not found'})
        response.status_code = 404
        return response
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500