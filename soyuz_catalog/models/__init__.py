"""SQLAlchemy ORM models for soyuz-catalog.

This package mirrors the Unity Catalog resource hierarchy as a set of
per-domain submodules. The top-level ``__init__`` re-exports every
public class so existing imports stay valid:

    from soyuz_catalog.models import Catalog, Schema, Table

Alembic and the test fixtures consume ``Base.metadata`` through the
same re-export. New models go into the matching submodule (or a new
one) and get added to the ``__all__`` list below.
"""

from __future__ import annotations

from soyuz_catalog.models._base import Base, _epoch_ms, _new_id, _now_ms
from soyuz_catalog.models.catalog import (
    Catalog,
    Function,
    Schema,
    Table,
    Volume,
)
from soyuz_catalog.models.column import Column, TableConstraint
from soyuz_catalog.models.credentials import Credential, ExternalLocation
from soyuz_catalog.models.federation import Connection
from soyuz_catalog.models.governance import AuditLog, Permission, Tag
from soyuz_catalog.models.lineage import (
    LineageColumnEdge,
    LineageEdge,
    LineageRun,
    LineageValueChange,
)
from soyuz_catalog.models.metastore import Metastore
from soyuz_catalog.models.ml import ModelVersion, RegisteredModel
from soyuz_catalog.models.semantic import MetricView
from soyuz_catalog.models.sharing import Recipient, Share, ShareGrant, ShareObject
from soyuz_catalog.models.staging import DeltaUnbackfilledCommit, StagingTable

__all__ = [
    "AuditLog",
    "Base",
    "Catalog",
    "Column",
    "Connection",
    "Credential",
    "DeltaUnbackfilledCommit",
    "ExternalLocation",
    "Function",
    "LineageColumnEdge",
    "LineageEdge",
    "LineageRun",
    "LineageValueChange",
    "Metastore",
    "MetricView",
    "ModelVersion",
    "Permission",
    "Recipient",
    "RegisteredModel",
    "Schema",
    "Share",
    "ShareGrant",
    "ShareObject",
    "StagingTable",
    "Table",
    "TableConstraint",
    "Tag",
    "Volume",
    "_epoch_ms",
    "_new_id",
    "_now_ms",
]
