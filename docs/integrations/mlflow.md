# MLflow Tracking

soyuz-catalog implements the Unity Catalog **Registered Models** resource
family, which doubles as a
[Model Registry](https://mlflow.org/docs/latest/model-registry.html)
backend for [MLflow](https://mlflow.org/). MLflow's official
`unitycatalog` client targets the UC REST API; soyuz speaks that API, so
soyuz works as a drop-in MLflow registry backend.

## What gets stored

Registered Models is a two-level resource:

- A **Registered Model** lives under a schema:
  `<catalog>.<schema>.<model_name>`. It has metadata (name, comment,
  owner) but no version-specific state.
- A **Model Version** lives under a registered model with an integer
  version number. Each version has a `status` (`PENDING_REGISTRATION`,
  `READY`, `FAILED_REGISTRATION`), a `storage_location` where the
  artifacts live, and run metadata pointing back at the MLflow run that
  produced it.

soyuz stores the metadata. Artifacts (the actual model files —
`MLmodel`, `model.pkl`, conda files, etc.) live at the
`storage_location`, which defaults to
`$SOYUZ_MODEL_ARTIFACT_ROOT/<model_id>/<version>/`.

## Configuring MLflow

Point MLflow at soyuz with the standard MLflow environment variables:

```bash
export MLFLOW_TRACKING_URI=http://your-mlflow-server:5000
export MLFLOW_REGISTRY_URI=databricks-uc://soyuz
```

…where `soyuz` is a `~/.databrickscfg` profile pointing at your soyuz
instance:

```ini
[soyuz]
host = http://localhost:8000
token = unused
```

MLflow's `databricks-uc` registry implementation calls the UC REST API
under the hood. Authentication is via the bearer token — soyuz has no
auth surface, so any token works. Production deployments use the proxy
in front of soyuz for that.

## Register a model

The MLflow Python flow:

```python
import mlflow
from mlflow.tracking import MlflowClient

mlflow.set_registry_uri("databricks-uc://soyuz")
client = MlflowClient()

# 1) Create the registered model
client.create_registered_model("sales.ml.churn")

# 2) Log a model artifact tied to a tracking run
with mlflow.start_run() as run:
    mlflow.sklearn.log_model(my_model, artifact_path="model")
    model_uri = f"runs:/{run.info.run_id}/model"

# 3) Register a new version
client.create_model_version(
    name="sales.ml.churn",
    source=model_uri,
    run_id=run.info.run_id,
)
```

Under the hood, MLflow:

1. `POST /api/2.1/unity-catalog/models` — register the model.
2. `POST /api/2.1/unity-catalog/models/{name}/versions` — start a new
   version. soyuz returns the `storage_location` for the artifact upload.
3. MLflow uploads artifacts to that location.
4. `PATCH /api/2.1/unity-catalog/models/{name}/versions/{version}` —
   finalize, flipping `status` from `PENDING_REGISTRATION` to `READY`.

## Loading a model

```python
import mlflow.pyfunc

model = mlflow.pyfunc.load_model("models:/sales.ml.churn/1")
```

MLflow resolves the version through the UC API, downloads the artifacts
from the `storage_location`, and instantiates the pyfunc wrapper. soyuz
serves the metadata; artifact IO is between MLflow and the storage
backend.

## Artifact storage

By default soyuz stores artifacts under
`$SOYUZ_MODEL_ARTIFACT_ROOT/<model_id>/<version>/`, defaulting to
`model_artifacts/` next to the soyuz database. For container
deployments mount a persistent volume at that path
([Configuration](../admin/configuration.md)).

For cloud-backed artifact storage (S3, ABFSS, GCS), point
`SOYUZ_MODEL_ARTIFACT_ROOT` at the cloud URL and configure MLflow with
matching cloud credentials. soyuz does not vend credentials — see
[Concepts → Credentials](../concepts/credentials.md).

## State transitions

The model-version status flow:

```text
PENDING_REGISTRATION --> READY        (normal happy path)
PENDING_REGISTRATION --> FAILED_REGISTRATION   (upload or finalize fails)
```

`READY` is terminal. A version cannot be reopened — register a new
version instead.

## What works, what does not

soyuz implements the full Registered Models surface from the UC spec.
MLflow features that depend on it work:

- ✅ Registering models and versions.
- ✅ Tagging model versions (via UC tags — see
  [walkthroughs/tags.md](../guides/walkthroughs/tags.md)).
- ✅ Listing models and versions, with pagination.
- ✅ Aliases on model versions (`models:/sales.ml.churn/latest`).
- ✅ Downloading artifacts from soyuz-managed storage.

Features that depend on Databricks-specific MLflow extensions (model
serving endpoints, lakehouse monitoring) are out of scope — soyuz is the
catalog only.

## See also

- [Concepts → Securables and naming](../concepts/securables-and-naming.md)
  — the three-part `catalog.schema.model` name pattern.
- [Configuration](../admin/configuration.md) — `SOYUZ_MODEL_ARTIFACT_ROOT`.
- [REST API reference](../reference/api.md) — the Registered Models and
  Model Versions endpoints.
- [MLflow Model Registry docs](https://mlflow.org/docs/latest/model-registry.html)
- [Unity Catalog + MLflow integration guide](https://github.com/unitycatalog/unitycatalog/blob/main/docs/usage/models.md)
