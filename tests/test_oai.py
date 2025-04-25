import copy
import time

import pytest
from invenio_oaiserver.errors import OAINoRecordsMatchError
from invenio_oaiserver.percolator import _build_percolator_index_name
from invenio_oaiserver.query import get_records
from invenio_oaiserver.receivers import after_insert_oai_set, after_update_oai_set
from invenio_oaiserver.response import NS_DC, NS_OAIDC, NS_OAIPMH
from lxml import etree
from modela.records.api import ModelaDraft, ModelaRecord
from modelb.records.api import ModelbDraft, ModelbRecord
from modelc.records.api import ModelcDraft, ModelcRecord
from datetime import datetime, timedelta
from invenio_oaiserver.proxies import current_oaiserver
from invenio_db import db
from invenio_oaiserver.models import OAISet
from invenio_search.proxies import current_search_client

def datetime_to_datestamp(dt, day_granularity=False):
    """Transform datetime to datestamp.

    :param dt: The datetime to convert.
    :param day_granularity: Set day granularity on datestamp.
    :returns: The datestamp.
    """
    # assert dt.tzinfo is None  # only accept timezone naive datetimes
    # ignore microseconds
    if type(dt) == str:
        dt = datetime.fromisoformat(dt)

    dt = dt.replace(microsecond=0, tzinfo=None)
    result = dt.isoformat() + "Z"
    if day_granularity:
        result = result[:-10]
    return result

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

    rdm_records_service.publish(identity_simple, recorda["id"])
    rdm_records_service.publish(identity_simple, recordb["id"])

    resulta = client.get(f"/oai2d?verb=GetRecord&identifier=oai:oaioaioai:{recorda['id']}&metadataPrefix=oai_dc")
    resultb = client.get(f"/oai2d?verb=GetRecord&identifier=oai:oaioaioai:{recordb['id']}&metadataPrefix=oai_dc")


    check_record(etree.fromstring(resulta.data), f"oai:oaioaioai:{recorda['id']}")
    check_record(etree.fromstring(resultb.data), f"oai:oaioaioai:{recordb['id']}")


