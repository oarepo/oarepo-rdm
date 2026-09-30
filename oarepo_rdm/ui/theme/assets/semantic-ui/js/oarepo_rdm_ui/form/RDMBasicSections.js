// SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
// SPDX-License-Identifier: MIT

import { RDMCommunityAndAccess } from "./sections/RDMCommunityAndAccess";
import { RDMGeneralInformationBasic } from "./sections/RDMGeneralInformationBasic";
import { RDMFiles } from "./sections/RDMFiles";

export const RDMBasicSections = [
  RDMCommunityAndAccess,
  RDMFiles,
  RDMGeneralInformationBasic,
];
