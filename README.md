# OARepo RDM

A set of runtime patches to enable RDM service to work with different metadata models.
It replaces `search/search_drafts/scan` methods with oarepo-global-search (might be merged
here in the future) and for the methods that that take a pid delegates to a specialized
per-model services.

It also patches the pid context of the `RDMRecord/RDMDraft` so that when a resolve is called
on the record, an instance of a specialized record is returned.
