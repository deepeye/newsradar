# 脚本配置
[alembic]
script_location = migrations

# 模板配置
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s

# 预填充迁移脚本
prepend_sys_path = .

# 版本路径
version_path_separator = os
version_locations = %(here)s/versions

# 数据库URL（会被 alembic.ini 覆盖）
sqlalchemy.url = postgresql+asyncpg://postgres:postgres@localhost:5432/clue_collector

[post_write_hooks]

# 日志配置
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
