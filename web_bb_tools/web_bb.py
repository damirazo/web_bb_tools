# coding: utf-8
import os
import sys
from functools import partial

# Регистрируем путь до текущего модуля в путях поиска модулей
CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, '..'))

try:
    from web_bb_tools import COMMANDS
except ImportError as exc:
    COMMANDS = {}
    print(str(exc))
    exit(1)
from web_bb_tools.config import WEB_BB_PROJECT_DIR


# Пути до установленных пакетов
join = partial(os.path.join, WEB_BB_PROJECT_DIR)
AVAILABLE_PACKAGES = (
    ('Компоненты приложения', join('web_bb_app')),
    ('Ядро', join('web_bb_core')),
    ('Бухгалтерия', join('web_bb_accounting')),
    ('Зарплата и Кадры', join('web_bb_salary')),
    ('Питание', join('web_bb_food')),
    ('Автотранспорт', join('web_bb_vehicle')),
)


if len(sys.argv) > 1:
    command = sys.argv[1]
else:
    command = 'info'


if command in COMMANDS:
    try:
        COMMANDS[command][0](AVAILABLE_PACKAGES)
    except RuntimeError as exc:
        print(str(exc))
