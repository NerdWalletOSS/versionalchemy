from __future__ import absolute_import

import versionalchemy
from tests.models import UserTable
from tests.utils import SQLiteTestBase


class TestInsert(SQLiteTestBase):
    def test_insert_new_product(self):
        self.assertTrue(versionalchemy.is_initialized())
        p = UserTable(**self.p1)
        p.col4 = 11
        self._add_and_test_version(p, 0)

        expected = dict(other_name=11, **self.p1)
        self._verify_row(expected, 0)
        self._verify_archive(expected, 0, log_id=p.va_id)

    def test_insert_multiple_products(self):
        p1 = UserTable(**self.p1)
        p2 = UserTable(**self.p2)
        p3 = UserTable(**self.p3)
        self.session.add_all([p1, p2, p3])
        self.session.flush()
        self.assertEqual(p1.version(self.session), 0)
        self.assertEqual(p2.version(self.session), 0)
        self.assertEqual(p3.version(self.session), 0)

        # Assert the columns match
        expected = [self.p1, self.p2, self.p3]
        ids = [p1.va_id, p2.va_id, p3.va_id]
        for i, p in enumerate(expected):
            self._verify_row(p, 0)
            self._verify_archive(p, 0, log_id=ids[i])

    def test_insert_new_product_with_user(self):
        p = UserTable(**self.p1)
        p.updated_by('test_user')
        self._add_and_test_version(p, 0)

        self._verify_row(self.p1, 0)
        self._verify_archive(self.p1, 0, log_id=p.va_id, user='test_user')
