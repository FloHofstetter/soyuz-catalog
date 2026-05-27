"""Storage credentials and external locations.

Two-table mini-hierarchy at the root of the metastore. Credentials are
the flat namespace of storage-IAM bindings; external locations carry a
URL + a foreign key into a credential. Both are referenced from
:class:`soyuz_catalog.models.Catalog` (catalog ``storage_root``) and
from tables/volumes implicitly via that catalog binding.
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from soyuz_catalog.models._base import Base, _new_id, _now_ms


class Credential(Base):
    """A Unity Catalog storage credential (metastore-level, flat namespace).

    Credentials live at the root of the metastore — they are *not* scoped
    to a catalog or schema — which is why the table is flat and the
    unique constraint is a plain index on ``name`` rather than the
    per-parent composite used by schemas / tables / volumes. Every
    external location binds to a credential by ``credential_id`` (see
    :class:`ExternalLocation`), so this class is effectively the root of
    a two-table mini-hierarchy.

    The only credential payload soyuz actually stores is the AWS IAM
    role triple: ``aws_iam_role_arn`` is the client-provided
    ``role_arn`` from ``AwsIamRoleRequest``; ``aws_iam_role_external_id``
    is a server-minted UUID used as the confused-deputy mitigation (AWS
    STS ``ExternalId`` for role assumption — the spec documents it as
    a response-only field). ``aws_iam_role_unity_catalog_iam_arn`` is
    declared on the spec but stays ``None`` in soyuz because the
    project has no runtime IAM identity of its own — see
    ``DIVERGENCES.md``.

    Azure and GCP credential shapes defined in forks of the UC spec are
    deliberately **not** modelled here: the upstream ``all.yaml`` we pin
    as the contract carries only ``aws_iam_role``. Adding the other two
    without a spec change would reintroduce the silent-spec-extension
    bug class this project refuses to tolerate.

    ``purpose`` is stored as a plain string even though the spec's
    ``CredentialPurpose`` enum has a single value (``STORAGE``) today —
    same "enums grow between UC minor versions, avoid a migration per
    new value" reasoning as :class:`soyuz_catalog.models.Table`
    ``table_type``.
    """

    __tablename__ = "credentials"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    purpose: Mapped[str] = mapped_column(String(32), nullable=False, default="STORAGE")
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    aws_iam_role_arn: Mapped[str | None] = mapped_column(String, nullable=True)
    aws_iam_role_external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    aws_iam_role_unity_catalog_iam_arn: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    external_locations: Mapped[list[ExternalLocation]] = relationship(
        "ExternalLocation",
        back_populates="credential",
        cascade="all, delete-orphan",
        passive_deletes=False,
    )


class ExternalLocation(Base):
    """A Unity Catalog external location (url + bound storage credential).

    External locations are the governance anchor for tables and volumes
    backed by storage outside the metastore's managed storage root. The
    shape is deliberately minimal: a ``url`` (scheme-validated against
    :func:`soyuz_catalog.storage.parse_storage_uri` on write, same
    write-path gate as every other resource that carries a storage URI)
    and a foreign key to :class:`Credential`.

    ``credential_id`` is the stored binding; ``credential_name`` is
    **not** a column — it is reconstructed at response time from the
    live credential row so a credential rename propagates for free
    without a fan-out UPDATE. This is the same rename-invariance trick
    used by schemas, tables, and volumes to reconstruct their
    ``full_name`` from live parent names.

    The foreign key to ``credentials.id`` is declared without
    ``ondelete="CASCADE"``. ``delete_credential`` cascades explicitly at
    the service layer when ``force=true`` and refuses the delete with
    409 otherwise — same "service-owns-cascade" policy as every other
    resource in this module (see :class:`soyuz_catalog.models.Schema`
    for the rationale).
    """

    __tablename__ = "external_locations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_new_id)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    credential_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("credentials.id"),
        nullable=False,
        index=True,
    )
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False, default=_now_ms)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    credential: Mapped[Credential] = relationship(
        "Credential",
        back_populates="external_locations",
    )
