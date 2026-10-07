"""ORM models.

Importing this package registers every model with ``Base.metadata``,
which is required for ``create_all`` to build the tables.
"""

from app.models.user import User
from app.models.tasks import Priority, Task