def test_list_records(app, rdm_records_service, identity_simple, workflow_data, users, logged_client, search_clear):
    user = users[0]
    client = logged_client(user)

    for _ in range(16):
        recorda = rdm_records_service.create(
            identity_simple, data={"$schema": "local://modela-1.0.0.json", **workflow_data, "files": {"enabled": False}}
        )
        rdm_records_service.publish(identity_simple, recorda["id"])

    for _ in range(16):
        recordb = rdm_records_service.create(
            identity_simple, data={"$schema": "local://modelb-1.0.0.json", **workflow_data, "files": {"enabled": False}}
        )
        rdm_records_service.publish(identity_simple, recordb["id"])

    ModelaRecord.index.refresh()
    ModelbRecord.index.refresh()
    ModelaDraft.index.refresh()
    ModelbDraft.index.refresh()

    result = client.get("/oai2d?verb=ListRecords&metadataPrefix=oai_dc")

    tree = etree.fromstring(result.data)

    assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1

    assert len(tree.xpath("/x:OAI-PMH/x:ListRecords", namespaces=NAMESPACES)) == 1
    assert (
            len(tree.xpath("/x:OAI-PMH/x:ListRecords/x:record", namespaces=NAMESPACES))
            == 10
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header", namespaces=NAMESPACES
                )
            )
            == 10
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:identifier",
                    namespaces=NAMESPACES,
                )
            )
            == 10
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:datestamp",
                    namespaces=NAMESPACES,
                )
            )
            == 10
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:metadata",
                    namespaces=NAMESPACES,
                )
            )
            == 10
    )

    # First resumption token
    resumption_token = tree.xpath(
        "/x:OAI-PMH/x:ListRecords/x:resumptionToken", namespaces=NAMESPACES
    )[0]
    assert resumption_token.text
    # Get data for resumption token
    with app.test_client() as c:
        result = c.get(
            "/oai2d?verb=ListRecords&resumptionToken={0}".format(
                resumption_token.text
            )
        )

    tree = etree.fromstring(result.data)
    assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1
    assert len(tree.xpath("/x:OAI-PMH/x:ListRecords", namespaces=NAMESPACES)) == 1
    assert (
            len(tree.xpath("/x:OAI-PMH/x:ListRecords/x:record", namespaces=NAMESPACES))
            == 10
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header", namespaces=NAMESPACES
                )
            )
            == 10
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:identifier",
                    namespaces=NAMESPACES,
                )
            )
            == 10
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:datestamp",
                    namespaces=NAMESPACES,
                )
            )
            == 10
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:metadata",
                    namespaces=NAMESPACES,
                )
            )
            == 10
    )

    # Second resumption token
    resumption_token = tree.xpath(
        "/x:OAI-PMH/x:ListRecords/x:resumptionToken", namespaces=NAMESPACES
    )[0]
    assert resumption_token.text
    # Get data for resumption token
    with app.test_client() as c:
        result = c.get(
            "/oai2d?verb=ListRecords&resumptionToken={0}".format(
                resumption_token.text
            )
        )

    tree = etree.fromstring(result.data)
    assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1
    assert len(tree.xpath("/x:OAI-PMH/x:ListRecords", namespaces=NAMESPACES)) == 1
    assert (
            len(tree.xpath("/x:OAI-PMH/x:ListRecords/x:record", namespaces=NAMESPACES))
            == 10
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header", namespaces=NAMESPACES
                )
            )
            == 10
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:identifier",
                    namespaces=NAMESPACES,
                )
            )
            == 10
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:datestamp",
                    namespaces=NAMESPACES,
                )
            )
            == 10
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:metadata",
                    namespaces=NAMESPACES,
                )
            )
            == 10
    )

    # Third resumption token
    resumption_token = tree.xpath(
        "/x:OAI-PMH/x:ListRecords/x:resumptionToken", namespaces=NAMESPACES
    )[0]
    assert resumption_token.text
    with app.test_client() as c:
        result = c.get(
            "/oai2d?verb=ListRecords&resumptionToken={0}".format(
                resumption_token.text
            )
        )

    tree = etree.fromstring(result.data)
    assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1
    assert len(tree.xpath("/x:OAI-PMH/x:ListRecords", namespaces=NAMESPACES)) == 1
    assert (
            len(tree.xpath("/x:OAI-PMH/x:ListRecords/x:record", namespaces=NAMESPACES))
            == 2
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header", namespaces=NAMESPACES
                )
            )
            == 2
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:identifier",
                    namespaces=NAMESPACES,
                )
            )
            == 2
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:header" "/x:datestamp",
                    namespaces=NAMESPACES,
                )
            )
            == 2
    )
    assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListRecords/x:record/x:metadata",
                    namespaces=NAMESPACES,
                )
            )
            == 2
    )

    # No fourth resumption token
    resumption_token = tree.xpath(
        "/x:OAI-PMH/x:ListRecords/x:resumptionToken", namespaces=NAMESPACES
    )[0]
    assert not resumption_token.text


    # Check from:until range
    with app.test_client() as c:
        # Check date and datetime timestamps.
        for granularity in (False, True):
            result = c.get(
                "/oai2d?verb=ListRecords&metadataPrefix=oai_dc"
                "&from={0}&until={1}".format(
                    datetime_to_datestamp(
                        datetime.fromisoformat(recordb.data['updated']) - timedelta(days=1),
                        day_granularity=granularity,
                    ),
                    datetime_to_datestamp(
                        datetime.fromisoformat(recordb.data['updated']) + timedelta(days=1),
                        day_granularity=granularity,
                    ),
                )
            )
            assert result.status_code == 200

            tree = etree.fromstring(result.data)
            assert (
                    len(
                        tree.xpath(
                            "/x:OAI-PMH/x:ListRecords/x:record", namespaces=NAMESPACES
                        )
                    )
                    == 10
            )

            # Check from:until range in resumption token
            resumption_token = tree.xpath(
                "/x:OAI-PMH/x:ListRecords/x:resumptionToken", namespaces=NAMESPACES
            )[0]
            assert resumption_token.text
            with app.test_client() as c:
                result = c.get(
                    "/oai2d?verb=ListRecords&resumptionToken={0}".format(
                        resumption_token.text
                    )
                )
            assert result.status_code == 200

def run_after_insert_oai_set():
    """Run task run_after_insert_oai_set."""
    for oaiset_id in [oaiset_.spec for oaiset_ in OAISet.query.all()]:
        oaiset = OAISet.query.filter_by(spec=oaiset_id).one()
        after_insert_oai_set(None, None, oaiset)

