import React from "react";
import { buildUID } from "react-searchkit";
import Overridable from "react-overridable";
import i18next from "i18next";
import { EDTFSingleDatePicker, CreatibutorsField } from "@js/oarepo_ui/forms";
import { TitlesField, ResourceTypeField } from "@js/invenio_rdm_records";

export const RDMGeneralInformationBasic = {
  key: "general-information",
  label: i18next.t("General information"),
  component: (tabConfig) => {
    const { record, formConfig } = tabConfig;
    const { vocabularies } = formConfig.config;
    const { overridableIdPrefix } = formConfig;
    return (
      <>
        <Overridable
          id={buildUID(overridableIdPrefix, "Title")}
          {...tabConfig}
        >
          <TitlesField
            options={vocabularies?.titles}
            fieldPath="metadata.title"
            recordUI={record.ui}
            required
          />
        </Overridable>
        <Overridable
          id={buildUID(overridableIdPrefix, "ResourceType")}
          {...tabConfig}
        >
          <ResourceTypeField
            options={vocabularies?.resource_type}
            fieldPath="metadata.resource_type"
            required
          />
        </Overridable>
        <Overridable
          id={buildUID(overridableIdPrefix, "PublicationDate")}
          {...tabConfig}
        >
          <EDTFSingleDatePicker fieldPath="metadata.publication_date" />
        </Overridable>
        <Overridable
          id={buildUID(overridableIdPrefix, "Creators")}
          {...tabConfig}
        >
          <CreatibutorsField
            fieldPath="metadata.creators"
            schema="creators"
            autocompleteNames="search"
          />
        </Overridable>
      </>
    );
  },
  includesPaths: [
    "metadata.resource_type",
    "metadata.publication_date",
    "metadata.title",
    "metadata.creators",
  ],
};
