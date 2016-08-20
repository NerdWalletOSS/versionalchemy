import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from tests.models import (
    MultiColumnUserTable,
)
from tests.utils import SQLiteTestBase


class TestMultiColumnVersioning(SQLiteTestBase):
    UserTable = MultiColumnUserTable

    def test_insert(self):
        r = {
            'product_id_1': 11,
            'product_id_2': 'foo',
            'col1': 'foo',
            'col2': 100,
        }
        row = MultiColumnUserTable(**r)
        self._add_and_test_version(row, 0)

        self._verify_row(r, 0)
        self._verify_archive(r, 0, log_id=row.va_id)

    def test_multi_insert(self):
        r1 = {
            'product_id_1': 11,
            'product_id_2': 'foo',
            'col1': 'foo',
            'col2': 100,
        }
        row = MultiColumnUserTable(**r1)
        self._add_and_test_version(row, 0)

        r2 = {
            'product_id_1': 11,
            'product_id_2': 'bar',
            'col1': 'foo',
            'col2': 100,
        }
        row = MultiColumnUserTable(**r2)
        self._add_and_test_version(row, 0)

        r3 = {
            'product_id_1': 10,
            'product_id_2': 'bar',
            'col1': 'foo',
            'col2': 100,
        }
        row = MultiColumnUserTable(**r3)
        self._add_and_test_version(row, 0)

        self._verify_row(r1, 0)
        self._verify_archive(r1, 0)
        self._verify_row(r2, 0)
        self._verify_archive(r2, 0)
        self._verify_row(r3, 0)
        self._verify_archive(r3, 0)

    def test_unique_constraint(self):
        r1 = {
            'product_id_1': 11,
            'product_id_2': 'foo',
            'col1': 'foo',
            'col2': 100,
        }
        row = MultiColumnUserTable(**r1)
        self._add_and_test_version(row, 0)

        r2 = {
            'product_id_1': 11,
            'product_id_2': 'foo',
            'col1': 'bar',
            'col2': 100,
        }
        row = MultiColumnUserTable(**r2)
        with self.assertRaises(IntegrityError):
            self._add_and_test_version(row, 0)

    def test_update(self):
        r = {
            'product_id_1': 11,
            'product_id_2': 'foo',
            'col1': 'foo',
            'col2': 100,
        }
        row = MultiColumnUserTable(**r)
        self._add_and_test_version(row, 0)

        self._verify_row(r, 0)
        self._verify_archive(r, 0)

        row.col1 = 'bar'
        row.col2 = 300
        self._add_and_test_version(row, 1)

        self._verify_row(dict(r, col1='bar', col2=300), 1)
        self._verify_archive(dict(r, col1='bar', col2=300), 1)

    def test_multi_update(self):
        r = {
            'product_id_1': 11,
            'product_id_2': 'foo',
            'col1': 'foo',
            'col2': 100,
        }
        row = MultiColumnUserTable(**r)
        self._add_and_test_version(row, 0)

        self._verify_row(r, 0)
        self._verify_archive(r, 0)

        row.col1 = 'bar'
        row.col2 = 300
        self._add_and_test_version(row, 1)

        self._verify_row(dict(r, col1='bar', col2=300), 1)
        self._verify_archive(dict(r, col1='bar', col2=300), 1)

        row.col1 = 'hello'
        row.col2 = 404
        self._add_and_test_version(row, 2)

        self._verify_row(dict(r, col1='hello', col2=404), 2)
        self._verify_archive(dict(r, col1='hello', col2=404), 2)

    def test_update_version_column(self):
        r = {
            'product_id_1': 11,
            'product_id_2': 'foo',
            'col1': 'foo',
            'col2': 100,
        }
        row = MultiColumnUserTable(**r)
        self._add_and_test_version(row, 0)

        self._verify_row(r, 0)
        self._verify_archive(r, 0)

        row.product_id_1 = 12
        self._add_and_test_version(row, 0)
        self._verify_row(dict(r, product_id_1=12), 0)
        self._verify_archive(dict(r, product_id_1=12), 0)
        self._verify_archive(r, 1, deleted=True)

    def test_delete(self):
        r = {
            'product_id_1': 11,
            'product_id_2': 'foo',
            'col1': 'foo',
            'col2': 100,
        }
        row = MultiColumnUserTable(**r)
        self._add_and_test_version(row, 0)

        self.session.delete(row)
        self.session.flush()
        self.assertEquals(len(self.session.execute(
            sa.select([MultiColumnUserTable]).
            where(sa.and_(
                MultiColumnUserTable.product_id_1 == r['product_id_1'],
                MultiColumnUserTable.product_id_2 == r['product_id_2']
            ))
        ).fetchall()), 0)
        self._verify_archive(r, 0)
        self._verify_archive(r, 1, deleted=True)

    def test_insert_after_delete(self):
        r = {
            'product_id_1': 11,
            'product_id_2': 'foo',
            'col1': 'foo',
            'col2': 100,
        }
        row = MultiColumnUserTable(**r)
        self._add_and_test_version(row, 0)

        self.session.delete(row)
        self.session.flush()

        r_new = {
            'product_id_1': 11,
            'product_id_2': 'foo',
            'col1': 'new',
            'col2': 101,
        }
        row = MultiColumnUserTable(**r_new)
        self._add_and_test_version(row, 2)

        self._verify_row(r_new, 2)
        self._verify_archive(r, 0)
        self._verify_archive(r, 1, deleted=True)
        self._verify_archive(r_new, 2)
