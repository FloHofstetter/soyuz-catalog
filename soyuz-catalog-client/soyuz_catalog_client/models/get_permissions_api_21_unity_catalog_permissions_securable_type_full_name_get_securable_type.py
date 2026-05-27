from enum import Enum


class GetPermissionsApi21UnityCatalogPermissionsSecurableTypeFullNameGetSecurableType(
    str, Enum
):
    CATALOG = "catalog"
    CREDENTIAL = "credential"
    EXTERNAL_LOCATION = "external_location"
    FUNCTION = "function"
    METASTORE = "metastore"
    REGISTERED_MODEL = "registered_model"
    SCHEMA = "schema"
    TABLE = "table"
    VOLUME = "volume"

    def __str__(self) -> str:
        return str(self.value)
