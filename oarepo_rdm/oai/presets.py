from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import Customization, PatchJSONFile
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class OAIMappingAliasPreset(Preset):
    """Add oaisource alias to record mapping."""

    modifies = ("record-mapping",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:

        yield PatchJSONFile(
            "record-mapping",
            {
                "aliases": {"oaisource": {}},
            },
        )


class OAIDraftMappingAliasPreset(Preset):
    """Remove oaisource alias from draft mapping.

    We need to do this as draft mapping is a copy of record mapping
    and will thus contain the oaisource from the preset above. Drafts
    should not be harvestable, so need to remove that.
    """

    modifies = ("draft-mapping",)
    only_if = ("draft-mapping",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:

        def remove_oaisource(mapping):
            mapping.get("aliases", {}).pop("oaisource", None)
            return mapping

        yield PatchJSONFile(
            "draft-mapping",
            remove_oaisource,
        )


oai_presets = [OAIMappingAliasPreset, OAIDraftMappingAliasPreset]
