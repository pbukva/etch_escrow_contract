import os
import time
import types
import logging
import base64 as b64
from pathlib import Path
from contextlib import contextmanager
from typing import List, Optional, Tuple, Iterable
from getpass import getpass

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

from fetchai.ledger.api import LedgerApi, TokenApi, ApiError
from fetchai.ledger.api.contracts import ContractTxFactory
from fetchai.ledger.api.token import AddressLike, TokenTxFactory
from fetchai.ledger.crypto import Entity, Address, Identity
from fetchai.ledger.crypto.deed import Deed
from fetchai.ledger.contract import Contract


EntityList = List[Entity]

LEDGER_HOST = os.environ.get('FETCH_LEDGER_HOST', 'localhost')
FETCH_SERVICE_ACCOUNT_KEY = os.environ.get("FETCH_SERVICE_ACCOUNT_KEY",
                                           "dbc95564f5671769f150faf93701a2514bfc496b387bfa9af675ba9f5510fe94")
ETCH_CONTRACT_NONCE = os.environ.get('ETCH_CONTRACT_NONCE', "ioufqiubviq")
if os.path.exists("../erc20_migration_contract.etch"):
    ETCH_CONTRACT_ROOT = Path(__file__).resolve().parent.parent
else:
    ETCH_CONTRACT_ROOT = Path(__file__).resolve().parent.parent / 'ERC20-migration' / 'fet_contrat'

FETFees = 100000


@contextmanager
def track_cost(api: TokenApi, entity: Entity, message: str):
    """
    Context manager for recording the change in balance over a set of actions
    Will be inaccurate if other factors change an account balance
    """
    if isinstance(entity, Entity):
        entity = Address(entity)
    elif not isinstance(entity, Address):
        raise TypeError("Expecting Entity or Address")

    balance_before = api.balance(entity)
    yield

    if not message:
        message = "Actions cost: "

    print(message + "{} TOK".format(api.balance(entity) - balance_before))


def connect_ledger(network: Optional[str] = None, host: Optional[str] = '127.0.0.1', port: Optional[int] = 8000):
    for _ in range(0, 200):
        try:
            if network:
                logger.info(f"Connecting to {network} ledger network ...")
                api = LedgerApi(network=network)
            else:
                logger.info("Connecting to ledger {}:{} ...".format(host, port))
                api = LedgerApi(host, port)

            break

        except Exception as ex:
            logger.error("Unable to connect to ledger {}:{} ...".format(host, port))
            time.sleep(5)

    if not api:
        exit(1)

    tokens_api = api.tokens
    if not callable(getattr(tokens_api, "query_deed", None)):
        def query_deed(self, address: AddressLike):
            """
            Query the deed for a given address from the remote node

            :param address: The base58 encoded string containing the address of the node
            :return: The deed json response received from ledger
            :raises: ApiError on any failures
            """

            # convert the input to an address
            address = Address(address)

            # format and make the request
            request = {
                'address': str(address)
            }
            success, data = self._post_json('queryDeed', request)

            # check for error cases
            if not success:
                raise ApiError(f'Failed to query deed for the {address} address')

            return data

        # Extend instance of the TokenApi class with missing method
        tokens_api.query_deed = types.MethodType(query_deed, tokens_api)

    def deploy_deed(self, address: AddressLike, deed: Optional[Deed], fee: int, signatories: Iterable[Identity]):
        """
        Deploys the deed on `address`.

        :param address: Address where the deed will be deployed
        :param deed: The deed to set
        :param fee: Fee in Canonical FET
        :param signatories: The entities that will sign this action
        :return: The digest of the submitted transaction
        :raises: ApiError on any failures
        """

        tx = TokenTxFactory.deed(address, deed, fee, signatories)
        self._set_validity_period(tx)

        for signatory in signatories:
            tx.sign(signatory)

        return self.submit_signed_tx(tx)

    # Extend instance of the TokenApi class with missing method
    tokens_api.deed = types.MethodType(deploy_deed, tokens_api)

    return api


def get_contract_text(contract_dir, contract_name: str):
    with open(contract_dir / contract_name, 'r') as f:
        contract_text = f.read()
    return contract_text


