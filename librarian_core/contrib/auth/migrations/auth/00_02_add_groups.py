SQL = """
create table groups
(
    name varchar primary_key unique not null,   -- unique group name
    permissions text,                           -- comma separated list of permissions
    has_superpowers boolean not null default 0  -- is superuser?
);
"""

SQL_CREATE_GROUP = """
INSERT INTO groups (name, permissions, has_superpowers)
VALUES ('superuser', '', 1);
"""


def up(db, conf):
    db.executescript(SQL)
    # create superusers group
    db.execute(SQL_CREATE_GROUP)
