# -*- coding: utf-8 -*-

from ConfigParser import ConfigParser
import re


class Config(ConfigParser):
    _repo_prefix = 'repo_'
    _file = None

    def __init__(self, file):
        ConfigParser.__init__(self)

        self._file = file
        self.read(self._file)

    def setValue(self, section, option, value):
        if not self.has_section(section):
            self.add_section(section)

        self.set(section, option, value)

    def getValue(self, section, option, value=None):
        if self.has_section(section):
            if self.has_option(section, option):
                return self.get(section, option)
            else:
                return value
        else:
            return value

    def save(self):
        fh = open(self._file, 'r+')
        self.write(fh)
        fh.close()

    def getRepos(self):
        repos = []

        for section in self.sections():
            if re.match('^' + self._repo_prefix, section):
                repos.append(self.getRepoParams(section))

        return repos

    def getRepoParams(self, repo_section):
        repo = RepoParams()

        for option in self.options(repo_section):
            repo.__setattr__(option, self.getValue(repo_section, option))
            # repo.__dict__[option] = self.getValue(repo_section, option)

        return repo

    def getRepoParamsByName(self, repo_section):
        repo = RepoParams()

        for option in self.options(repo_section):
            repo.__setattr__(option, self.getValue(repo_section, option))
            # repo.__dict__[option] = self.getValue(repo_section, option)

        return repo


class RepoParams(object):
    pass
