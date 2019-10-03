from __future__ import absolute_import

import json
import unittest
from datetime import datetime
from decimal import Decimal

import six
import sqlalchemy as sa
from sqlalchemy.exc import StatementError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from versionalchemy import utils

EXCEPTIONS_NAME = 'builtins' if six.PY3 else 'exceptions'
TYPE_NAME = 'class' if six.PY3 else 'type'

Base = declarative_base()


class TestModel(Base):
    __tablename__ = 'test'
    id = sa.Column(sa.Integer, primary_key=True)
    json_list = sa.Column(utils.JSONEncodedList)
    json_dict = sa.Column(utils.JSONEncodedDict)


class TestClass(object):
    def __init__(self, foo):
        self.foo = foo


class TestUtils(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        self.engine = sa.create_engine('sqlite://', connect_args={'isolation_level': None})
        self.Session = sessionmaker(bind=self.engine)
        super(TestUtils, self).__init__(methodName=methodName)

    def setUp(self):
        Base.metadata.create_all(self.engine)
        self.session = self.Session()

    def tearDown(self):
        self.engine.execute('drop table test')
        self.session.close()

    def test_get_column_attribute(self):
        val = [1, 2, 3, 4]
        test_row = TestModel(json_list=val)
        dialect = self.engine.dialect
        attr = utils.get_column_attribute(test_row, 'json_list', dialect=dialect)
        self.assertEqual(attr, json.dumps(val))
        attr = utils.get_column_attribute(test_row, 'json_list')
        self.assertEqual(attr, val)

    def test_json_encoded_none_value(self):
        m = TestModel(json_list=None, json_dict=None)
        self.session.add(m)
        self.session.commit()
        result = self.session.query(TestModel).all()
        self.assertEqual(len(result), 1)
        self.assertIsNone(result[0].json_list)
        self.assertIsNone(result[0].json_dict)

    def test_json_encoded_string_value(self):
        m1 = TestModel(json_list=json.dumps([1, 2, 3]))
        m2 = TestModel(json_list=six.ensure_str(json.dumps([1, u'\u2603', 3], ensure_ascii=False)))
        self.session.add(m1)
        self.session.add(m2)
        self.session.commit()
        result = self.session.query(TestModel).all()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].json_list, [1, 2, 3])
        self.assertEqual(result[1].json_list, [1, u'\u2603', 3])

    def test_json_encoded_decimal_value(self):
        m = TestModel(json_list=[Decimal(1.0)], json_dict={'a': Decimal(2.1)})
        self.session.add(m)
        self.session.commit()
        result = self.session.query(TestModel).all()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].json_list, [1.0])
        self.assertEqual(result[0].json_dict, {'a': 2.1})

    def test_json_encoded_datetime_value(self):
        ts = datetime.now()
        m = TestModel(json_list=[ts], json_dict={'a': ts})
        self.session.add(m)
        self.session.commit()
        result = self.session.query(TestModel).all()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].json_list, [ts.isoformat()])
        self.assertEqual(result[0].json_dict, {'a': ts.isoformat()})

    def test_json_encoded_object_value(self):
        o = TestClass('bar')
        m = TestModel(json_list=[o], json_dict={'a': o})
        self.session.add(m)
        try:
            self.session.flush()
        except StatementError as e:
            self.assertTrue(type(e.orig), TypeError)
            return
        self.assertTrue(False, 'Test should have raised StatementError')

    def test_json_encoded_write_failure(self):
        m = TestModel(json_list={'a': 'b'})
        self.session.add(m)
        try:
            self.session.flush()
        except StatementError as e:
            self.assertEqual(
                e.args[0],
                "({0}.ValueError) value of type <{1} 'dict'> is not <{1} 'list'>".format(
                    EXCEPTIONS_NAME, TYPE_NAME
                )
            )
            return
        self.assertTrue(False, 'Test should have raised StatementError')

    def test_json_encode_read_failure(self):
        self.session.execute(
            sa.insert(sa.table('test', sa.column('json_list')), values={'json_list': '{"a": "b"}'})
        )
        try:
            self.session.query(TestModel).first()
        except ValueError as e:
            expected_error = "value of type <{0} 'dict'> is not <{0} 'list'>".format(TYPE_NAME)
            self.assertEqual(str(e), expected_error)
            return
        self.assertTrue(False, 'Test should have raised ValueError')

    def test_is_modified(self):
        row = TestModel(json_list=[1, 2, 3])
        row.json_list = [1]
        self.assertTrue(utils.is_modified(row))
