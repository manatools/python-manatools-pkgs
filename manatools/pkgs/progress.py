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

@package manatools.pkgs.progress
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
from dnf.callback import DownloadProgress
import hawkey

import gettext
from gettext import gettext as _

class Progress(DownloadProgress):
    '''
        cli progress bar example
    '''
    def __init__(self):
        super(Progress, self).__init__()
        self.total_files = 0
        self.total_size = 0.0
        self.download_files = 0
        self.download_size = 0.0
        self.dnl = {}
        self.last_pct = 0
        self._guess_metadata = False

    def start(self, total_files, total_size):
        print(_("Downloading :  %d files,  %d bytes") % (total_files, total_size))
        self.total_files = total_files
        self.total_size = total_size
        self.download_files = 0
        self.download_size = 0.0
        self.last_pct = 0
        self._guess_metadata = False

    def end(self,payload, status, msg):
        if not status: # payload download complete
            self.download_files += 1
            self.update()
        else: # dnl end with errors
            self.update()

    def progress(self, payload, done):
        pload = str(payload)
        if not pload in self.dnl:
            self.dnl[pload] = 0.0
            print(_("Starting to download : %s ") % str(payload))
        else:
            self.dnl[pload] = done
            pct = self.get_total()
            if pct > self.last_pct:
                self.last_pct = pct
                self.update()


    def get_total(self):
        """ Get the total downloaded percentage"""
        tot = 0.0
        for value in self.dnl.values():
            tot += value
        #pct make sense in file download, repo metadata total_size is always 1 :(
        if self.total_size >= tot:
            pct = int((tot / float(self.total_size)) * 100)
        else:
            pct = int(tot)
            self._guess_metadata = True
        return pct

    def update(self):
        """ Output the current progress"""
        if not self._guess_metadata:
            sys.stdout.write(_("Progress : %-3d %% (%d/%d)\r") % (self.last_pct,self.download_files, self.total_files))