def test_listsets(app, search_clear):
    with app.test_request_context():
        current_oaiserver.unregister_signals_oaiset()
        with db.session.begin_nested():
            a = OAISet(
                spec="test", name="Test", description="test desc", system_created=False
            )
            db.session.add(a)

        with app.test_client() as c:
            result = c.get("/oai2d?verb=ListSets")

        tree = etree.fromstring(result.data)

        assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1

        assert len(tree.xpath("/x:OAI-PMH/x:ListSets", namespaces=NAMESPACES)) == 1
        assert (
            len(tree.xpath("/x:OAI-PMH/x:ListSets/x:set", namespaces=NAMESPACES)) == 1
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListSets/x:set/x:setSpec", namespaces=NAMESPACES
                )
            )
            == 1
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListSets/x:set/x:setName", namespaces=NAMESPACES
                )
            )
            == 1
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListSets/x:set/x:setDescription",
                    namespaces=NAMESPACES,
                )
            )
            == 1
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListSets/x:set/x:setDescription/y:dc",
                    namespaces=NAMESPACES,
                )
            )
            == 1
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListSets/x:set/x:setDescription/y:dc/"
                    "z:description",
                    namespaces=NAMESPACES,
                )
            )
            == 1
        )
        text = tree.xpath(
            "/x:OAI-PMH/x:ListSets/x:set/x:setDescription/y:dc/" "z:description/text()",
            namespaces=NAMESPACES,
        )
        assert len(text) == 1
        assert text[0] == "test desc"


