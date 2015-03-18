import os
from urllib2 import URLError

import notify2
from twisted.application import service
from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.plugin import IPlugin
from twisted.python import usage
from twisted.python.threadpool import ThreadPool
from zope.interface.declarations import implements

from config import Config

from hgrepo import HgRepo


__author__ = 'a.egorov'


class Options(usage.Options):
    pass
    optParameters = [
        ['cfg', 'c', 'hgsnooper.ini', 'The config file.'],
    ]


class HgSnooperService(service.Service):
    name = 'hgsnooper'
    cfg = None

    _tpool = None

    def __init__(self, cfg):
        self.cfg = Config(cfg)

        self._tpool = ThreadPool()

        if not os.path.exists("cache"):
            os.makedirs("cache")

    def startService(self):
        service.Service.startService(self)

        self._tpool.start()

        for repoCfg in self.cfg.getRepos():
            try:
                hgRepo = HgRepo(repoCfg)
                task.LoopingCall(
                    self.checkRepo,
                    repo=hgRepo
                ).start(int(repoCfg.refresh))
            except URLError as e:
                self.showNotice("Error in '%s' repo" % repoCfg.name, str(e.reason))
            except Exception as e:
                self.showNotice("Error in '%s' repo" % repoCfg.name, e.message)

    def checkRepo(self, repo):
        self._tpool.callInThread(self.getRepoIncoming, repo)

    def getRepoIncoming(self, repo):
        d = Deferred()
        # d.addCallbacks(self.showIncoming, self.handleError, callbackKeywords={"repo": repo})
        d.addCallback(self.showIncoming, repo)
        d.addErrback(self.handleError, repo)
        d.callback(repo.checkIncoming())

        return d

    def showIncoming(self, sets, repo):
        if len(sets):
            self.showNotice("New incoming in repo '%s'" % repo.name, self.makeMsg(sets))

    def handleError(self, err, repo):
        self.showNotice("Error in repo '%s'" % repo.name, str(err.value))

    def showNotice(self, title, msg):
        notify2.init("HgSnooper")
        notify2.Notification(title, msg, "") \
            .show()
        # log.msg("%s: %s" % (title, msg))

    def makeMsg(self, sets):
        msg = "%d new changesets" % len(sets)

        if len(sets) == 1:
            msg = self.makeMsgForSet(sets[0])

        return msg

    def makeMsgForSet(self, chset):
        msg = "Revision: %s\n" \
              "Branch: %s\n" \
              "File(s): %d\n" \
              "Comment: %s\n" \
              "User: %s\n" \
              "Date: %s" % (
                  chset.hex_short,
                  chset.branch,
                  chset.files_count,
                  chset.desc,
                  chset.user,
                  chset.datestr
              )
        return msg

    def stopService(self):
        self._tpool.stop()
        service.Service.stopService(self)


class HgServiceMaker(object):
    implements(service.IServiceMaker, IPlugin)

    tapname = "hgsnooper"
    description = "Service for hg incoming."
    options = Options

    def makeService(self, options):
        mainService = service.MultiService()

        hgsnooper_service = HgSnooperService(options['cfg'])
        hgsnooper_service.setServiceParent(mainService)

        return mainService


service_maker = HgServiceMaker()
