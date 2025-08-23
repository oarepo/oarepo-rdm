from flask import g
from flask_resources import (
    resource_requestctx,
    response_handler,
    route,
)
from invenio_rdm_records.resources.resources import RDMRecordResource
from invenio_records_resources.resources.records.resource import request_search_args


class OARepoRDMRecordResource(RDMRecordResource):
    def create_url_rules(self):

        all_records_route = (
            f"{self.config.routes['all-prefix']}{self.config.url_prefix}"
        )

        rules = super().create_url_rules()
        rules += [
            # Custom route for all records
            route("GET", all_records_route, self.search_all_records),
        ]
        return rules

    @request_search_args
    @response_handler(many=True)
    def search_all_records(self):
        items = self.service.search_all_records(
            g.identity, params=resource_requestctx.args
        )
        return items.to_dict(), 200