def test_listidentifiers(app, rdm_records_service, identity_simple, workflow_data, search_clear):
    """Test verb ListIdentifiers."""
    from invenio_oaiserver.models import OAISet
    workflow_data_a = workflow_data | {"metadata": {"title": "lalala", "adescription": "bbbb"}}
    workflow_data_b = workflow_data | {"metadata": {"title": "lalala", "bdescription": "bbbb"}}
    workflow_data_c = workflow_data | {"metadata": {"title": "tralala", "cdescription": "cccc"}}

    with app.app_context():
        current_oaiserver.unregister_signals_oaiset()
        # create new OAI Set
        with db.session.begin_nested():
            oaiset1 = OAISet(
                spec="test0",
                name="Test0",
                description="test desc 0",
                search_pattern="metadata.title:lalala",
                system_created=False,
            )

            oaiset2 = OAISet(
                spec="bdescription",
                name="Bdescription",
                description="test b",
                search_pattern="metadata.bdescription:bbbb",
                system_created=False,
            )
            db.session.add(oaiset1)
            db.session.add(oaiset2)
        db.session.commit()

    run_after_insert_oai_set()

    recorda = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modela-1.0.0.json", **workflow_data_a, "files": {"enabled": False}}
    )
    recordb = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modelb-1.0.0.json", **workflow_data_b, "files": {"enabled": False}}
    )
    recordc = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modelc-1.0.0.json", **workflow_data_c, "files": {"enabled": False}}
    )
    recorda = rdm_records_service.publish(identity_simple, recorda["id"])
    recordb = rdm_records_service.publish(identity_simple, recordb["id"])
    recordc = rdm_records_service.publish(identity_simple, recordc["id"])

    ModelaRecord.index.refresh()
    ModelbRecord.index.refresh()
    ModelcRecord.index.refresh()
    ModelaDraft.index.refresh()
    ModelbDraft.index.refresh()
    ModelcDraft.index.refresh()

    with app.test_request_context():

        recorda_oai_pid = recorda['pids']['oai']['identifier']

        # get the list of identifiers
        with app.test_client() as c:
            result = c.get("/oai2d?verb=ListIdentifiers&metadataPrefix=oai_dc")

        tree = etree.fromstring(result.data)

        assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1
        assert (
            len(tree.xpath("/x:OAI-PMH/x:ListIdentifiers", namespaces=NAMESPACES)) == 1
        )
        assert (
            len(
                tree.xpath(
                    "/x:OAI-PMH/x:ListIdentifiers/x:header", namespaces=NAMESPACES
                )
            )
            == 3
        )
        identifier = tree.xpath(
            "/x:OAI-PMH/x:ListIdentifiers/x:header/x:identifier", namespaces=NAMESPACES
        )
        assert len(identifier) == 3
        assert identifier[0].text == str(recorda_oai_pid)
        datestamp = tree.xpath(
            "/x:OAI-PMH/x:ListIdentifiers/x:header/x:datestamp", namespaces=NAMESPACES
        )
        assert len(datestamp) == 3
        # assert datestamp[0].text == datetime_to_datestamp(record.updated)

        # Check from:until range
        with app.test_client() as c:
            # Check date and datetime timestamps.
            for granularity in (False, True):
                result = c.get(
                    "/oai2d?verb=ListIdentifiers&metadataPrefix=oai_dc"
                    "&from={0}&until={1}".format(
                        datetime_to_datestamp(
                            datetime.fromisoformat(recorda.data['updated']) - timedelta(1), day_granularity=granularity
                        ),
                        datetime_to_datestamp(
                            datetime.fromisoformat(recorda.data['updated']) + timedelta(1), day_granularity=granularity
                        ),
                    )
                )
                assert result.status_code == 200

                tree = etree.fromstring(result.data)
                identifier = tree.xpath(
                    "/x:OAI-PMH/x:ListIdentifiers/x:header/x:identifier",
                    namespaces=NAMESPACES,
                )
                assert len(identifier) == 3

        # check set param
        with app.test_client() as c:
            for granularity in (False, True):
                result_test0 = c.get(
                    "/oai2d?verb=ListIdentifiers&metadataPrefix=oai_dc"
                    "&set=test0".format(
                        datetime_to_datestamp(
                            datetime.fromisoformat(recorda.data['updated']) - timedelta(1), day_granularity=granularity
                        ),
                        datetime_to_datestamp(
                            datetime.fromisoformat(recorda.data['updated']) + timedelta(1), day_granularity=granularity
                        ),
                    )
                )
                result_b = c.get(
                    "/oai2d?verb=ListIdentifiers&metadataPrefix=oai_dc"
                    "&set=bdescription".format(
                        datetime_to_datestamp(
                            datetime.fromisoformat(recorda.data['updated']) - timedelta(1), day_granularity=granularity
                        ),
                        datetime_to_datestamp(
                            datetime.fromisoformat(recorda.data['updated']) + timedelta(1), day_granularity=granularity
                        ),
                    )
                )
                assert result_test0.status_code == 200
                assert result_b.status_code == 200

                tree = etree.fromstring(result_test0.data)
                identifier = tree.xpath(
                    "/x:OAI-PMH/x:ListIdentifiers/x:header/x:identifier",
                    namespaces=NAMESPACES,
                )
                assert len(identifier) == 2
                assert {identifier[0].text, identifier[1].text} == {recorda["pids"]["oai"]["identifier"], recordb["pids"]["oai"]["identifier"]}

                tree = etree.fromstring(result_b.data)
                identifier = tree.xpath(
                    "/x:OAI-PMH/x:ListIdentifiers/x:header/x:identifier",
                    namespaces=NAMESPACES,
                )
                assert len(identifier) == 1
                assert identifier[0].text == recordb["pids"]["oai"]["identifier"]

        # check from:until range and set param
        with app.test_client() as c:
            for granularity in (False, True):
                result = c.get(
                    "/oai2d?verb=ListIdentifiers&metadataPrefix=oai_dc"
                    "&from={0}&until={1}&set=test0".format(
                        datetime_to_datestamp(
                            datetime.fromisoformat(recorda.data['updated']) - timedelta(1), day_granularity=granularity
                        ),
                        datetime_to_datestamp(
                            datetime.fromisoformat(recorda.data['updated']) + timedelta(1), day_granularity=granularity
                        ),
                    )
                )
                assert result.status_code == 200

                tree = etree.fromstring(result.data)
                identifier = tree.xpath(
                    "/x:OAI-PMH/x:ListIdentifiers/x:header/x:identifier",
                    namespaces=NAMESPACES,
                )
                assert len(identifier) == 2

def test_listmetadataformats(app, search_clear):
    """Test ListMetadataFormats."""
    _listmetadataformats(app=app, query="/oai2d?verb=ListMetadataFormats")


def test_listmetadataformats_record(app, rdm_records_service, identity_simple, workflow_data, search_clear):
    """Test ListMetadataFormats for a record."""
    recorda = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modela-1.0.0.json", **workflow_data, "files": {"enabled": False}}
    )
    recorda = rdm_records_service.publish(identity_simple, recorda["id"])

    ModelaRecord.index.refresh()
    ModelaDraft.index.refresh()

    _listmetadataformats(
        app=app,
        query="/oai2d?verb=ListMetadataFormats&identifier={0}".format(recorda["pids"]["oai"]["identifier"]),
    )

