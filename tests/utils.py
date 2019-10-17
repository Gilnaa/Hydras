from hydras import *
import unittest


class HydrasTestCase(unittest.TestCase):
    def setUp(self):
        self._settings_snapshot = HydraSettings.snapshot()

    def tearDown(self):
        HydraSettings.update(self._settings_snapshot)
