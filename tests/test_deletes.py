from __future__ import absolute_import

import sqlalchemy as sa

from tests.models import UserTable
from tests.utils import SQLiteTestBase


class TestDelete(SQLiteTestBase):
    def test_delete(self):
        p = UserTable(**self.p1)
        self._add_and_test_version(p, 0)

        self.session.delete(p)
        self.session.flush()
        self.assertEqual(len(self.session.execute(
            sa.select([UserTable]).
            where(UserTable.product_id == self.p1['product_id'])
        ).fetchall()), 0)
        self._verify_archive(self.p1, 0)
        self._verify_archive(self.p1, 1, deleted=True)

    def test_insert_after_delete(self):
        """
        Inserting a row that has already been deleted should version where it left off
        (not at 0).
        """
        p = UserTable(**self.p1)
        self._add_and_test_version(p, 0)

        self.session.delete(p)
        self.session.flush()

        p_new = dict(self.p1, **{
            'col1': 'changed',
            'col2': 139,
        })
        q = UserTable(**p_new)
        self._add_and_test_version(q, 2)

        self._verify_row(p_new, 2)
        self._verify_archive(self.p1, 0)
        self._verify_archive(self.p1, 1, deleted=True)
        self._verify_archive(p_new, 2)

    def test_delete_with_user(self):
        p = UserTable(**self.p1)
        p.updated_by('test_user')
        self._add_and_test_version(p, 0)

        self.session.delete(p)
        self.session.flush()
        self.assertEqual(len(self.session.execute(
            sa.select([UserTable]).
            where(UserTable.product_id == self.p1['product_id'])
        ).fetchall()), 0)
        self._verify_archive(self.p1, 0)
        self._verify_archive(self.p1, 1, deleted=True, user='test_user')
