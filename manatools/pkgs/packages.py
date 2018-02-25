# vim: set fileencoding=utf-8 :
# vim: set et ts=4 sw=4:
'''
ManaTools is a generic launcher application that can run
internal or external modules, such as system configuration tools.

ManaTools is also a collection of configuration tools that allows
users to configure most of their system components in a very simple,
intuitive and attractive interface. It consists of some modules
that can be also run as autonomous applications.

Python-ManaTools is a python framework to write manatools application
written in python, this project started from perl manatools experience
and its aim is to give an easy and common interface to develop and add
new modules based on libYui. Every modules can be run using QT, Gtk or
ncurses interface.

License: LGPLv2+

Author:  Angelo Naselli <anaselli@linux.it>

@package manatools.pkgs.packages
'''

from __future__ import print_function
from __future__ import absolute_import

from time import time
from os import listdir
import sys
import dnf
import dnf.yum
import dnf.const
import dnf.conf
import dnf.subject
import dnf.repodict
import dnf.repo
import dnf.package
import hawkey

import gettext
from gettext import gettext as _

class Packages:
    '''
    Get access to packages in the dnf (hawkey) sack in an easy way
    '''

    def __init__(self, base):
        self._base = base
        self._sack = base.sack
        self._inst_na = self._sack.query().installed()._na_dict()
        self._protected = None

    def _filter_packages(self, pkg_list, replace=True):
        '''
        Filter a list of package objects and replace
        the installed ones with the installed object, instead
        of the available object
        '''
        pkgs = []
        for pkg in pkg_list:
            key = (pkg.name, pkg.arch)
            inst_pkg = self._inst_na.get(key, [None])[0]
            if inst_pkg and inst_pkg.evr == pkg.evr:
                if replace:
                    pkgs.append(inst_pkg)
            else:
                pkgs.append(pkg)
        return pkgs


    @property
    def query(self):
        '''
        Get the query object from the current sack
        '''
        return self._sack.query()

    @property
    def installed(self):
        '''
        get installed packages
        '''
        return list(self.query.installed().run())

    @property
    def updates(self):
        '''
        get available updates
        '''
        return self.query.upgrades().run()

    @property
    def all(self,showdups = False):
        '''
        all packages in the repositories
        installed ones are replace with the install package objects
        '''
        if showdups:
            return self._filter_packages(self.query.available().run())
        else:
            return self._filter_packages(self.query.latest().run())

    @property
    def available(self, showdups = False):
        '''
        available packages there is not installed yet
        '''
        if showdups:
            return self._filter_packages(self.query.available().run(), replace=False)
        else:
            return self._filter_packages(self.query.latest().run(), replace=False)

    @property
    def extras(self):
        '''
        installed packages, not in current repos
        '''
        # anything installed but not in a repo is an extra
        avail_dict = self.query.available().pkgtup_dict()
        inst_dict = self.query.installed().pkgtup_dict()
        pkgs = []
        for pkgtup in inst_dict:
            if pkgtup not in avail_dict:
                pkgs.extend(inst_dict[pkgtup])
        return pkgs

    @property
    def obsoletes(self):
        '''
        packages there is obsoleting some installed packages
        '''
        inst = self.query.installed()
        return self.query.filter(obsoletes=inst)

    def _cacheProtected(self) :
        '''
        gets all the protected packages
        '''
        self._protected = {}
        protected_conf_path='/etc/dnf/protected.d'
        conf_files = listdir(protected_conf_path)
        for f in conf_files :
            file_path = protected_conf_path + '/' + f
            with open(file_path, 'r') as content_file:
                for line in content_file:
                    names=line.strip()
                    if names:
                        self._base.packages.all
                        q = self._base.packages.query
                        i = q.filter(provides=names,latest=False)
                        pkgs = i.run()
                        if len(pkgs) > 0:
                            for pkg in pkgs:
                                pkgid = pkg_id(pkg)
                                if (not pkgid in self._protected.keys()) :
                                    self._protected[pkgid] = pkg
                                    # TODO it could be necessary to get recursive require

    def isProtected(self, pkg) :
        '''
        if pkg is not none returns if the given package is a protected one
        '''
        if not self._protected :
            self._cacheProtected()
        found = pkg_id(pkg) in self._protected.keys()

        return found

    @property
    def protected(self, clean_cache=False) :
        '''
        protected (base) package list, if clean_cache is True, cache them again
        '''
        if not self._protected or clean_cache:
            self._cacheProtected()

        return self._protected.values()

    def addToProtected(self, pkg):
        '''
        add the given package to protected list
        '''
        if not self._protected :
            self._cacheProtected()
        pkgid = pkg_id(pkg)
        if (not pkgid in self._protected.keys()) :
            self._protected[pkgid] = pkg


    @property
    def recent(self, showdups=False):
        '''
        Get the recent packages
        '''
        recent = []
        now = time()
        recentlimit = now-(self._base.conf.recent*86400)
        if showdups:
            avail = self.query.available()
        else:
            avail = self.query.latest()
        for po in avail:
            if int(po.buildtime) > recentlimit:
                recent.append(po)
        return recent


def get_pkg_info(pkg):
    '''
    returns package description
    '''
    return pkg.description

def pkg_id(pkg):
    '''
    return pkg_id as nevra from a dnf.package.Package
    '''
    if not isinstance(pkg, dnf.package.Package):
        raise ValueError

    if pkg.epoch and pkg.epoch != '0':
        return "%s-%s:%s-%s.%s" % (pkg.name, pkg.epoch, pkg.version, pkg.release, pkg.arch)
    else:
        return "%s-%s-%s.%s" % (pkg.name, pkg.version, pkg.release, pkg.arch)

def fullname(pkg):
    '''
    return package full name as nevra
    '''
    return pkg_id(pkg)

