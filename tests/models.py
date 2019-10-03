from __future__ import absolute_import

from sqlalchemy import Boolean, Column, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

from versionalchemy.models import VALogMixin, VAModelMixin

Base = declarative_base()


class UserTable(VAModelMixin, Base):
    __tablename__ = 'test_table'
    va_version_columns = ['product_id']
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, index=True, nullable=False)
    col1 = Column(String(50))
    col2 = Column(Integer)
    col3 = Column(Boolean)
    col4 = Column('other_name', Integer)

    __table_args__ = (
        UniqueConstraint('product_id', name='product_id'),
    )


class ArchiveTable(VALogMixin, Base):
    __tablename__ = 'test_table_archive'
    product_id = Column(Integer, nullable=False)
    user_id = Column(String(50))

    __table_args__ = (
        UniqueConstraint('product_id', 'va_version', name='product_id'),
    )


class MultiColumnUserTable(VAModelMixin, Base):
    __tablename__ = 'multi_col_test_table'
    va_version_columns = ['product_id_1', 'product_id_2']
    id = Column(Integer, primary_key=True)
    product_id_1 = Column(Integer, index=True, nullable=False)
    product_id_2 = Column(String(50), index=True, nullable=False)
    col1 = Column(String(50))
    col2 = Column(Integer)

    __table_args__ = (
        UniqueConstraint('product_id_1', 'product_id_2'),
    )


class MultiColumnArchiveTable(VALogMixin, Base):
    __tablename__ = 'multi_col_test_table_archive'
    product_id_1 = Column(Integer, nullable=False)
    product_id_2 = Column(String(50), index=True, nullable=False)
    user_id = Column(String(50))
    __table_args__ = (
        UniqueConstraint('product_id_1', 'product_id_2', 'va_version'),
    )
