# -*- coding: utf-8 -*-

import os
from ConfigParser import ConfigParser
import pickle
from urllib2 import URLError

from mercurial import hg, ui, bundlerepo, util
from mercurial.context import changectx
from mercurial.error import RepoError
from twisted.python.failure import Failure


''' FOR DEBUG'''


class HgRepo():
    ui = None
    repo = None
    remote = None
    cfg = None
    name = None

    _cache = []

    _cache_file = None

    def __init__(self, repo_cfg):
        self.cfg = repo_cfg
        self.name = repo_cfg.name

        self.ui = ui.ui()
        self.ui.setconfig('ui', 'debug', False)
        self.ui.setconfig('ui', 'verbose', False)
        self.ui.setconfig('ui', 'quiet', True)

        self.repo = hg.repository(self.ui, self.cfg.path)

        cfg = ConfigParser()
        cfg.read(os.path.join(os.path.join(self.cfg.path, '.hg'), 'hgrc'))

        self.remote = hg.peer(self.repo, {}, cfg.get('paths', 'default'))

        self._cache_file = "cache/%s.cache" % self.name

        if not os.path.exists(self._cache_file):
            f = open(self._cache_file, "w")
            pickle.dump([], f)
            f.close()

        self._cache = self.getCache()

    def checkIncoming(self):
        try:
            self.repo = hg.repository(self.ui, self.cfg.path)

            cfg = ConfigParser()
            cfg.read(os.path.join(os.path.join(self.cfg.path, '.hg'), 'hgrc'))

            self.remote = hg.peer(self.repo, {}, cfg.get('paths', 'default'))

            other, chlist, cleanupfn = bundlerepo.getremotechanges(self.ui, self.repo, self.remote)
        except URLError as e:
            return Failure(Exception(str(e.reason)))
        except Exception as e:
            return Failure(Exception(e.message))

        if len(chlist) == 0:
            self._resetCache()

        changesets = list(set(chlist) - set(self._cache))

        self._cache = list(set(changesets) | set(self._cache))

        self.saveCache()

        res = []

        for cs in changesets:
            res.append(HgChangeSet(other, cs))

        return res

    def _resetCache(self):
        self._cache = []
        self.saveCache()

    def getCache(self):
        return pickle.load(open(self._cache_file, "r"))

    def saveCache(self):
        pickle.dump(self._cache, open(self._cache_file, "w"))


class HgChangeSet(object):
    node = None
    rev = None
    hex = None
    hex_short = None
    user = None
    date = None
    datestr = None
    files = []
    files_count = None
    desc = None
    branch = None
    tags = []
    parents = []
    children = None

    def __init__(self, other, change_set):
        ctx = changectx(other, change_set)

        self.node = ctx.node()
        self.rev = ctx.rev()
        self.hex = ctx.hex()
        self.hex_short = self.hex[:12]
        self.user = ctx.user()
        self.date = ctx.date()
        self.datestr = util.datestr(ctx.date())
        self.files = ctx.files()
        self.files_count = len(ctx.files())
        self.desc = ctx.description()
        self.branch = ctx.branch()
        self.tags = ctx.tags()
        self.parents = ctx.parents()
        self.children = ctx.children()
