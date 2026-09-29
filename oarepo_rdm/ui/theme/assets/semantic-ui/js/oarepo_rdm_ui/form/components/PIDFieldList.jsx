// SPDX-FileCopyrightText: 2020-2025 CERN
// SPDX-License-Identifier: MIT

import React, { Fragment } from "react";
import PropTypes from "prop-types";
import { PIDField } from "@js/invenio_rdm_records";

export const PIDFieldList = ({ pids = [], record, isDoiRequired = false }) => (
  <Fragment>
    {pids?.map((pid) => (
      <Fragment key={pid.scheme}>
        <PIDField
          btnLabelDiscardPID={pid.btn_label_discard_pid}
          btnLabelGetPID={pid.btn_label_get_pid}
          canBeManaged={pid.can_be_managed}
          canBeUnmanaged={pid.can_be_unmanaged}
          optionalDOItransitions={pid.optional_doi_transitions}
          fieldPath={`pids.${pid.scheme}`}
          fieldLabel={pid.field_label}
          isEditingPublishedRecord={record.is_published === true}
          managedHelpText={pid.managed_help_text}
          pidLabel={pid.pid_label}
          pidPlaceholder={pid.pid_placeholder}
          pidType={pid.scheme}
          unmanagedHelpText={pid.unmanaged_help_text}
          doiDefaultSelection={pid.default_selected}
          required={isDoiRequired}
          record={record}
        />
      </Fragment>
    ))}
  </Fragment>
);

PIDFieldList.propTypes = {
  pids: PropTypes.array,
  record: PropTypes.object.isRequired,
  isDoiRequired: PropTypes.bool,
};
