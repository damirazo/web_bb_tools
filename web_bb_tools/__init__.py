import os
import re
import sys
import curses
import locale
import subprocess
import configparser
from web_bb_tools.config import (
    VIRTUALENV_PATH, WEB_BB_SETTINGS, WEB_BB_CONF, CONFIGURATIONS_FILES_DIR)
from web_bb_tools.constants import LJUST_NUM
from web_bb_tools.utils import (
    color, Color, repo_iter, extract_origin, Cursor, Key)


# Реестр доступных команд
COMMANDS = {}


def command(name, description=None):
    """
    Декоратор для регистрации команды
    """
    def outer(fn):
        value = (fn, description or fn.__doc__.strip())

        if isinstance(name, tuple):
            for n in name:
                COMMANDS[n] = value
        else:
            COMMANDS[name] = value

        def inner(*args, **kwargs):
            return fn(*args, **kwargs)

        return inner
    return outer


@command('info')
def command_info(all_packages, *args, **kwargs):
    """
    Отображение информации о подключенных репозиториях
    """
    max_name = 0
    results = []

    for name, repo in repo_iter(all_packages):
        if len(name) > max_name:
            max_name = len(name)

        results.append((
            name,
            repo and repo.head.reference or None,
            repo and repo.is_dirty() or None,
        ))

    for name, branch_name, is_dirty in results:
        name_row = name.ljust(LJUST_NUM, u'\u00B7')

        if branch_name is not None:
            row = color('{}{}\u00B7{}'.format(
                name_row,
                is_dirty is None and '' or (
                    is_dirty and '\033[31m[+]\033[0m\033[32m' or u'[-]'),
                str(branch_name),
            ), Color.FG.green)
        else:
            row = color('{}[отсутствует]'.format(
                name_row,
            ), Color.FG.lightred)

        print(row)


@command('co')
def command_checkout(all_packages, *args, **kwargs):
    """
    Переключение рабочей ветки всех доступных репозиториев (кроме web_bb_app)
    """
    if len(sys.argv) < 3:
        raise RuntimeError('Не указана на какую ветку нужно переключиться!')

    branch_name = sys.argv[2]
    print('Переключаемся на {}...'.format(branch_name))
    print('-----------------------------')

    for name, repo in repo_iter(all_packages[1:]):
        if repo is None:
            continue

        origin = extract_origin(repo)
        if origin is None:
            raise RuntimeError

        new_branch = list(filter(lambda x: x.name == branch_name, repo.heads))
        if new_branch:
            new_branch = new_branch[0]
        else:
            if not hasattr(origin.refs, branch_name):
                raise RuntimeError((
                    'Ветка {} отсутствует на удаленном репозитории'
                ).format(branch_name))

            new_branch = repo.create_head(
                branch_name,
                getattr(origin.refs, branch_name),
            )

        new_branch.set_tracking_branch(
            getattr(origin.refs, branch_name)
        ).checkout()

    command_info(all_packages)


@command('pull')
def command_pull(all_packages, *args, **kwargs):
    """
    Обновление локальных репозиториев
    """
    for name, repo in repo_iter(all_packages):
        if repo is None:
            continue

        try:
            origin = repo.remotes[0]
        except IndexError:
            raise RuntimeError((
                'Репозиторий "{}" не связан с внешним репозиторием'
            ).format(name))

        try:
            origin.pull()
        except Exception as exc:
            print('{}[{}] ({})'.format(
                name.ljust(LJUST_NUM, u'\u00B7'),
                color('X', Color.FG.red),
                str(exc).replace('\n', ';'),
            ))
        else:
            print('{}[{}]'.format(
                name.ljust(LJUST_NUM, u'\u00B7'),
                color('V', Color.FG.green)))


@command('m')
def command_manage(all_packages, *args, **kwargs):
    """
    Выполнение manage.py команды
    """
    if not os.path.exists(VIRTUALENV_PATH):
        raise RuntimeError('Не найден исполняемый файл python')

    wb_app_path = os.path.join(
        all_packages[0][1],
        'src', 'web_bb_app')

    manage_path = os.path.join(wb_app_path, 'manage.py')
    if not os.path.exists(manage_path):
        manage_path = os.path.join(wb_app_path, 'manage.pyc')

        if not os.path.exists(manage_path):
            raise RuntimeError('Не удалось найти файл manage.py')

    env = os.environ.copy()
    env['DJANGO_SETTINGS_MODULE'] = WEB_BB_SETTINGS
    env['WEB_BB_CONF'] = WEB_BB_CONF

    subprocess.call(
        [VIRTUALENV_PATH, manage_path, *sys.argv[2:]],
        env=env,
    )


