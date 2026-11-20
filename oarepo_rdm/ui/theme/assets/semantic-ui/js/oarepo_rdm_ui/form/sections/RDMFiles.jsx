// SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
// SPDX-License-Identifier: MIT

import React from "react";
import { buildUID } from "react-searchkit";
import Overridable from "react-overridable";
import { i18next } from "@translations/oarepo_rdm";
import { UppyUploader } from "@js/invenio_rdm_records";
import { Message } from "semantic-ui-react";
import { i18next as rdmI18next } from "@translations/invenio_app_rdm/i18next";
import { FileModificationUntil } from "@js/invenio_app_rdm/components/FileModificationUntil";

export const RDMFiles = {
  key: "files",
  label: i18next.t("Upload files"),
  component: (tabConfig) => {
    const { record, formConfig } = tabConfig;
    const { filesLocked, permissions, overridableIdPrefix, fileModification } =
      formConfig;
    // same conditions as upstream FileModificationUntil, so no empty notice is rendered
    const showFileModification =
      record.is_published &&
      !filesLocked &&
      !!fileModification?.fileModification?.enabled &&
      !!fileModification?.context?.days_until;
    return (
      <>
        {/* invenio-app-rdm v14 shows this in the "Files" accordion label */}
        {showFileModification && (
          <Message info size="small" data-testid="file-modification-until">
            {rdmI18next.t("Files")}
            <FileModificationUntil
              record={record}
              filesLocked={filesLocked}
              fileModification={fileModification}
            />
          </Message>
        )}
        <Overridable id={buildUID(overridableIdPrefix, "Files")} {...tabConfig}>
          <UppyUploader
            isDraftRecord={!record.is_published}
            config={formConfig}
            quota={formConfig?.config?.quota}
            decimalSizeDisplay={formConfig.decimal_size_display}
            allowEmptyFiles={formConfig.allow_empty_files}
            fileUploadConcurrency={formConfig.file_upload_concurrency}
            showMetadataOnlyToggle={permissions?.can_manage_files}
            filesLocked={filesLocked}
            fileModification={fileModification}
          />
        </Overridable>
      </>
    );
  },
  includesPaths: ["files.enabled"],
};
