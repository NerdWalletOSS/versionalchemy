import datetime
import itertools
import simplejson as json

import sqlalchemy as sa
from sqlalchemy import (
    TypeDecorator,
    UnicodeText,
)
from sqlalchemy.engine.reflection import Inspector


def result_to_dict(res):
    """
    :param res: :any:`sqlalchemy.engine.ResultProxy`

    :return: a list of dicts where each dict represents a row in the query where the key \
    is the column name and the value is the value of that column.
    """
    keys = res.keys()
    all_ = res.fetchall()
    return [dict(zip(keys, row)) for row in all_]


def generate_where_clause(cls, row, col, use_dirty=True):
    """
    :param cls: the sqlalchemy ORM model
    :param row: a sqlalchemy ORM model object (must be an instance of :py:data:`cls`)
    :param col: the column name
    :param use_dirty: if ``True`` (default) will return the dirty value of the column

    :return: a sqlalchemy ``==`` clause
    """
    return getattr(cls, col) == get_column_attribute(row, col, use_dirty=use_dirty)


def generate_and_clause(cls, row, cols, use_dirty=True):
    """
    :param cls: the sqlalchemy ORM model
    :param row: a sqlalchemy ORM model object (must be an instance of :py:data:`cls`)
    :param cols: an iterable of strings corresponding to column names
    :param use_dirty: if ``True`` (default) will return the dirty value of the column

    :return: a :py:func:`sqlalchemy.and_` clause which checks for equality of all columns \
    in cols to the value they contain in row.

    For example,

    .. code-block:: python

        generate_and_clause(cls, ['foo', 'bar'], cols) =
    would return

    .. code-block:: python

        sqlalchemy.and_(cls.foo == row.foo, cls.bar == row.bar)
    """

    return sa.and_(*(
        generate_where_clause(cls, row, col_name, use_dirty=use_dirty)
        for col_name in cols
    ))


def get_bind_processor(row, col_name, dialect):
    '''
    Returns a bind_processor for the given column in the row based on the dialect. If dialect
    is None or there is no bind_processor, returns the identity function. The return value
    of this can be applied to ``getattr(row, col_name)`` and will return the sql type of that value.
    '''
    bind_processor = None
    if dialect is not None:
        bind_processor = getattr(type(row), col_name).type.bind_processor(dialect)
    return (lambda x: x) if bind_processor is None else bind_processor


def get_column_attribute(row, col_name, use_dirty=True, dialect=None):
    """
    :param row: the row object
    :param col_name: the column name
    :param use_dirty: whether to return the dirty value of the column
    :param dialect: if not None, should be a :py:class:`~sqlalchemy.engine.interfaces.Dialect`. If \
        specified, this function will process the column attribute into the dialect type before \
        returning it; useful if one is using user defined column types in their mappers.

    :return: if :any:`use_dirty`, this will return the value of col_name on the row before it was \
    changed; else this will return getattr(row, col_name)
    """
    bind_processor = get_bind_processor(row, col_name, dialect)
    hist = getattr(sa.inspect(row).attrs, col_name).history
    getattr(row, col_name)
    if not use_dirty and hist.has_changes():
        if hist.deleted:
            return bind_processor(hist.deleted[0])
        else:
            return None
    return bind_processor(getattr(row, col_name))


def get_column_keys(table):
    '''
    Return a generator of names of the python attribute for the table columns.
    '''
    for k, _ in get_column_keys_and_names(table):
        yield k


def get_column_names(table):
    '''
    Return a generator of names of the name of the column in the sql table.
    '''
    for _, c in get_column_keys_and_names(table):
        yield c


def get_column_keys_and_names(table):
    '''
    Return a generator of tuples k, c such that k is the name of the python attribute for
    the column and c is the name of the column in the sql table.
    '''
    ins = sa.inspect(table)
    return ((k, c.name) for k, c in ins.mapper.c.items())


def get_dialect(session):
    return session.connection().dialect


def has_constraint(tbl_name, engine, *col_names):
    """
    :param tbl_name: a string with the name of the table to check
    :param engine: an instance of :class:`sa.engine.Engine` from which to execute the query
    :param col_names: the name of columns which the unique constraint should contain

    :rtype: bool
    :return: True if the given columns are part of a unique constraint on tbl_name
    """
    insp = Inspector.from_engine(engine)
    constraints = itertools.chain(
        (sorted(x['column_names']) for x in insp.get_unique_constraints(tbl_name)),
        sorted(insp.get_pk_constraint(tbl_name)['constrained_columns']),
    )
    return sorted(col_names) in constraints


def is_modified(row, ignore=None):
    if ignore is None:
        ignore = set()
    ins = sa.inspect(row)
    modified_cols = \
        {key for key in get_column_keys(ins.mapper) if key not in ignore} - ins.unmodified
    return not all((
        get_column_attribute(row, col) == get_column_attribute(row, col, use_dirty=False)
        for col in modified_cols
    ))


class VAJSONEncoder(json.JSONEncoder):
    """
    Extends the default encoder to add support for serializing datetime objects.
    Currently, this uses the `datetime.isoformat()` method; the resulting string
    can be reloaded into a MySQL/Postgres TIMESTAMP column directly.
    (This was verified on MySQL 5.6 and Postgres 9.6)
    """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super(VAJSONEncoder, self).default(obj)


class _JSONEncoded(TypeDecorator):
    """
    Does validation and serde on a JSON python type (list, dict, int, str) to
    a text based column in a SQL database. This class should be overriden for each
    primitive JSON type.
    """

    impl = UnicodeText
    json_type = None

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        elif isinstance(value, basestring):
            value = json.loads(value)

        if self.json_type is not None and not isinstance(value, self.json_type):
            raise ValueError('value of type {} is not {}'.format(type(value), self.json_type))

        return json.dumps(value, ensure_ascii=False, encoding='utf8', cls=VAJSONEncoder)

    def process_result_value(self, value, dialect):
        if value is None:
            return None

        value = json.loads(value)
        if self.json_type is not None and not isinstance(value, self.json_type):
            raise ValueError('value of type {} is not {}'.format(type(value), self.json_type))

        return value


class JSONEncodedList(_JSONEncoded):
    json_type = list


class JSONEncodedDict(_JSONEncoded):
    json_type = dict
