# coding: utf-8
import os
import sys
from functools import partial
from commands import show_info, checkout, pull, help, manage

# Путь до директории с компонентами приложения
WEB_BB_PROJECT_DIR = '/Users/damirazo/projects/web_bb'

# Путь до интерпретатора python из виртуального окружения
VIRTUALENV_PATH = '/Users/damirazo/.virtualenvs/web_bb/bin/python'

# Используемый в проекте модуль settings
WEB_BB_SETTINGS = 'web_bb_app.settings'

# Путь до используемого файла project.conf
WEB_BB_CONF = (
    '/Users/damirazo/projects/web_bb/web_bb_app/src/web_bb_app/project.conf')

# Пути до установленных пакетов
join = partial(os.path.join, WEB_BB_PROJECT_DIR)
AVAILABLE_PACKAGES = (
    (u'Компоненты приложения', join('web_bb_app')),
    (u'Ядро', join('web_bb_core')),
    (u'Бухгалтерия', join('web_bb_accounting')),
    (u'Зарплата и Кадры', join('web_bb_salary')),
    (u'Питание', join('web_bb_food')),
    (u'Автотранспорт', join('web_bb_vehicle')),
)

# Список доступных команд
AVAILABLE_COMMANDS = (
    ('help', help),
    ('info', show_info),
    ('co', checkout),
    ('pull', pull),
    ('m', manage),
)


if len(sys.argv) > 1:
    command = sys.argv[1]
else:
    command = 'info'


for command_name, runnable in AVAILABLE_COMMANDS:
    if command == command_name:
        try:
            runnable(AVAILABLE_PACKAGES)
        except RuntimeError as exc:
            print(str(exc))
        break
