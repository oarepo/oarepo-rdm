from invenio_i18n import lazy_gettext as _
from invenio_rdm_records.services.pids import providers

RDM_PERSISTENT_IDENTIFIER_PROVIDERS = [
    providers.OAIPIDProvider(
        "oai",
        label=_("OAI ID"),
    ),
]

RDM_PERSISTENT_IDENTIFIERS = {
    "oai": {
        "providers": ["oai"],
        "required": True,
        "label": _("OAI"),
        "is_enabled": providers.OAIPIDProvider.is_enabled,
    },
}
