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


if __name__ == '__main__':
    unittest.main()