def get_contract(contract_dir: Path, contract_name: str, owner: Entity, contract_nonce: str):
    owner_addr = Address(owner)
    contract_text = get_contract_text(contract_dir, contract_name)
    contract = Contract(contract_text, owner_addr, contract_nonce.encode())
    logger.info(f"Contract text for {contract_name} loaded:")
    logger.info(f"Address: {contract.address}")
    logger.info(f"Owner: f{owner_addr}")
    return contract


def deploy_contract(api: LedgerApi, contract: Contract, fee: int, signatories: EntityList,
                    transfers: Optional[List[Tuple]] = None):
    #TODO(pb: issue_with_v1.0.2): Commenting out as temorary workaround bellow
    #tx = contract.create_as_tx(api=api, from_address=contract.owner, fee=fee, signers=signatories)

    #TODO(pb: issue_with_v1.0.2): Temorary workaround for above commented-out code
    shard_mask = None
    tx = ContractTxFactory.create(contract.owner, contract, fee, signatories, shard_mask)
    api.set_validity_period(tx)

    for address, amount in transfers if transfers else []:
        tx.add_transfer(address, amount)

    for signatory in signatories:
        tx.sign(signatory)

    tx_hash = api.submit_signed_tx(tx)
    api.sync([tx_hash])
    return tx_hash


def entity_from_string(priv_key: str):
    try:
        return Entity.from_hex(priv_key)
    except Exception as _:
        try:
            return Entity.from_base64(priv_key)
        except Exception as _:
            pass

    return None


def collect_single_signatory_from_user_input(signee: Optional[AddressLike] = None):
    if signee:
        signee = Address(signee)
        key_query_msg = f"Private key for {{{signee}}} signee (hex or base64): "
    else:
        key_query_msg = "Private key for signee (hex or base64): "

    signatory = None
    while not signatory:
        signer_priv_key = getpass(key_query_msg)
        signatory = entity_from_string(signer_priv_key)

        if not signatory:
            print(f"Invalid key: Unable to parse the key.")
        elif signee and signee != Address(signatory):
            print(f"Invalid key: Key does not correspond to the address requested.")
            signatory = None

        if not signatory:
            resp = input("\nWant to re-enter the key again? [y/N]: ").lower()
            if resp != "y":
                break

    return signatory


def collect_private_keys_from_user_input(signees: Iterable[AddressLike] = None):
    signatories_set = set()
    signatories = []

    def iterator():
        if signees is None:
            while True:
                yield None
        else:
            for signee in signees:
                if signee:
                    yield signee

    for signee in iterator():
        signatory = collect_single_signatory_from_user_input(signee)

        if not signatory:
            print("Exiting ...")
            exit(-1)

        if signatory not in signatories_set:
            signatories_set.add(signatory)
            signatories.append(signatory)
            print(f"Added new signatory[{len(signatories)-1}] with address {Address(signatory)}")
        else:
            print(f"The {Address(signatory)} signatory already exists => omitting.")

        resp = input("\nContinue with next key? [y/N]: ").lower()

        if resp != "y":
            break

    return signatories


def decode_uint_b64(value: str) -> int:
    return int.from_bytes(b64.b64decode(value), byteorder='big', signed=False)


def encode_uint_b64(value: int) -> str:
    return b64.b64encode(value.to_bytes((value.bit_length() + 7) // 8, byteorder='big', signed=False)).decode()


class AddressEx(Address):
    def __repr__(self):
        return self._display


class FetchTxDigest:
    def __init__(self, digest: int):
        self.digest = int(digest)

    def __repr__(self):
        return self.digest.to_bytes((self.digest.bit_length() + 7) // 8, byteorder='big', signed=False).hex()

    @staticmethod
    def decode(value: str) -> 'FetchTxDigest':
        return FetchTxDigest(decode_uint_b64(value)) if value else None

    @staticmethod
    def encode(value: 'FetchTxDigest') -> str:
        return encode_uint_b64(value.digest)


def decode_fetch_address(value: str) -> Address:
    return AddressEx(value) if value else None


def encode_fetch_address(value: Address) -> str:
    return str(value)


def decode_bool(value: str) -> bool:
    low_value = value.lower()
    if low_value == "true":
        return True
    elif low_value == "false":
        return False

    raise ValueError(f'Value "{value}" can not be converted to boolean type')


def encode_bool(value: bool) -> str:
    return str(value).lower()
