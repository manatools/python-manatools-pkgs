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



class PackageQueue:
    '''
    A Queue class to store selected packages/groups and the pending actions
    '''

    def __init__(self):
        self.packages = {}
        self.actions = {}
        self._download_size = 0
        self.QUEUE_PACKAGE_TYPES = {
            'i' : 'install',
            'u' : 'update',
            'r' : 'remove',
            'o' : 'obsolete',
            'ri': 'reinstall',
            'do': 'downgrade',
            'li': 'localinstall'
        }
        self._setup_packages()

    def _setup_packages(self):
        for key in self.QUEUE_PACKAGE_TYPES.keys():
            self.packages[key] = []

    def clear(self):
        del self.packages
        self.packages = {}
        self._setup_packages()
        self.actions = {}
        self._download_size = 0


    def get(self, action=None):
        if action is None:
            return self.packages
        else:
            return self.packages[action]

    def total(self):
        num = 0
        for key in self.QUEUE_PACKAGE_TYPES.keys():
            num += len(self.packages[key])
        return num

    def downloadsize(self):
      ''' returns the current total download size '''
      return self._download_size

    def add(self, pkg, action):
      """Add a package to queue"""
      pkgid = pkg_id(pkg)
      if pkgid in self.actions.keys():
        old_action = self.actions[pkgid]
        if old_action != action:
          # decrease size if old action was to install, update or reinstall a package
          if old_action == 'i' or old_action == 'ri' or old_action == 'u':
            self._download_size -= pkg.downloadsize
          self.packages[old_action].remove(pkgid)
          if (pkg.installed and action != 'i' or not pkg.installed and action != 'r'):
            self.packages[action].append(pkgid)
            self.actions[pkgid] = action
            # increase size if old action was to install, update or reinstall a package
            if action == 'i' or action == 'ri' or action == 'u':
              self._download_size += pkg.downloadsize
          else:
            del self.actions[pkgid]
      else:
        self.packages[action].append(pkgid)
        self.actions[pkgid] = action
        # increase size if old action was to install, update or reinstall a package
        if action == 'i' or action == 'ri' or action == 'u':
          self._download_size += pkg.downloadsize

    def add_to_install(self, pkg):
      '''
      add pkg with action 'i' (shortcut)
      '''
      self.add(pkg, 'i')

    def add_to_remove(self, pkg):
      '''
      add pkg with action 'r' (shortcut)
      '''
      self.add(pkg, 'r')

    def checked(self, pkg):
      '''
      returns if a package has to be checked in gui pacakge-list
      '''
      pkgid = pkg_id(pkg)
      if pkgid in self.actions.keys():
        return pkg.installed and self.actions[pkgid] != 'r' or self.actions[pkgid] != 'r'
      return pkg.installed

    def action(self, pkg):
      '''
      returns the action of the queued package or None if pacakge is not queued
      '''
      pkgid = pkg_id(pkg)
      if pkgid in self.actions.keys():
        return self.actions[pkgid]
      return None

    def remove(self, pkg):
      """Remove package from queue"""
      pkgid = pkg_id(pkg)
      if pkgid in self.actions.keys():
        action = self.actions[pkgid]
        self.packages[action].remove(pkgid)
        del self.actions[pkgid]

    def install_list(self):
      '''
      return the install package list
      '''
      return self.packages['i']

    def update_list(self):
      '''
      return the update package list
      '''
      return self.packages['u']

    def uninstall_list(self):
      '''
      return the uninstall package list
      '''
      return self.packages['r']


def get_pkg_info(pkg):
    '''
    returns package description
    '''
    if not isinstance(pkg, dnf.package.Package):
        raise ValueError

    return pkg.description

def pkg_id(pkg):
  '''
  return pkg_id as nevra from a dnf.package.Package
  '''
  if not isinstance(pkg, dnf.package.Package):
    raise ValueError

  return "%s,%s,%s,%s,%s,%s" % (pkg.name, pkg.epoch, pkg.version, pkg.release, pkg.arch, pkg.reponame)


def to_pkg_tuple(pkg_id):
  """Find the real package nevre & repoid from an package pkg_id"""
  (n, e, v, r, a, repo_id) = str(pkg_id).split(',')
  return (n, e, v, r, a, repo_id)

def pkg_id_to_fullname(pkg_id):
  '''
  return the fullname from pkg_id
  '''
  (n, e, v, r, a, repo_id) = to_pkg_tuple(pkg_id)
  if e and e != '0':
    return "%s-%s:%s-%s.%s" % (n, e, v, r, a)
  else:
    return "%s-%s-%s.%s" % (n, v, r, a)

def fullname(pkg):
    '''
    return package full name as nevra
    '''
    if not isinstance(pkg, dnf.package.Package):
      raise ValueError

    if pkg.epoch and pkg.epoch != '0':
      return "%s-%s:%s-%s.%s" % (pkg.name, pkg.epoch, pkg.version, pkg.release, pkg.arch)
    else:
      return "%s-%s-%s.%s" % (pkg.name, pkg.version, pkg.release, pkg.arch)






