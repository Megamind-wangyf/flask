#coding: utf-8
#!/usr/bin/env python
import os
from app import create_app, db
from app.models import User, Role, Post
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role, Post=Post)
manager.add_command("shell", Shell(make_context=make_shell_context))
# 集成python shell, 这个函数注册了程序，数据库实例以及模型，因此这些对象能直接导入shell
manager.add_command('db', MigrateCommand)
# 为了导出数据库迁移命令



@manager.command
def deploy():
    from flask_migrate import upgrade, init, migrate
    from app.models import Role, User
    # 把数据库迁移到最新修订版本
    init()
    migrate()
    upgrade()
    # 创建用户角色
    Role.insert_roles()
    # 让所有的用户都关注这个用户
    User.add_self_follows()


#app.run()

if __name__ == '__main__':
    manager.run()