def _listmetadataformats(app, query):
    """Try ListMetadataFormats."""
    with app.test_request_context():
        with app.test_client() as c:
            result = c.get(query)

        tree = etree.fromstring(result.data)

        assert len(tree.xpath("/x:OAI-PMH", namespaces=NAMESPACES)) == 1
        assert (
            len(tree.xpath("/x:OAI-PMH/x:ListMetadataFormats", namespaces=NAMESPACES))
            == 1
        )
        metadataFormats = tree.xpath(
            "/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat", namespaces=NAMESPACES
        )
        cfg_metadataFormats = copy.deepcopy(app.config.get("OAISERVER_METADATA_FORMATS", {}))
        assert len(metadataFormats) == len(cfg_metadataFormats)

        prefixes = tree.xpath(
            "/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat/" "x:metadataPrefix",
            namespaces=NAMESPACES,
        )
        assert len(prefixes) == len(cfg_metadataFormats)
        assert all(pfx.text in cfg_metadataFormats for pfx in prefixes)

        schemas = tree.xpath(
            "/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat/" "x:schema",
            namespaces=NAMESPACES,
        )
        assert len(schemas) == len(cfg_metadataFormats)
        assert all(
            sch.text in cfg_metadataFormats[pfx.text]["schema"]
            for sch, pfx in zip(schemas, prefixes)
        )

        metadataNamespaces = tree.xpath(
            "/x:OAI-PMH/x:ListMetadataFormats/x:metadataFormat/" "x:metadataNamespace",
            namespaces=NAMESPACES,
        )
        assert len(metadataNamespaces) == len(cfg_metadataFormats)
        assert all(
            nsp.text in cfg_metadataFormats[pfx.text]["namespace"]
            for nsp, pfx in zip(metadataNamespaces, prefixes)
        )


def test_search_pattern_change(app, rdm_records_service, identity_simple, workflow_data, search_clear):
    """Test search pattern change."""
    data = workflow_data | {"metadata": {"title": "lalala", "adescription": "bbbb"}}
    recorda = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modela-1.0.0.json", **data, "files": {"enabled": False}})
    recorda = rdm_records_service.publish(identity_simple, recorda["id"])

    with app.app_context():
        # create new OAI Set
        with db.session.begin_nested():
            oaiset = OAISet(
                spec="test0",
                name="test",
                description="test desc 0",
                search_pattern="metadata.title:lalala",
                system_created=False,
            )
            db.session.add(oaiset)
        db.session.commit()
        # check record is in set
        time.sleep(0.5)
        rec_in_set = get_records(set="test0")
        assert rec_in_set.total == 1
        rec = next(rec_in_set.items)
        assert rec["json"]["_source"]["metadata"]["title"] == "lalala"

        # change search pattern
        oaiset.search_pattern = "metadata.title:itsnothere"
        db.session.merge(oaiset)
        db.session.commit()
        # check records is not in set
        with pytest.raises(OAINoRecordsMatchError):
            get_records(set="test0")

def test_search_pattern_change_percolators(app, rdm_records_service, identity_simple, workflow_data, search_clear):
    """Test search pattern changes in percolator indices."""
    data1 = workflow_data | {"metadata": {"title": "lalala", "adescription": "bbbb"}}
    data2 = workflow_data | {"metadata": {"title": "tralala", "adescription": "bbbb"}}
    record1 = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modela-1.0.0.json", **data1, "files": {"enabled": False}})

    record2 = rdm_records_service.create(
        identity_simple, data={"$schema": "local://modela-1.0.0.json", **data2, "files": {"enabled": False}})
    record1 = rdm_records_service.publish(identity_simple, record1["id"])
    record2 = rdm_records_service.publish(identity_simple, record2["id"])

    record_index = record1._record.index._name
    percolator_index = _build_percolator_index_name(record_index)

    with app.app_context():
        # create new OAI Set
        with db.session.begin_nested():
            oaiset = OAISet(
                spec="test0",
                name="test",
                description="test desc 0",
                search_pattern="metadata.title:lalala",
                system_created=False,
            )
            db.session.add(oaiset)
        db.session.commit()
        # check record is in set
        current_search_client.indices.refresh(index=percolator_index)
        sets_before_change = current_oaiserver.record_list_sets_fetcher([record1, record2])

        oaiset.search_pattern = "metadata.title:tralala"
        db.session.merge(oaiset)
        db.session.commit()

        current_search_client.indices.refresh(index=percolator_index)
        sets_after_change = current_oaiserver.record_list_sets_fetcher([record1, record2])

        import pdb
        if not sets_after_change == [[], ['test0']]:
            pdb.set_trace()

        assert sets_before_change == [['test0'], []]
        assert sets_after_change == [[], ['test0']]






