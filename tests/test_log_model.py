from __future__ import absolute_import

from datetime import datetime

from sqlalchemy import Column, Integer, String
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base

from tests.models import ArchiveTable, UserTable
from tests.utils import SQLiteTestBase
from versionalchemy.exceptions import LogTableCreationError
from versionalchemy.models import VALogMixin


class TestArchiveTable(SQLiteTestBase):
    def test_register_bad_archive_table_fails(self):
        """
        Assert that an archive table with the following conditions fails to get registered:
            * no product_id column
            * the product_id column has the wrong type
        """
        Base_ = declarative_base()  # use alternate base so these tables don't get created
        try:
            # no product_id column
            class ArchiveNoFKey(VALogMixin, Base_):
                __tablename__ = 'no_fkey'
                user_id = Column(String(50))
            with self.assertRaises(LogTableCreationError):
                UserTable.register(ArchiveNoFKey, self.engine)

            # product_id is not the same type as product_id
            class ArchiveWrongFKey(VALogMixin, Base_):
                __tablename__ = 'wrong_fkey'
                product_id = Column(String(10))
                user_id = Column(String(50))
            with self.assertRaises(LogTableCreationError):
                UserTable.register(ArchiveWrongFKey, self.engine)

            # column is named something different
            class ArchiveWrongName(VALogMixin, Base_):
                __tablename__ = 'wrong_name'
                foo = Column(String(10))
                user_id = Column(String(50))
            with self.assertRaises(LogTableCreationError):
                UserTable.register(ArchiveWrongName, self.engine)

            # user did not add user_id column
            class ArchiveNoUserId(VALogMixin, Base_):
                __tablename__ = 'no_user_id'
                product_id = Column(Integer, nullable=False)
            with self.assertRaises(LogTableCreationError):
                UserTable.register(ArchiveNoUserId, self.engine)

            # no unique constraint on version column
            class ArchiveNoConstraint(VALogMixin, Base_):
                __tablename__ = 'no_constraint'
                product_id = Column(Integer)
                user_id = Column(String(50))
            with self.assertRaises(LogTableCreationError):
                UserTable.register(ArchiveNoConstraint, self.engine)
        finally:
            UserTable.register(ArchiveTable, self.engine)

    def test_archive_table_collision_fails_1(self):
        """
        Try to insert two records with the same version and foreign key in the same transaction
        and ensure the write fails. In other words, ensure the unique constraint
        is correctly imposed on the archive table.
        """
        # Insert an element so it exists in the archive table
        p = UserTable(**self.p1)
        self._add_and_test_version(p, 0)

        to_insert = {
            'va_version': 1,
            'va_deleted': False,
            'user_id': 'bar',
            'va_updated_at': datetime.now(),
            'va_data': {},
            'product_id': p.product_id,
        }
        self.session.add(ArchiveTable(**to_insert))
        to_insert = {
            'va_version': 1,
            'va_deleted': True,
            'user_id': 'foo',
            'va_updated_at': datetime.now(),
            'va_data': {},
            'product_id': p.product_id,
        }
        self.session.add(ArchiveTable(**to_insert))
        with self.assertRaises(IntegrityError):
            self.session.flush()

    def test_archive_table_collision_fails_2(self):
        """
        Try to insert two records with the same version and foreign key in different transactions
        and ensure the second write fails. In other words, ensure the unique constraint
        is correctly imposed on the archive table.
        """
        # Insert an element so it exists in the archive table
        p = UserTable(**self.p1)
        self._add_and_test_version(p, 0)

        to_insert = {
            'va_version': 0,
            'va_deleted': False,
            'user_id': 'foo',
            'va_updated_at': datetime.now(),
            'va_data': {},
            'product_id': p.product_id,
        }
        self.session.add(ArchiveTable(**to_insert))
        with self.assertRaises(IntegrityError):
            self.session.flush()
