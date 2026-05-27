"""Service layer holding business logic for soyuz-catalog.

The service modules follow a flat ``<resource>_service.py`` naming
convention with one exception worth flagging: the credentials surface
is split across two near-identically-named modules because the UC
spec defines two unrelated resources whose names collide in English:

* :mod:`soyuz_catalog.services.credential_service` — singular —
  backs the **Storage Credentials** CRUD resource at
  ``/credentials``. Named storage-credential definitions that
  external locations bind to for governance.
* :mod:`soyuz_catalog.services.credentials_service` — plural —
  backs the **Temporary Credentials** stub endpoints at
  ``/temporary-table-credentials`` /
  ``/temporary-volume-credentials`` / ``/temporary-path-credentials``
  / ``/temporary-model-version-credentials``. Ephemeral
  credential-vending requests (spec-conformant stubs in soyuz —
  cloud credential vending is explicitly out of scope).

Singular vs plural mirrors the resource the module backs; both
names are kept because each matches the wire vocabulary of its
respective UC spec section.
"""
