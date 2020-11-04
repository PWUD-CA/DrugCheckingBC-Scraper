
from unittest import TestCase

from DCBCScraper import DrugCheckingBCScraper


class TestDrugCheckingBCScraper(TestCase):
    @classmethod
    def setUpClass(cls):
        cls._dcbc = DrugCheckingBCScraper()

    def test_entry_count(self):
        if len(self._dcbc.entry_count) <= 0:
            self.fail()
        print(self._dcbc.entry_count)

    def test_get_page(self):
        self.fail()

    def test_fields(self):
        fields = self._dcbc.fields
        if len(fields) <= 2:
            self.fail()
        if 'drug' not in fields:
            self.fail()