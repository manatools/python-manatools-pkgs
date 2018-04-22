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

@package manatools.pkgs.dnfbackend
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

import manatools.pkgs.packages as pkgs

class DnfBase(dnf.Base):
    '''
    class to encapsulate and extend the dnf.Base API
    '''
    def __init__(self, setup_sack=True, pbar=None):
        dnf.Base.__init__(self)
        # setup the dnf cache
        RELEASEVER = dnf.rpm.detect_releasever(self.conf.installroot)
        self.conf.substitutions['releasever'] = RELEASEVER
        # progress = progress_ui.Progress()

        ## Package queue
        self.packageQueue = pkgs.PackageQueue()

        # read the repository infomation
        self.read_all_repos()
        if setup_sack:
            # populate the dnf sack
            repos = self.repos.iter_enabled() #all()
            for repo in repos :
                if pbar != None:
                    repo.set_progress_bar(pbar)
                try:
                    repo.load()
                except dnf.exceptions.RepoError as e:
                    # TODO log and eventually manage it
                    print(e)

                #repo.set_progress_bar(None)
            self.fill_sack()
            self._packages = pkgs.Packages(self) # Define a Packages object

    def setup_base(self):
        self.fill_sack()
        self._packages = pkgs.Packages(self) # Define a Packages object

    @property
    def packages(self):
        ''' property to get easy acceess to packages'''
        return self._packages

    def cachedir_fit(self):
        conf = self.conf
        subst = conf.substitutions
        # this is not public API, same procedure as dnf cli
        suffix = dnf.conf.parser.substitute(dnf.const.CACHEDIR_SUFFIX, subst)
        cli_cache = dnf.conf.CliCache(conf.cachedir, suffix)
        return cli_cache.cachedir, cli_cache.system_cachedir

    def setup_cache(self):
        """Setup the dnf cache, same as dnf cli"""
        conf = self.conf
        conf.substitutions['releasever'] = dnf.rpm.detect_releasever('/')
        conf.cachedir, self._system_cachedir = self.cachedir_fit()
        print(_("cachedir: %s") % conf.cachedir)


    def search(self, fields, values, match_all=True, showdups=False):
        '''
        search in a list of package fields for a list of keys
        :param fields: package attributes to search in
        :param values: the values to match
        :param match_all: match all values (default)
        :param showdups: show duplicate packages or latest (default)
        :return: a list of package objects
        '''
        matches = set()
        for key in values:
            key_set = set()
            for attr in fields:
                pkgs = set(self.contains(attr,key).run())
                key_set |= pkgs
            if len(matches) == 0:
                matches = key_set
            else:
                if match_all:
                    matches &= key_set
                else:
                    matches |= key_set
        result = list(matches)
        if not showdups:
            result = self.sack.query().filter(pkg=result).latest()
        return result

    def contains(self, attr, needle, ignore_case=True):
        fdict = {'%s__substr' % attr : needle}
        if ignore_case:
            return self.sack.query().filter(hawkey.ICASE, **fdict)
        else:
            return self.sack.query().filter(**fdict)


    def apply_transaction(self):
        rc = self.resolve()
        print(_("Depsolve rc: "), rc)
        if rc:
            progress = progress_ui.Progress()
            to_dnl = self.get_packages_to_download()
            if len(to_dnl) :
                # Downloading Packages
                self.download_packages(to_dnl, progress)

            print(_("\nRunning Transaction"))
            print(self.do_transaction())
#            display = progress_ui.TransactionProgress()
#            s = self.do_transaction(display)
#            if isinstance(s, str):
#                print(s)
            del progress
#            del display
            self.setup_base()

        else:
            print(_("Depsolve failed"))

    def get_packages_to_download(self):
        to_dnl = []
        for tsi in self.transaction:
            print("   "+tsi.active_history_state+" - "+ str(tsi.active) )
            if tsi.installed:
                to_dnl.append(tsi.installed)
        return to_dnl

