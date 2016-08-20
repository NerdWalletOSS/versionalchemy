import copy
from datetime import datetime
from itertools import chain, izip

import mock
import sqlalchemy as sa
from sqlalchemy import func

from tests.models import (
    MultiColumnUserTable,
    UserTable,
    ArchiveTable,
)
from tests.utils import (
    SQLiteTestBase,
)
from versionalchemy.api import (
    delete,
    get,
)
from versionalchemy.api.data import _get_conditions_list
from versionalchemy.utils import (
    get_dialect,
)


class TestDeleteAPI(SQLiteTestBase):
    def setUp(self):
        super(TestDeleteAPI, self).setUp()

        p1 = UserTable(**self.p1)
        p3 = UserTable(**self.p3)
        self.session.add_all([p1, p3])
        self.session.flush()

        p1.col1 = 'change1'
        p2 = UserTable(**self.p2)
        self.session.add_all([p1, p2])
        self.session.flush()

        p1.col3 = False
        p1.col1 = 'change2'
        self.session.add(p1)
        self.session.flush()

        p1.col2 = 15
        p2.col2 = 12
        self.session.add_all([p1, p2])
        self.session.flush()

    def test_delete_single_row(self):
        conds = [{'product_id': 10}]
        delete(UserTable, self.session, conds=conds)
        self._verify_deleted(conds[0])

    def test_delete_multi_row(self):
        conds = [{'product_id': 11}, {'product_id': 10}]
        delete(UserTable, self.session, conds=conds)
        for c in conds:
            self._verify_deleted(c)

    def test_delete_rollback(self):
        conds = [{'product_id': 10}]
        cond_list_1 = _get_conditions_list(UserTable, conds)
        with mock.patch(
            'versionalchemy.api.data._get_conditions_list',
            side_effect=[cond_list_1, Exception()]
        ):
            try:
                delete(UserTable, self.session, conds=conds)
                self.assertTrue(False, 'Should have raised an exception')
            except Exception:
                version_col_names = UserTable.va_version_columns
                and_clause = sa.and_(*[
                    getattr(UserTable.ArchiveTable, col_name) == conds[0][col_name]
                    for col_name in version_col_names
                ])
                res = self.session.execute(
                    sa.select([func.count(UserTable.ArchiveTable.va_id)])
                    .where(and_clause)
                )
                self.assertEquals(res.scalar(), 4)

                and_clause = sa.and_(*[
                    getattr(UserTable, col_name) == conds[0][col_name]
                    for col_name in version_col_names
                ])
                res = self.session.execute(
                    sa.select([func.count(UserTable.id)])
                    .where(and_clause)
                )
                self.assertEquals(res.scalar(), 1)


class TestMultiColDeleteAPI(SQLiteTestBase):
    UserTable = MultiColumnUserTable

    def setUp(self):
        super(TestMultiColDeleteAPI, self).setUp()
        r1 = {
            'product_id_1': 11,
            'product_id_2': 'foo',
            'col1': 'foo',
            'col2': 100,
        }
        p1 = self.UserTable(**r1)
        r2 = {
            'product_id_1': 11,
            'product_id_2': 'bar',
            'col1': 'foo',
            'col2': 100,
        }
        p2 = self.UserTable(**r2)
        self.session.add_all([p1, p2])
        self.session.flush()

        p1.col1 = 'change1'
        self.session.add(p1)
        self.session.flush()

        p1.col1 = 'change2'
        self.session.add(p1)
        self.session.flush()

        p1.col2 = 15
        p2.col2 = 12
        self.session.add_all([p1, p2])
        self.session.flush()

    def test_delete_single_row(self):
        conds = [{'product_id_1': 11, 'product_id_2': 'foo'}]
        delete(self.UserTable, self.session, conds=conds)
        self._verify_deleted(conds[0])

    def test_delete_multi_row(self):
        conds = [
            {'product_id_1': 11, 'product_id_2': 'bar'},
            {'product_id_1': 11, 'product_id_2': 'foo'}
        ]
        delete(self.UserTable, self.session, conds=conds)
        for c in conds:
            self._verify_deleted(c)


