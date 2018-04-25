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

@package manatools.pkgs.functions
'''
import dnf
import dnf.package

import manatools.pkgs.dnfbackend as dnfbackend

def dnfBase(setup_sack=True, pbar=None):
  '''
  returns a dnf base object
  '''
  return dnfbackend.DnfBase(setup_sack, pbar)

def selectedSize(dnf_base):
    '''
      return the transaction download size if a transaction has been run,
      or the action queue content size otherwise
    '''
    if not isinstance(dnf_base, dnfbackend.DnfBase):
        raise ValueError

    total_size = 0
    if dnf_base.transaction:
        for tsi in dnf_base.transaction:
            if tsi.installed:
                total_size += tsi.installed.downloadsize
    else:
      total_size = dnf_base.packageQueue.downloadsize()
    return total_size

def packagesProviding(dnf_base, name):
    '''
    return a list of pacakges providing "name"
    '''
    if not isinstance(dnf_base, dnfbackend.DnfBase):
        raise ValueError

    dnf_base.packages.all
    q = dnf_base.packages.query
    i = q.filter(provides=name,latest=True)

    return i.run()

def packageByName(dnf_base, name):
    '''
    search package with given "name" and compatible with current architecture,
    it takes the most up-to-date
    '''
    if not isinstance(dnf_base, dnfbackend.DnfBase):
        raise ValueError

    dnf_base.packages.all
    q = dnf_base.packages.query
    i = q.filter(name=name,latest=True)
    p = i.run()
    if len(p) > 0:
        return p[0]

    return None

def packagesToInstall(dnf_base):
    '''
    return the package list to be installed from transaction
    '''
    if not isinstance(dnf_base, dnfbackend.DnfBase):
      raise ValueError

    to_dnl = []
    if dnf_base.transaction:
      for tsi in dnf_base.transaction:
        if tsi.installed:
          to_dnl.append(tsi.installed)
    else:
      il = dnf_base.packageQueue.install_list()
      #NOTE adding also updates by now
      #TODO check if correct
      il.extend(dnf_base.packageQueue.update_list())
      q = dnf_base.sack.query()
      f = q.available()
      for pid in il:
        (n, e, v, r, a, repo_id) = pid.split(',')
        pl = f.filter(name=n, version=v, release=r, arch=a)
        if len(pl) > 0:
          to_dnl.append(pl[0])

    return to_dnl

def filter(query, options):
    '''
    return a query filterd by options (wrapping dnf.query.filter) cause of named parameters
    '''
    if not isinstance(query, dnf.query.Query):
        raise ValueError
    return query.filter(**options)

def skip_packages(dnf_base, skipped_packages):
    '''
    excludes skipped_packages (array of pcakages names)
    '''
    if not isinstance(dnf_base, dnfbackend.DnfBase):
        raise ValueError

    for pkg_name in skipped_packages:
        subj = dnf.subject.Subject(pkg_name)
        pkgs = subj.get_best_query(dnf_base.sack)
        # The only way to get expected behavior is to declare it
        # as excluded from the installable set
        dnf_base.sack.add_excludes(pkgs)

def protected(dnf_base):
    '''
    returns protected (base) package list
    '''
    if not isinstance(dnf_base, dnfbackend.DnfBase):
        raise ValueError

    return dnf_base.packages.protected

def is_protected(dnf_base, pkg):
    '''
    returns if pkg is protected (base package)
    '''
    if not isinstance(dnf_base, dnfbackend.DnfBase):
        raise ValueError
    return dnf_base.packages.isProtected(pkg)

def select_by_package_names(dnf_base, names, protected=False):
    '''
    select packages to install by providing their names and
    add them to protected if required by caller
    '''
    if not isinstance(dnf_base, dnfbackend.DnfBase):
        raise ValueError

    for name in names:
      p = packageByName(dnf_base, name)
      if p:
        dnf_base.packageQueue.add_to_install(p)
        if protected:
          dnf_base.packages.addToProtected(p)
    #TODO manage return package list (transaction)

def select_by_package_names_or_die(dnf_base, names, protected=False):
    '''
    select packages to install by providing their names and
    add them to protected if required by caller
    '''
    return select_by_package_names(dnf_base, names, protected)
    #TODO manage exception if cannot be installed

def selectPackage(dnf_base, pkg, protected=False):
    '''
    select a package to install and add it to protected if required by caller
    '''
    if not isinstance(dnf_base, dnfbackend.DnfBase):
        raise ValueError

    if not isinstance(pkg, dnf.package.Package):
        raise ValueError

    dnf_base.packageQueue.add_to_install(pkg)
    if protected:
        dnf_base.packages.addToProtected(pkg)

def unselectPackage(dnf_base, pkg):
    '''
    unselect a package from install if not protected
    '''
    if not isinstance(dnf_base, dnfbackend.DnfBase):
      raise ValueError

    if not isinstance(pkg, dnf.package.Package):
      raise ValueError

    if not is_protected(dnf_base, pkg) :
      dnf_base.packageQueue.add_to_remove(pkg)

def unselectAllPackages(dnf_base) :
    '''
    unselect all packages but protected ones
    '''
    if not isinstance(dnf_base, dnfbackend.DnfBase):
        raise ValueError

    for p in packagesToInstall(dnf_base):
        if not is_protected(dnf_base, p):
            dnf_base.packageQueue.remove(p)
