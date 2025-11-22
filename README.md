# OARepo RDM

Runtime extensions for integrating custom metadata models with [Invenio RDM](https://inveniosoftware.org/products/rdm/).

## Overview

This package provides a set of runtime patches that enable the RDM service to work seamlessly with different metadata models. It extends the standard Invenio RDM functionality by:

- Patching RDM service methods (`search`, `search_drafts`, `scan`, `read`) to search and operate across multiple models
- Delegating PID-based method calls to specialized per-model services
- Modifying the PID context of `RDMRecord`/`RDMDraft` to return specialized record instances on resolve
- Enabling registration of custom services/resources in place of default RDM ones

This package depends on OARepo patches to `invenio_rdm_records` that provide the infrastructure for registering custom service/resource implementations.

## Installation

```bash
pip install oarepo-rdm
```

### Requirements

- Python 3.13+
- Invenio 14.x
- oarepo-runtime >= 2.0.0dev5
- oarepo-model >= 0.1.0dev17

## Key Features

### 1. Multi-Model Service Integration

**Source:** [`oarepo_rdm/ext.py`](oarepo_rdm/ext.py), [`oarepo_rdm/services/`](oarepo_rdm/services/)

The package patches RDM service methods to enable unified operations across multiple metadata models:

```python
# The patched service can search across all registered models
results = rdm_service.search(identity=identity)

# PID-based operations are delegated to model-specific services
record = rdm_service.read(identity=identity, id_=record_id)
```

**Patched methods:**

- `search` - Searches across all registered models
- `search_drafts` - Searches draft records across models
- `scan` - Scans records across models
- `read` - Delegates to specialized service based on record PID

### 2. Specialized Record Resolution

**Source:** [`oarepo_rdm/records/`](oarepo_rdm/records/)

The PID context is patched so that resolving a PID returns an instance of the specialized record class rather than the generic RDM record:

```python
# Resolving a PID returns the model-specific record class
record = pid.resolve()  # Returns MyCustomRecord instance
```

This ensures that model-specific behavior and fields are available when working with resolved records.

### 3. Custom Service and Resource Registration

**Source:** [`oarepo_rdm/model/presets/rdm/`](oarepo_rdm/model/presets/rdm/)

The package provides infrastructure for registering custom services and resources for specific metadata models:

- **Records:** Custom record and draft implementations ([`records/`](oarepo_rdm/model/presets/rdm/records/))
- **Resources:** Custom resource configurations ([`resources/`](oarepo_rdm/model/presets/rdm/resources/))
- **Services:** Custom service implementations ([`services/`](oarepo_rdm/model/presets/rdm/services/))

### 4. RDM Metadata Presets

**Source:** [`oarepo_rdm/model/presets/rdm_metadata/`](oarepo_rdm/model/presets/rdm_metadata/)

Pre-configured RDM metadata elements and schemas:

- `rdm_elements.yaml` - Reusable RDM metadata field definitions
- `rdm.yaml` - Complete RDM metadata schema preset

These presets provide a starting point for creating RDM-compatible custom models.

### 5. OAI-PMH Integration

**Source:** [`oarepo_rdm/oai/`](oarepo_rdm/oai/)

Full OAI-PMH support with percolator-based set management:

```python
from oarepo_rdm.oai import OAIPMHPresets

# Configure OAI-PMH for your model
presets = OAIPMHPresets(
    serializer=datacite_serializer,
    config=oai_config
)
```

**Components:**

- Percolator-based OAI set filtering ([`percolator.py`](oarepo_rdm/oai/percolator.py))
- DataCite and Dublin Core serializers ([`serializer.py`](oarepo_rdm/oai/serializer.py))
- OpenSearch index templates for OAI ([`index_templates/`](oarepo_rdm/oai/index_templates/))
- OAI percolator mappings ([`mappings/`](oarepo_rdm/oai/mappings/))

### 6. PID System Fields

**Source:** [`oarepo_rdm/records/systemfields/pid.py`](oarepo_rdm/records/systemfields/pid.py)

Enhanced PID system fields that integrate with the multi-model architecture:

```python
from oarepo_rdm.records.systemfields import OARepoPIDField

class MyRecord(RDMRecord):
    pid = OARepoPIDField()
```

### 7. Unified Permission Policy

**Source:** Configuration via `RDM_PERMISSION_POLICY`

For performance reasons, permissions for search and scan operations are evaluated at the RDM records level, not on the specialized-service layer. This means that the permissions defined for the RDM records service apply to all requests, regardless of which specialized service is handling the request.

**Important:** All models must use the same permission policy, configured via the `RDM_PERMISSION_POLICY` configuration variable.

```python
# In your configuration
RDM_PERMISSION_POLICY = MyUnifiedPermissionPolicy
```

### 8. Response Handlers

**Source:** [`oarepo_rdm/resources/records/response_handlers.py`](oarepo_rdm/resources/records/response_handlers.py)

Custom response handlers for RDM resources that properly handle multi-model scenarios.

### 9. Internationalization Support

**Source:** [`oarepo_rdm/i18n/`](oarepo_rdm/i18n/)

Full i18n support with translations for Czech and English:

- Message catalogs for UI elements
- Webpack integration for frontend translations
- Semantic UI translation bundles

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/oarepo/oarepo-rdm.git
cd oarepo-rdm

./run.sh venv
```

### Running Tests

```bash
./run.sh test
```

The test suite includes:

- RDM CRUD operations (`test_rdm_crud.py`)
- Search functionality (`test_search.py`, `test_search_drafts.py`)
- PID resolution (`test_pid.py`)
- OAI-PMH integration (`test_oai.py`)
- Resource endpoints (`test_resources.py`)
- Service tasks (`test_service_tasks.py`)
- Secret links (`test_secret_links.py`)
- Runtime model behavior (`test_runtime_model.py`)

## Entry Points

The package registers several Invenio entry points:

```python
[project.entry-points."invenio_config.module"]
oarepo_rdm = "oarepo_rdm.initial_config"

[project.entry-points."invenio_base.apps"]
invenio_rdm_records = "invenio_rdm_records.ext:InvenioRDMRecords"
oarepo_rdm = "oarepo_rdm.ext:OARepoRDM"

[project.entry-points."invenio_base.api_apps"]
invenio_rdm_records = "invenio_rdm_records.ext:InvenioRDMRecords"
oarepo_rdm = "oarepo_rdm.ext:OARepoRDM"

[project.entry-points."invenio_base.api_blueprints"]
invenio_rdm_records = "invenio_rdm_records.views:create_records_bp"
# ... and more RDM blueprints

[project.entry-points."invenio_base.finalize_app"]
invenio_rdm_records = "invenio_rdm_records.ext:finalize_app"
oarepo_rdm = "oarepo_rdm.ext:finalize_app"

[project.entry-points."invenio_search.index_templates"]
oarepo_rdm_oai = "oarepo_rdm.oai.index_templates"

[project.entry-points."invenio_search.mappings"]
oarepo_rdm_oai = "oarepo_rdm.oai.mappings"

[project.entry-points."oarepo.cli.search.init"]
install_percollators = "oarepo_rdm.oai.percolator:init_percolators"
```

## License

Copyright (c) 2020-2025 CESNET z.s.p.o.

OARepo RDM is free software; you can redistribute it and/or modify it under the terms of the MIT License. See [LICENSE](LICENSE) file for more details.

## Links

- Documentation: <https://github.com/oarepo/oarepo-rdm>
- PyPI: <https://pypi.org/project/oarepo-rdm/>
- Issues: <https://github.com/oarepo/oarepo-rdm/issues>
- OARepo Project: <https://github.com/oarepo>

## Acknowledgments

This project builds upon [Invenio RDM](https://inveniosoftware.org/products/rdm/) and is developed as part of the OARepo ecosystem.