@command('h')
def command_help(*args, **kwargs):
    """
    Отображение справочной информации
    """
    def _(s1, s2):
        print(s2.ljust(15) + s1)

    print('WEB_BB_UTILS v0.1')
    print('Список доступных команд:')

    for k, v in COMMANDS.items():
        _(v[1], k)


@command('conf')
def command_config(*args, **kwargs):
    """
    Генерация конфигурационного файла для нужного проекта
    """
    from m3_legacy import config

    def _parse_name(name):
        result = re.findall(
            '([a-f0-9]{1,3}\.[a-f0-9]{1,3}\.[a-f0-9]{1,3}\.[a-f0-9]{1,3})_(.+?)\.conf',  # noqa
            name,
        )
        if result:
            return result[0]

    configs = []
    conformity = {}
    for file_name in os.listdir(CONFIGURATIONS_FILES_DIR):
        full_path = os.path.join(CONFIGURATIONS_FILES_DIR, file_name)
        if os.path.isfile(full_path) and file_name.endswith('.conf'):
            value = _parse_name(file_name)
            configs.append(value)
            conformity[value] = full_path

    locale.setlocale(locale.LC_ALL, '')

    scr = curses.initscr()
    scr.clear()
    curses.noecho()
    curses.cbreak()
    curses.start_color()
    scr.keypad(1)

    key_code = None
    pos = 0
    exit_state = False
    selected_row = None
    cursor = Cursor()

    max_rows = 16
    page_offset = 0

    def flush_row(message, indent=0, *args):
        try:
            scr.addstr(cursor(), indent, message, *args)
        except Exception as exc:
            print(str(exc))

    configs = sorted(configs, key=lambda x: '+'.join(x))

    while key_code != ord('\n') and not exit_state:
        position_in_page = pos - page_offset

        cursor(0)
        scr.border(0)
        flush_row('Выберите сервер для генерации конфига:')
        flush_row('\n')

        for row_num, (ip, name) in enumerate(configs[page_offset:page_offset + max_rows]):  # noqa
            s = '[{}] {}'.format(
                selected_row is not None and selected_row - page_offset == row_num and '*' or ' ',  # noqa
                ip.ljust(20, '.') + name.ljust(20)
            )

            if row_num == position_in_page:
                flush_row(s, 3, curses.A_STANDOUT)
            else:
                flush_row(s, 3)

        flush_row('\n')
        flush_row('Нажмите SPACE, чтобы отметить выделенную строку')
        flush_row('Нажмите Q для выхода или Enter для создания файла')
        flush_row('\n')

        key_code = scr.getch()

        if key_code == Key.UP and pos > 0:
            if position_in_page == 0:
                page_offset -= 1
            pos -= 1
        elif key_code == Key.DOWN and pos < len(configs) - 1:
            if position_in_page == max_rows - 1:
                page_offset += 1
            pos += 1
        elif key_code == Key.Q:
            exit_state = True
        elif key_code == Key.SPACE:
            if pos == selected_row:
                selected_row = None
            else:
                selected_row = pos

        scr.refresh()

    curses.endwin()
    os.system('clear')

    server_params = configs[pos]
    server_config_path = conformity[server_params]

    parser = configparser.ConfigParser()
    parser.read(filenames=(server_config_path,))

    default_params_parser = configparser.ConfigParser()
    default_params_parser.read(filenames=(os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'defaults.conf',
    ),))

    # Доработка параметров соединения к БД
    database_settings = parser.items('database')
    for k, v in database_settings:
        if k.upper() == 'DATABASE_HOST' and v in ('127.0.0.1', 'localhost'):
            replaced_value = server_params[0]
            parser.set('database', k, replaced_value)

    # Использование существующих параметров по умолчанию
    sections = default_params_parser.sections()
    for section in sections:
        if not parser.has_section(section):
            parser.add_section(section)

        for k, v in default_params_parser.items(section):
            parser.set(section, k, v)

    with open(WEB_BB_CONF, 'w+') as f:
        parser.write(f)
