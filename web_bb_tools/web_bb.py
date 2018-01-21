# coding: utf-8
import os
import sys
from functools import partial
from commands import show_info, checkout, pull, help


# Путь до директории с компонентами приложения
WEB_BB_PROJECT_DIR = '/Users/damirazo/projects/web_bb'

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
