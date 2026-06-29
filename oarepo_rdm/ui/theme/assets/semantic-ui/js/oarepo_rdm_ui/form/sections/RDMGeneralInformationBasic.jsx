// This file is part of InvenioRDM
// Copyright (C) 2020-2025 CERN.
// Copyright (C) 2020-2022 Northwestern University.
// Copyright (C) 2021-2022 Graz University of Technology.
// Copyright (C) 2022-2024 KTH Royal Institute of Technology.
//
// Invenio App RDM is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

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
