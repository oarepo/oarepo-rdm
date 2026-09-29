// SPDX-FileCopyrightText: 2020-2025 CERN
// SPDX-License-Identifier: MIT

import React from "react";
import { buildUID } from "react-searchkit";
import Overridable from "react-overridable";
import { i18next } from "@translations/oarepo_rdm";
import { EDTFSingleDatePicker, CreatibutorsField } from "@js/oarepo_ui/forms";
import { TitlesField, ResourceTypeField } from "@js/invenio_rdm_records";
import { PIDFieldList } from "../components";

export const RDMGeneralInformationBasic = {
  key: "general-information",
  label: i18next.t("General information"),
  component: (tabConfig) => {
    const { record, formConfig } = tabConfig;
    const { vocabularies, pids, is_doi_required } = formConfig.config;
    const { overridableIdPrefix } = formConfig;
    return (
      <>
        <Overridable
          id={buildUID(overridableIdPrefix, "PIDField")}
          {...tabConfig}
        >
          <PIDFieldList
            pids={pids}
            record={record}
            isDoiRequired={is_doi_required}
          />
        </Overridable>
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
    "pids",
    "metadata.resource_type",
    "metadata.publication_date",
    "metadata.title",
    "metadata.creators",
  ],
};
