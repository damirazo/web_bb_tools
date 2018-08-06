# coding: utf-8
import os
from git import Repo, InvalidGitRepositoryError


class Color:
    reset = '\033[0m'
    bold = '\033[01m'
    disable = '\033[02m'
    underline = '\033[04m'
    reverse = '\033[07m'
    strikethrough = '\033[09m'
    invisible = '\033[08m'

    class FG:
        black = '\033[30m'
        red = '\033[31m'
        green = '\033[32m'
        orange = '\033[33m'
        blue = '\033[34m'
        purple = '\033[35m'
        cyan = '\033[36m'
        lightgrey = '\033[37m'
        darkgrey = '\033[90m'
        lightred = '\033[91m'
        lightgreen = '\033[92m'
        yellow = '\033[93m'
        lightblue = '\033[94m'
        pink = '\033[95m'
        lightcyan = '\033[96m'

    class BG:
        black = '\033[40m'
        red = '\033[41m'
        green = '\033[42m'
        orange = '\033[43m'
        blue = '\033[44m'
        purple = '\033[45m'
        cyan = '\033[46m'
        lightgrey = '\033[47m'


def color(text, fg=None, bg=None):
    return u'{}{}{}{}'.format(
        fg or '',
        bg or '',
        text,
        Color.reset,
    )


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


class Cursor:
    _position = None

    def __init__(self):
        self._position = 0

    def __call__(self, position=None):
        if position is None:
            try:
                return self._position
            finally:
                self._position += 1
        else:
            self._position = 0


class Key:
    # Клавиша вверх
    UP = 259
    # Клавиша вниз
    DOWN = 258
    # Клавиша Q
    Q = 113
    # Клавиша пробела
    SPACE = 32
