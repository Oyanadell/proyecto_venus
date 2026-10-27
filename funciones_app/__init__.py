from django.db.backends.mysql.base import DatabaseWrapper
from django.db.backends.mysql.features import DatabaseFeatures

# Ignorar la comprobación de versión de MariaDB (< 10.11)
DatabaseWrapper.check_database_version_supported = lambda self: None

# Desactivar 'RETURNING' para compatibilidad con MariaDB 10.4
DatabaseFeatures.can_return_columns_from_insert = False