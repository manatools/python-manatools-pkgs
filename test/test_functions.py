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
 

if __name__ == '__main__':
    unittest.main()
