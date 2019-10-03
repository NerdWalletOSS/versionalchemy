from __future__ import absolute_import

from sqlalchemy import Column, Integer, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

from tests.models import ArchiveTable, UserTable
from tests.utils import SQLiteTestBase
from versionalchemy import VAModelMixin
from versionalchemy.exceptions import LogTableCreationError
from versionalchemy.models import VALogMixin


class TestUserTable(SQLiteTestBase):
    def test_register_user_table(self):
        Base_ = declarative_base()
        try:
            # --- Test failure cases ---
            class WrongVersionColumns(VAModelMixin, Base_):
                __tablename__ = 'wrong_version_cols'
                va_version_columns = ['id']
                pid = Column(Integer, primary_key=True)

            class WrongVersionColumnsArchive(VALogMixin, Base_):
                __tablename__ = 'wrong_version_cols_archive'
                pid = Column(Integer)
            with self.assertRaises(LogTableCreationError):
                WrongVersionColumns.register(WrongVersionColumnsArchive, self.engine)

            class NoVersionCols(VAModelMixin, Base_):
                __tablename__ = 'no_version_cols'
                pid = Column(Integer, primary_key=True)

            class NoVersionColsArchive(VALogMixin, Base_):
                __tablename__ = 'no_version_cols_archive'
                pid = Column(Integer)
            with self.assertRaises(LogTableCreationError):
                NoVersionCols.register(NoVersionColsArchive, self.engine)

            class NoConstraint(VAModelMixin, Base_):
                __tablename__ = 'no_constraint'
                va_version_columns = ['pid1', 'pid2']
                pid1 = Column(Integer, primary_key=True)
                pid2 = Column(Integer)

            class NoConstraintArchive(VALogMixin, Base_):
                __tablename__ = 'no_constraint_archive'
                pid1 = Column(Integer)
                pid2 = Column(Integer)
            with self.assertRaises(LogTableCreationError):
                NoConstraint.register(NoConstraintArchive, self.engine)

            # --- Test success cases ---
            class PKConstraint(VAModelMixin, Base_):
                __tablename__ = 'pk_constraint'
                va_version_columns = ['pid1']
                pid1 = Column(Integer, primary_key=True)
                pid2 = Column(Integer)

            class PKConstraintArchive(VALogMixin, Base_):
                __tablename__ = 'pk_constraint_archive'
                pid1 = Column(Integer)
                user_id = Column(Integer)
                __table_args__ = (
                    UniqueConstraint('pid1', 'va_version', name='pid'),
                )
            Base_.metadata.create_all(self.engine)
            PKConstraint.register(PKConstraintArchive, self.engine)
        finally:
            UserTable.register(ArchiveTable, self.engine)
            Base_.metadata.drop_all(self.engine)

    def test_insert_into_unregistered_table_fails(self):
        Base_ = declarative_base()

        class UnregisteredTable(VAModelMixin, Base_):
            __tablename__ = 'unregistered_table'
            pid = Column(Integer, primary_key=True)
            col1 = Column(Integer)
        Base_.metadata.create_all(self.engine)
        self.session.add(UnregisteredTable(pid=1, col1=5))
        with self.assertRaises(LogTableCreationError):
            self.session.commit()
