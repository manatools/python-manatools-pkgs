import unittest

from manatools.pkgs import functions
from manatools.pkgs import dnfbackend
from manatools.pkgs import packages
from manatools.pkgs import progress


class TestFunctions(unittest.TestCase):
  def setUp(self):
    pbar = progress.Progress()
    self.dnf_base = dnfbackend.DnfBase(True, pbar)

  def test_dnfbase(self):
    self.assertIsNotNone(self.dnf_base)

  def test_protected(self):
    packages = functions.protected(self.dnf_base)
    self.assertTrue( len(packages) > 0)
 
  def test_selectedSize(self):
    sz = functions.selectedSize(self.dnf_base)
    self.assertTrue(sz == 0)

  def test_getPackageByName(self):
    p_name="bless"
    p = functions.packageByName(self.dnf_base, p_name)
    self.assertIsNotNone(p)
    self.assertEqual(p.name, p_name, 'looking for "bless" package')

  def test_pkg_id(self):
    p_name="bless"
    p = functions.packageByName(self.dnf_base, p_name)
    self.assertIsNotNone(p)
    self.assertEqual(p.name, p_name, 'looking for "bless" package')
    pkgid = packages.pkg_id(p)
    fn_from_pkgid = packages.pkg_id_to_fullname(pkgid)
    fn = packages.fullname(p)
    self.assertEqual(fn, fn_from_pkgid, "pkg_id fullname")

  def test_packagesProviding(self):
    p_name="dnf"
    pl = functions.packagesProviding(self.dnf_base, p_name);
    self.assertTrue(len(pl) > 0)
    print("%s is provided by:"%(p_name))
    for p in pl:
      print(" ", packages.fullname(p))

  def test_packagesToInstall(self):
    name_list = ["btanks"]
    functions.select_by_package_names(self.dnf_base, name_list)
    pl = functions.packagesToInstall(self.dnf_base)
    self.assertTrue(len(pl) > 0)
    print(" ")
    for p in pl:
      print(" ", packages.fullname(p))

  def test_unselectAllPackages(self):
    p_name = "kernel-desktop-latest"
    kp = functions.packageByName(self.dnf_base, p_name)
    name_list = ["bless"]
    functions.select_by_package_names(self.dnf_base, name_list)
    print(" ")
    self.assertIsNotNone(kp)
    print( " selecting kernel and adding to protected %s", packages.pkg_id(kp))
    functions.selectPackage(self.dnf_base, kp, True)
    self.assertTrue(functions.is_protected(self.dnf_base, kp))
    pl = functions.packagesToInstall(self.dnf_base)
    print(" Selected:")
    self.assertTrue(len(pl) > 0)
    for p in pl:
      print(" ", packages.fullname(p))
    functions.unselectAllPackages(self.dnf_base)
    print(" After the unselect all:")
    pl = functions.packagesToInstall(self.dnf_base)
    self.assertTrue(len(pl) > 0)
    for p in pl:
      print(" ", packages.fullname(p))

if __name__ == '__main__':
    unittest.main()
