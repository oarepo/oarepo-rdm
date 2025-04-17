import pytest
from invenio_oaiserver.response import NS_DC, NS_OAIDC, NS_OAIPMH
from lxml import etree

NAMESPACES = {"x": NS_OAIPMH, "y": NS_OAIDC, "z": NS_DC}

def check_record(tree, pid_value):
    assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1
    assert len(tree.xpath("/x:OAI-PMH/x:GetRecord", namespaces=NAMESPACES)) == 1
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:GetRecord/x:record/x:header",
                    namespaces=NAMESPACES,
                )
            )
            == 1
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:GetRecord/x:record/x:header/x:identifier",
                    namespaces=NAMESPACES,
                )
            )
            == 1
    )
    identifier = tree.xpath(
        "/x:OAI-PMH/x:GetRecord/x:record/x:header/x:identifier/text()",
        namespaces=NAMESPACES,
    )
    assert identifier == [pid_value]
    datestamp = tree.xpath(
        "/x:OAI-PMH/x:GetRecord/x:record/x:header/x:datestamp/text()",
        namespaces=NAMESPACES,
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:GetRecord/x:record/x:metadata",
                    namespaces=NAMESPACES,
                )
            )
            == 1
    )

def test_identify(users, logged_client, search_clear):
    user = users[0]
    client = logged_client(user)

    identify = client.get("/oai2d?verb=Identify")
    print(identify)

def test_get_record(app, rdm_records_service, identity_simple, workflow_data, users, logged_client, search_clear):
    user = users[0]
    client = logged_client(user)

    recorda = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modela-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )
    recordb = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modelb-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )
    recordc = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modelc-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )
    rdm_records_service.publish(identity_simple, recorda["id"])
    rdm_records_service.publish(identity_simple, recordb["id"])
    rdm_records_service.publish(identity_simple, recordc["id"])

    resulta = client.get(f"/oai2d?verb=GetRecord&identifier=oai:oaioaioai:{recorda['id']}&metadataPrefix=oai_dc")
    resultb = client.get(f"/oai2d?verb=GetRecord&identifier=oai:oaioaioai:{recordb['id']}&metadataPrefix=oai_dc")
    with pytest.raises(AttributeError): # PIDsComponent does not allow to assign pids based on models as far as i know
        resultc = client.get(f"/oai2d?verb=GetRecord&identifier=oai:oaioaioai:{recordc['id']}&metadataPrefix=oai_dc")


    check_record(etree.fromstring(resulta.data), f"oai:oaioaioai:{recorda['id']}")
    check_record(etree.fromstring(resultb.data), f"oai:oaioaioai:{recordb['id']}")
    print()


def test_list_records(app, rdm_records_service, identity_simple, workflow_data, users, logged_client, search_clear):
    user = users[0]
    client = logged_client(user)

    recorda = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modela-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )
    recordb = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modelb-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )
    recordc = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modelc-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )
    rdm_records_service.publish(identity_simple, recorda["id"])
    rdm_records_service.publish(identity_simple, recordb["id"])
    rdm_records_service.publish(identity_simple, recordc["id"])

    # result = client.get("/oai2d?verb=ListRecords&metadataPrefix=oai_dc")
    # identify = client.get("/oai2d?verb=Identify")
    result = client.get("/oai2d?verb=ListRecords&metadataPrefix=oai_dc")
    print(result)





