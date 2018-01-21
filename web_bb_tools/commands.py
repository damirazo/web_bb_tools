# coding: utf-8
import os
import sys
from git import Repo, InvalidGitRepositoryError
from utils import color, Color


def repo_iter(all_packages):
    u"""
    Итератор по репозиториям.
    В случае отсутствия репозитория возвращает None
    """
    for name, path in all_packages:
        if not os.path.exists(path):
            yield name, None
            continue

        try:
            repo = Repo(path)
        except InvalidGitRepositoryError:
            yield name, None
            continue
        else:
            yield name, repo


def extract_origin(repo):
    try:
        origin = repo.remotes[0]
    except IndexError:
        origin = None

    return origin


def show_info(all_packages, *args, **kwargs):
    u"""Отображение информации о подключенных репозиториях
    """
    max_name = 0
    results = []

    for name, repo in repo_iter(all_packages):
        if len(name) > max_name:
            max_name = len(name)

        results.append((name, repo and repo.head.reference or None))

    for name, branch_name in results:
        name_row = name.ljust(30, u'\u00B7')
        if branch_name is not None:
            row = color(u'{}{}'.format(name_row, branch_name), Color.FG.green)
        else:
            row = color(
                u'{}[отсутствует]'.format(name_row), Color.FG.lightred)

        print(row)


def checkout(all_packages, *args, **kwargs):
    u"""Переключение рабочей ветки всех доступных репозиториев (кроме web_bb_app)
    """
    if len(sys.argv) < 3:
        raise RuntimeError(u'Не указана на какую ветку нужно переключиться!')

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
                    u'Ветка {} отсутствует на удаленном репозитории'
                ).format(branch_name))

            new_branch = repo.create_head(
                branch_name,
                getattr(origin.refs, branch_name),
            )

        new_branch.set_tracking_branch(
            getattr(origin.refs, branch_name)
        ).checkout()

        repo.head.reset(index=True, working_tree=True)

    show_info(all_packages)


def pull(all_packages, *args, **kwargs):
    u"""Обновление локальных репозиториев
    """
    for name, repo in repo_iter(all_packages):
        if repo is None:
            continue

        try:
            origin = repo.remotes[0]
        except IndexError:
            raise RuntimeError((
                u'Репозиторий "{}" не связан с внешним репозиторием'
            ).format(name))

        try:
            origin.pull()
        except Exception as exc:
            print(u'{}[{}] ({})'.format(
                name.ljust(34),
                color('X', Color.FG.red),
                str(exc).replace('\n', ';'),
            ))
        else:
            print(u'{}[{}]'.format(name.ljust(34), color('V', Color.FG.green)))


def help(*args, **kwargs):
    u"""Отображение справочной информации
    """
    print('WEB_BB_UTILS v0.1')
    print('Список доступных команд:')
    print('{}Отображение информации о локальных репозиториях'.format('info'.ljust(15)))  # noqa
    print('{}Переключение всех репозиториев (кроме web_bb_app) на указанную ветку'.format('co [branch]'.ljust(15)))  # noqa
    print('{}Обновление локальных репозиториев'.format('pull'.ljust(15)))
