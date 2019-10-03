from __future__ import absolute_import

import os
import unittest

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from tests.models import ArchiveTable, Base, UserTable
from tests.utils import SQLiteTestBase, VaTestHelpers


class TestUpdate(SQLiteTestBase):
    def test_product_update(self):
        p = UserTable(**self.p1)
        self._add_and_test_version(p, 0)

        p.col1 = 'new'
        p.col2 = -1
        self._add_and_test_version(p, 1)

        self._verify_row(dict(self.p1, **{
            'col1': 'new',
            'col2': -1
        }), 1)
        self._verify_archive(self.p1, 0)
        self._verify_archive(dict(self.p1, **{
            'col1': 'new',
            'col2': -1,
        }), 1, log_id=p.va_id)

    def test_product_update_fails(self):
        """
        Insert a product. Construct a new ORM object with the same id as the inserted object
        and make sure the insertion fails.
        """
        # Initial product insert
        p = UserTable(**self.p1)
        self._add_and_test_version(p, 0)

        # Create a new row with the same primary key and try to insert it
        p_up = dict(
            col1='newcol',
            col2=5,
            col3=False,
            product_id=10,
        )
        p_up_row = UserTable(**p_up)
        with self.assertRaises(IntegrityError):
            self._add_and_test_version(p_up_row, 1)

    def test_update_no_changes(self):
        '''
        Add an unchanged row and make sure the version does not get bumped.
        '''
        p = UserTable(**self.p1)
        self._add_and_test_version(p, 0)
        p.col1 = self.p1['col1']
        self.session.add(p)
        self.session.commit()
        self._verify_archive(self.p1, 0)
        self.assertEqual(len(self.session.query(ArchiveTable).all()), 1)

    def test_multiple_product_updates(self):
        """
        Update a product multiple times and ensure each one gets
        correctly versioned.
        """
        p = UserTable(**self.p1)
        self._add_and_test_version(p, 0)

        p.col1 = 'new'
        p.col2 = -1
        self._add_and_test_version(p, 1)

        p.col1 = 'third change'
        p.col2 = 139
        p.col3 = False
        self._add_and_test_version(p, 2)

        self._verify_row(dict(self.p1, **{
            'col1': 'third change',
            'col2': 139,
            'col3': False,
        }), 1)
        self._verify_archive(self.p1, 0)
        self._verify_archive(dict(self.p1, **{
            'col1': 'new',
            'col2': -1,
        }), 1)
        self._verify_archive(dict(self.p1, **{
            'col1': 'third change',
            'col2': 139,
            'col3': False,
        }), 2, log_id=p.va_id)

    def test_product_update_with_user(self):
        p = UserTable(**self.p1)
        p.updated_by('test_user1')
        self._add_and_test_version(p, 0)

        p.col1 = 'new'
        p.col2 = -1
        p.updated_by('test_user2')
        self._add_and_test_version(p, 1)

        self._verify_row(dict(self.p1, **{
            'col1': 'new',
            'col2': -1
        }), 1)
        self._verify_archive(self.p1, 0, user='test_user1')
        self._verify_archive(dict(self.p1, **{
            'col1': 'new',
            'col2': -1,
        }), 1, user='test_user2', log_id=p.va_id)


class TestConcurrentUpdate(unittest.TestCase, VaTestHelpers):
    DATABASE_URL = 'sqlite:///test.db'

    def __init__(self, methodName='runTest'):
        self.engine1 = sa.create_engine(
            self.DATABASE_URL,
            isolation_level='READ UNCOMMITTED',
            echo='debug',
            logging_name='engine1'
        )
        self.engine2 = sa.create_engine(
            self.DATABASE_URL,
            isolation_level='READ UNCOMMITTED',
            echo='debug',
            logging_name='engine2'
        )
        self.Session1 = sessionmaker(bind=self.engine1)
        self.Session2 = sessionmaker(bind=self.engine2)
        Base.metadata.create_all(self.engine1)
        UserTable.register(ArchiveTable, self.engine1)
        UserTable.register(ArchiveTable, self.engine1)
        self.p1 = dict(product_id=10, col1='foobar', col2=10, col3=True)
        super(TestConcurrentUpdate, self).__init__(methodName)

    def tearDown(self):
        delete_cmd = 'delete from {}'
        self.engine1.execute(delete_cmd.format(UserTable.__tablename__))
        self.engine1.execute(delete_cmd.format(ArchiveTable.__tablename__))
        self.Session1.close_all()
        self.Session2.close_all()
        self.engine1.dispose()
        self.engine2.dispose()

    @classmethod
    def tearDownClass(cls):
        os.remove('test.db')

    def test_concurrent_product_updates(self):
        """
        Assert that if two separate sessions try to update a product row,
        one succeeds and the other fails.
        """
        p1 = UserTable(**self.p1)

        # Create two sessions
        session1 = self.Session1()
        session2 = self.Session2()

        # Add the initial row and flush it to the table
        session1.add(p1)
        session1.commit()

        # Update 1 in session1
        p1.col1 = 'changed col 1'
        session1.add(p1)

        # Update 2 in session 2
        p2 = session2.query(UserTable).all()[0]
        p2.col2 = 1245600
        session2.add(p2)

        # this flush should succeed
        session2.commit()
        session2.close()

        # this flush should fail
        session1.commit()
        session1.close()

        final = dict(self.p1, **{'col1': 'changed col 1', 'col2': 1245600})
        self._verify_row(final, 2, session=session1)

        history = [self.p1, dict(self.p1, **{'col2': 1245600}), final]
        for i, expected in enumerate(history):
            self._verify_archive(expected, i, session=session1)
