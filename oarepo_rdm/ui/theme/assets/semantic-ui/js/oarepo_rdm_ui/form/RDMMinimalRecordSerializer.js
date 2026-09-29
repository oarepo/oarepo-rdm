// SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
// SPDX-License-Identifier: MIT

import { RDMDepositRecordSerializer } from "@js/invenio_rdm_records/src/deposit/api/DepositRecordSerializer";

export class RDMMinimalRecordSerializer extends RDMDepositRecordSerializer {
  get depositRecordSchema() {}
}