class TestGetAPI(SQLiteTestBase):
    def setUp(self):
        super(TestGetAPI, self).setUp()
        self.p1_history, self.p2_history, self.p3_history = [], [], []

        self.t1 = datetime.utcfromtimestamp(10)
        p1 = UserTable(**self.p1)
        p3 = UserTable(**self.p3)
        with mock.patch('versionalchemy.models.datetime') as p:
            p.now.return_value = self.t1
            self.session.add_all([p1, p3])
            self.session.flush()
            self.p1_history.append(self._history(p1, self.t1, 0))
            self.p3_history.append(self._history(p3, self.t1, 0))

        self.t2 = datetime.utcfromtimestamp(20)
        p1.col1 = 'change1'
        p2 = UserTable(**self.p2)
        with mock.patch('versionalchemy.models.datetime') as p:
            p.now.return_value = self.t2
            self.session.add_all([p1, p2])
            self.session.flush()
            self.p1_history.append(self._history(p1, self.t2, 1))
            self.p2_history.append(self._history(p2, self.t2, 0))

        self.t3 = datetime.utcfromtimestamp(30)
        p1.col3 = False
        p1.col1 = 'change2'
        with mock.patch('versionalchemy.models.datetime') as p:
            p.now.return_value = self.t3
            self.session.add(p1)
            self.session.flush()
            self.p1_history.append(self._history(p1, self.t3, 2))

        self.t4 = datetime.utcfromtimestamp(40)
        p1.col2 = 15
        p2.col2 = 12
        with mock.patch('versionalchemy.models.datetime') as p:
            p.now.return_value = self.t4
            self.session.add_all([p1, p2])
            self.session.flush()
            self.p1_history.append(self._history(p1, self.t4, 3))
            self.p2_history.append(self._history(p2, self.t4, 1))

    def test_get_single_product_no_change(self):
        '''
        Performs a query for p3 which has no changes for current time, previous time slice,
        a time period that includes t1, and a time period that does not include t1.
        '''
        conds = [{'product_id': 2546}]
        result = get(UserTable, self.session, conds=conds)
        self._assert_result(result, self.p3_history)

        result = get(
            UserTable,
            self.session,
            t1=datetime.utcfromtimestamp(5),
            conds=conds,
        )
        self.assertEquals(len(result), 0)

        result = get(
            UserTable,
            self.session,
            t1=datetime.utcfromtimestamp(15),
            conds=conds,
        )
        self._assert_result(result, self.p3_history)

        result = get(
            UserTable,
            self.session,
            t1=self.t1,
            conds=conds,
        )
        self._assert_result(result, self.p3_history)

        result = get(
            UserTable,
            self.session,
            t1=datetime.utcfromtimestamp(5),
            t2=datetime.utcfromtimestamp(11),
            conds=conds,
        )
        self._assert_result(result, self.p3_history)

        result = get(
            UserTable,
            self.session,
            t1=datetime.utcfromtimestamp(11),
            t2=datetime.utcfromtimestamp(15),
            conds=conds,
        )
        self.assertEquals(len(result), 0)

    def test_get_single_product_with_change(self):
        '''
        Performs a query for p1 which has been changed 3 times for current time, previous time
        slices, and various time periods.
        '''
        conds = [{'product_id': 10}]
        result = get(UserTable, self.session, conds=conds)
        self._assert_result(result, self.p1_history[-1:])

        result = get(UserTable, self.session, t1=datetime.utcfromtimestamp(15), conds=conds)
        self._assert_result(result, self.p1_history[:1])

        result = get(
            UserTable,
            self.session,
            t1=datetime.utcfromtimestamp(35),
            conds=conds,
        )
        self._assert_result(result, self.p1_history[2:3])

        result = get(
            UserTable,
            self.session,
            t2=datetime.utcfromtimestamp(35),
            conds=conds,
        )
        self._assert_result(result, self.p1_history[:3])

        result = get(
            UserTable,
            self.session,
            t1=datetime.utcfromtimestamp(11),
            t2=datetime.utcfromtimestamp(45),
            conds=conds,
        )
        self._assert_result(result, self.p1_history[1:])

        result = get(
            UserTable,
            self.session,
            t1=datetime.utcfromtimestamp(11),
            t2=datetime.utcfromtimestamp(35),
            conds=conds,
        )
        self._assert_result(result, self.p1_history[1:3])

    def test_get_multiple_products(self):
        conds = [{'product_id': 10}, {'product_id': 11}]
        result = get(UserTable, self.session, conds=conds)
        self._assert_result(result, [self.p1_history[-1], self.p2_history[-1]])

        result = get(UserTable, self.session, t1=datetime.utcfromtimestamp(15), conds=conds)
        self._assert_result(result, self.p1_history[:1])

        result = get(UserTable, self.session, t1=datetime.utcfromtimestamp(25), conds=conds)
        self._assert_result(result, [self.p1_history[1], self.p2_history[0]])

        result = get(
            UserTable,
            self.session,
            t1=datetime.utcfromtimestamp(11),
            t2=datetime.utcfromtimestamp(45),
            conds=conds,
        )
        self._assert_result(result, list(chain(self.p1_history[1:], self.p2_history)))

    def test_get_all_products(self):
        result = get(UserTable, self.session)
        self._assert_result(result, [self.p1_history[-1], self.p2_history[-1], self.p3_history[-1]])

        result = get(UserTable, self.session, t1=datetime.utcfromtimestamp(31))
        self._assert_result(result, [self.p1_history[2], self.p2_history[0], self.p3_history[0]])

        result = get(UserTable, self.session, t1=datetime.utcfromtimestamp(11))
        self._assert_result(result, [self.p1_history[0], self.p3_history[0]])

        result = get(
            UserTable,
            self.session,
            t1=datetime.utcfromtimestamp(11),
            t2=datetime.utcfromtimestamp(45),
        )
        self._assert_result(result, list(chain(self.p1_history[1:], self.p2_history)))

    def test_get_products_after_va_id(self):
        result = get(
            UserTable,
            self.session,
            va_id=3,
        )
        self._assert_result(result, [
            self.p1_history[1], self.p1_history[2], self.p1_history[3], self.p2_history[1]
        ])

    def test_fields_query(self):
        '''
        Test specifying fields and make sure dedup happens correctly.
        '''
        def prune_data(d, fields):
            return {k: d[k] for k in fields}

        conds = [{'product_id': 10}]

        fields = ['col2']
        result = get(
            UserTable,
            self.session,
            t1=datetime.utcfromtimestamp(9),
            t2=datetime.utcfromtimestamp(45),
            conds=conds,
            fields=fields,
        )
        expected = [self.p1_history[0], self.p1_history[3]]
        self._assert_result(result, expected, fields=fields)

        fields = ['col1', 'col2']
        result = get(
            UserTable,
            self.session,
            t1=datetime.utcfromtimestamp(9),
            t2=datetime.utcfromtimestamp(45),
            conds=conds,
            fields=fields,
        )
        self._assert_result(result, self.p1_history, fields=fields)

        fields = ['col1']
        result = get(
            UserTable,
            self.session,
            t1=datetime.utcfromtimestamp(9),
            t2=datetime.utcfromtimestamp(45),
            fields=fields,
        )
        self._assert_result(
            result,
            list(chain(self.p1_history[:3], self.p2_history[:1], self.p3_history)),
            fields=fields,
        )

        fields = ['col1', 'col2']
        result = get(
            UserTable,
            self.session,
            t1=datetime.utcfromtimestamp(11),
            conds=conds,
            fields=fields,
        )
        self._assert_result(result, self.p1_history[:1], fields=fields)

        fields = ['col1', 'col2']
        result = get(
            UserTable,
            self.session,
            conds=conds,
            fields=fields,
        )
        self._assert_result(result, self.p1_history[-1:], fields=fields)

        fields = ['col1', 'invalid_col']
        result = get(
            UserTable,
            self.session,
            conds=conds,
            fields=fields,
        )
        self.p1_history[-1]['va_data']['invalid_col'] = None
        self._assert_result(result, self.p1_history[-1:], fields=fields)

    def test_failure_conditions(self):
        '''
        Pass invalid conds arguments and ensure the query fails.
        '''
        conds = [{'product_id': 10, 'foo': 15}]
        with self.assertRaises(ValueError):
            get(UserTable, self.session, t1=datetime.utcfromtimestamp(31), conds=conds)

        conds = [{'pid': 10}]
        with self.assertRaises(ValueError):
            get(UserTable, self.session, t1=datetime.utcfromtimestamp(31), conds=conds)

        with self.assertRaises(ValueError):
            get(UserTable, self.session, page=-10)

    def test_paging_results(self):
        self.session.execute('delete from {}'.format(UserTable.__tablename__))
        self.session.execute('delete from {}'.format(ArchiveTable.__tablename__))
        t = datetime.utcfromtimestamp(10000)
        with mock.patch('versionalchemy.models.datetime') as p:
            p.now.return_value = t
            history = []
            self.p1['col2'] = 0
            p1 = UserTable(**self.p1)
            self.session.add(p1)
            self.session.commit()
            history.append(self._history(p1, t, self.p1['col2']))
            # make 500 changes
            for i in xrange(500):
                self.p1['col2'] += 1
                self.p1['col3'] = int(i < 250)
                self.p1['col1'] = 'foobar' + '1' * ((i + 1) / 10)
                [setattr(p1, k, v) for k, v in self.p1.iteritems()]
                self.session.add(p1)
                self.session.commit()
                history.append(self._history(p1, t, self.p1['col2']))
            result = get(
                UserTable,
                self.session,
                t1=datetime.utcfromtimestamp(0),
                t2=datetime.utcfromtimestamp(10000000000),
                page=1,
                page_size=1000,
            )
            self._assert_result(result, history)
            result = get(
                UserTable,
                self.session,
                t1=datetime.utcfromtimestamp(0),
                t2=datetime.utcfromtimestamp(10000000000),
                page=1,
                page_size=100
            )
            self._assert_result(result, history[:100])
            result = get(
                UserTable,
                self.session,
                t1=datetime.utcfromtimestamp(0),
                t2=datetime.utcfromtimestamp(10000000000),
                page=3,
                page_size=100
            )
            self._assert_result(result, history[200:300])
            result = get(
                UserTable,
                self.session,
                t1=datetime.utcfromtimestamp(0),
                t2=datetime.utcfromtimestamp(10000000000),
                page=5,
                page_size=100
            )
            self._assert_result(result, history[400:500])
            result = get(
                UserTable,
                self.session,
                t1=datetime.utcfromtimestamp(0),
                t2=datetime.utcfromtimestamp(10000000000),
                fields=['col1'],
                page=1,
                page_size=80
            )
            self._assert_result(result, history[0:80:10], fields=['col1'])

    def _assert_result(self, result, expected, fields=None):
        self.assertEquals(len(result), len(expected))
        for res, exp in izip(result, expected):
            res = copy.deepcopy(res)
            exp = copy.deepcopy(exp)
            self.assertEqual(res['va_id'], exp['va_data']['va_id'])
            del res['va_id']
            if 'id' in res['va_data']:
                del res['va_data']['id']
            del res['user_id']
            del exp['va_data']['id']
            del exp['va_data']['va_id']
            if fields is not None:
                for k in exp['va_data'].keys():
                    if k not in fields:
                        del exp['va_data'][k]
            self.assertEquals(res, exp)

    def _history(self, row, ts, version):
        self.assertEqual(row.version(self.session), version)
        d = row._to_dict(get_dialect(self.session))
        self.assertNotIn('va_id', d)
        d['va_id'] = row.va_id
        return {
            'va_data': d,
            'va_updated_at': ts,
            'va_deleted': False,
            'va_version': version,
            'product_id': row.product_id
        }
