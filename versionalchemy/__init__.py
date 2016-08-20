import sqlalchemy as sa
from sqlalchemy.orm import Session

from versionalchemy import utils
from versionalchemy.exceptions import LogTableCreationError
from models import VAModelMixin

_initialized = False


def init():
    """
    :param Session: the session factory class
    """
    global _initialized

    if _initialized:
        return
    _initialized = True
    sa.event.listen(Session, 'after_flush', _after_flush_handler)


def is_initialized():
    global _initialized
    return _initialized


def _after_flush_handler(session, flush_context):
    handlers = [
        (_versioned_delete, session.deleted),
        (_versioned_insert, session.new),
        (_versioned_update, session.dirty),
    ]
    for handler, rows in handlers:
        for row in rows:
            if isinstance(row, VAModelMixin):
                if not hasattr(row, 'ArchiveTable'):
                    raise LogTableCreationError('Need to register va tables!!')
                user_id = getattr(row, '_updated_by', None)
                va_id = handler(row, session, user_id)
                if va_id:
                    Model = type(row)
                    where_clause = utils.generate_and_clause(
                        Model, row, row.va_version_columns
                    )
                    session.execute(sa.update(Model, values={'va_id': va_id}).where(where_clause))
                    row.va_id = va_id


def _versioned_delete(row, session, user_id=None):
    result = session.execute(
        sa.insert(row.ArchiveTable),
        row.ArchiveTable.build_row_dict(row, session, deleted=True, user_id=user_id)
    )
    # This should not matter since the row is being deleted anyways from the user
    # table but is here if we ever decide to implement soft deletes on the user table
    return result.inserted_primary_key[0]


def _versioned_update(row, session, user_id=None):
    if not utils.is_modified(row, ignore={'va_id'}):
        return

    # Check if composite key has been changed
    for col in row.va_version_columns:
        hist = getattr(sa.inspect(row).attrs, col).history
        if hist.has_changes():
            # delete the original row from the archive table
            session.execute(
                sa.insert(row.ArchiveTable),
                row.ArchiveTable.build_row_dict(
                    row, session, user_id=user_id, deleted=True, use_dirty=False
                )
            )

    result = session.execute(
        sa.insert(row.ArchiveTable),
        row.ArchiveTable.build_row_dict(row, session, user_id=user_id)
    )
    return result.inserted_primary_key[0]


def _versioned_insert(row, session, user_id=None):
    result = session.execute(
        sa.insert(row.ArchiveTable),
        row.ArchiveTable.build_row_dict(row, session, user_id=user_id)
    )
    return result.inserted_primary_key[0]
