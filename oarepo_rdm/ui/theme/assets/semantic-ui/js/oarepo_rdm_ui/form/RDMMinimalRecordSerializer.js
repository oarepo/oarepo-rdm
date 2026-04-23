import { RDMDepositRecordSerializer } from "@js/invenio_rdm_records/src/deposit/api/DepositRecordSerializer";

export class RDMMinimalRecordSerializer extends RDMDepositRecordSerializer {
  get depositRecordSchema() {}
}
