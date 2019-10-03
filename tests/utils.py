from __future__ import absolute_import

import unittest

import sqlalchemy as sa
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker

import versionalchemy as va
from tests.models import (
    ArchiveTable,
    Base,
    MultiColumnArchiveTable,
    MultiColumnUserTable,
    UserTable,
)
from versionalchemy import utils


class VaTestHelpers(object):
    def _add_and_test_version(self, row, version):
        self.session.add(row)
        self.session.commit()
        self.assertEqual(row.version(self.session), version)

    def _result_to_dict(self, res):
        return utils.result_to_dict(res)

    def _verify_archive(
        self,
        expected,
        version,
        log_id=None,
        deleted=False,
        session=None,
        user=None
    ):
        UserTable_ = getattr(self, 'UserTable', UserTable)
        ArchiveTable_ = UserTable_.ArchiveTable
        if session is None:
            session = self.session

        and_clause = sa.and_(ArchiveTable_.va_version == version, *(
            getattr(ArchiveTable_, col_name) == expected[col_name]
            for col_name in UserTable_.va_version_columns
        ))
        res = session.execute(
            sa.select([ArchiveTable_]).
            where(and_clause)
        )
        all_ = self._result_to_dict(res)
        self.assertEqual(len(all_), 1)
        row = all_[0]
        data = row['va_data']
        self.assertEqual(row['va_deleted'], deleted)
        if user is not None:
            self.assertEqual(row['user_id'], user)
        for k in expected:
            self.assertIn(k, data)
            self.assertEqual(data[k], expected[k])
        if log_id is not None:
            self.assertEqual(log_id, row['va_id'])

    def _verify_row(self, expected_dict, version, session=None):
        UserTable_ = getattr(self, 'UserTable', UserTable)
        if session is None:
            session = self.session

        # Query user table and assert there is exactly 1 row
        and_clause = sa.and_(*(
            getattr(UserTable_, col_name) == expected_dict[col_name]
            for col_name in UserTable_.va_version_columns
        ))
        res = session.execute(
            sa.select([UserTable_]).
            where(and_clause)
        )
        all_ = self._result_to_dict(res)
        self.assertEqual(len(all_), 1)
        row_dict = all_[0]

        # Assert the columns match
        for k in expected_dict:
            self.assertEqual(row_dict[k], expected_dict[k])

    def _verify_deleted(self, key, session=None):
        if session is None:
            session = self.session

        UserTable_ = getattr(self, 'UserTable', UserTable)
        ArchiveTable_ = UserTable_.ArchiveTable
        version_col_names = UserTable_.va_version_columns
        self.assertEqual(len(key), len(version_col_names))

        and_clause = sa.and_(*[
            getattr(ArchiveTable_, col_name) == key[col_name]
            for col_name in version_col_names
        ])
        res = session.execute(
            sa.select([func.count(ArchiveTable_.va_id)])
            .where(and_clause)
        )
        self.assertEqual(res.scalar(), 0)

        and_clause = sa.and_(*[
            getattr(UserTable_, col_name) == key[col_name]
            for col_name in version_col_names
        ])
        res = session.execute(
            sa.select([func.count(UserTable_.id)])
            .where(and_clause)
        )
        self.assertEqual(res.scalar(), 0)


class SQLiteTestBase(unittest.TestCase, VaTestHelpers):
    def __init__(self, methodName='runTest'):
        # isolation_level is set so sqlite supports savepoints
        self.engine = sa.create_engine('sqlite://', connect_args={'isolation_level': None})
        self.Session = sessionmaker(bind=self.engine)
        va.init()
        super(SQLiteTestBase, self).__init__(methodName=methodName)

    def setUp(self):
        Base.metadata.create_all(self.engine)
        UserTable.register(ArchiveTable, self.engine)
        MultiColumnUserTable.register(MultiColumnArchiveTable, self.engine)
        self.p1 = dict(product_id=10, col1='foobar', col2=10, col3=1)
        self.p2 = dict(product_id=11, col1='baz', col2=11, col3=1)
        self.p3 = dict(product_id=2546, col1='test', col2=12, col3=0)
        self.session = self.Session()

    def tearDown(self):
        delete_cmd = 'drop table {}'
        self.engine.execute(delete_cmd.format(UserTable.__tablename__))
        self.engine.execute(delete_cmd.format(ArchiveTable.__tablename__))
        self.engine.execute(delete_cmd.format(MultiColumnUserTable.__tablename__))
        self.engine.execute(delete_cmd.format(MultiColumnArchiveTable.__tablename__))
        self.session.close()
