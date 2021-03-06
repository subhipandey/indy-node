import json
import pytest

from indy.anoncreds import issuer_create_and_store_credential_def
from indy.ledger import build_cred_def_request, parse_get_schema_response, \
    build_get_schema_request
from indy_common.constants import REF

from indy_node.test.api.helper import sdk_write_schema
from indy_node.test.helper import modify_field

from plenum.common.types import OPERATION
from plenum.test.helper import sdk_sign_and_submit_req, sdk_get_and_check_replies, sdk_get_reply


@pytest.fixture(scope="module")
def schema_json(looper, sdk_pool_handle, sdk_wallet_trustee):
    wallet_handle, identifier = sdk_wallet_trustee
    schema_json, _ = sdk_write_schema(looper, sdk_pool_handle, sdk_wallet_trustee)
    schema_id = json.loads(schema_json)['id']

    request = looper.loop.run_until_complete(build_get_schema_request(identifier, schema_id))
    reply = sdk_get_reply(looper, sdk_sign_and_submit_req(sdk_pool_handle, sdk_wallet_trustee, request))[1]
    _, schema_json = looper.loop.run_until_complete(parse_get_schema_response(json.dumps(reply)))
    return schema_json


def test_send_claim_def_succeeds(
        looper, sdk_pool_handle, nodeSet, sdk_wallet_trustee, schema_json):
    wallet_handle, identifier = sdk_wallet_trustee

    _, definition_json = looper.loop.run_until_complete(issuer_create_and_store_credential_def(
        wallet_handle, identifier, schema_json, "some_tag", "CL", json.dumps({"support_revocation": True})))
    request = looper.loop.run_until_complete(build_cred_def_request(identifier, definition_json))
    reply = sdk_get_and_check_replies(looper, [sdk_sign_and_submit_req(sdk_pool_handle, sdk_wallet_trustee, request)])


@pytest.mark.skip(reason="INDY-1862")
def test_send_claim_def_fails_if_ref_is_seqno_of_non_schema_txn(
        looper, sdk_pool_handle, nodeSet, sdk_wallet_trustee, schema_json):
    wallet_handle, identifier = sdk_wallet_trustee
    request = modify_field(schema_json, 9999, 'seq_no')

    _, definition_json = looper.loop.run_until_complete(issuer_create_and_store_credential_def(
        wallet_handle, identifier, schema_json, "some_tag1", "CL", json.dumps({"support_revocation": True})))
    request = looper.loop.run_until_complete(build_cred_def_request(identifier, definition_json))
    request = modify_field(request, 9999, OPERATION, REF)
    reply = sdk_get_and_check_replies(looper, [sdk_sign_and_submit_req(sdk_pool_handle, sdk_wallet_trustee, request)])


@pytest.mark.skip(reason="INDY-1862")
def test_send_claim_def_fails_if_ref_is_not_existing_seqno(
        looper, sdk_pool_handle, nodeSet, sdk_wallet_trustee, schema_json):
    wallet_handle, identifier = sdk_wallet_trustee

    _, definition_json = looper.loop.run_until_complete(issuer_create_and_store_credential_def(
        wallet_handle, identifier, schema_json, "some_tag1", "CL", json.dumps({"support_revocation": True})))
    request = looper.loop.run_until_complete(build_cred_def_request(identifier, definition_json))
    request = modify_field(request, 999999, OPERATION, REF)
    sdk_get_and_check_replies(looper, [sdk_sign_and_submit_req(sdk_pool_handle, sdk_wallet_trustee, request)])


def test_update_claim_def_for_same_schema_and_signature_type(
        looper, sdk_pool_handle, nodeSet, sdk_wallet_trustee, schema_json):
    wallet_handle, identifier = sdk_wallet_trustee

    _, definition_json = looper.loop.run_until_complete(issuer_create_and_store_credential_def(
        wallet_handle, identifier, schema_json, "some_tag1", "CL", json.dumps({"support_revocation": True})))
    request = looper.loop.run_until_complete(build_cred_def_request(identifier, definition_json))
    sdk_get_and_check_replies(looper, [sdk_sign_and_submit_req(sdk_pool_handle, sdk_wallet_trustee, request)])

    definition_json = modify_field(definition_json, '999', 'value', 'primary', 'n')
    request = looper.loop.run_until_complete(build_cred_def_request(identifier, definition_json))
    sdk_get_and_check_replies(looper, [sdk_sign_and_submit_req(sdk_pool_handle, sdk_wallet_trustee, request)])


def test_can_send_same_claim_def_by_different_issuers(
        looper, sdk_pool_handle, nodeSet, sdk_wallet_trustee, sdk_wallet_steward, schema_json):
    wallet_handle, identifier = sdk_wallet_trustee

    _, definition_json = looper.loop.run_until_complete(issuer_create_and_store_credential_def(
        wallet_handle, identifier, schema_json, "some_tag2", "CL", json.dumps({"support_revocation": True})))
    request = looper.loop.run_until_complete(build_cred_def_request(identifier, definition_json))
    sdk_get_and_check_replies(looper, [sdk_sign_and_submit_req(sdk_pool_handle, sdk_wallet_trustee, request)])

    wallet_handle, identifier = sdk_wallet_steward
    _, definition_json = looper.loop.run_until_complete(issuer_create_and_store_credential_def(
        wallet_handle, identifier, schema_json, "some_tag2", "CL", json.dumps({"support_revocation": True})))
    request = looper.loop.run_until_complete(build_cred_def_request(identifier, definition_json))
    sdk_get_and_check_replies(looper, [sdk_sign_and_submit_req(sdk_pool_handle, sdk_wallet_steward, request)])
