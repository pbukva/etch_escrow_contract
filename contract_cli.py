#!/usr/bin/env python3

import argparse as ap
import traceback
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, config
from typing import Tuple

from fetchai.ledger.crypto import Entity, Address
from fetchai.ledger.contract import Contract
from fetchai.ledger.api import LedgerApi
from fetchai.ledger.api.contracts import ContractTxFactory
from fet_tools.tools import deploy_contract, track_cost, connect_ledger,\
                            collect_private_keys_from_user_input,\
                            encode_uint_b64, decode_uint_b64, \
                            encode_fetch_address, decode_fetch_address, \
                            FetchTxDigest


class ExtendAction(ap.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest) or []
        items.extend(values)
        setattr(namespace, self.dest, items)


@dataclass_json
@dataclass(order=True)
class ContractStatus:
    buyer: Address = field(
        default=None,
        metadata=config(
            encoder=encode_fetch_address,
            decoder=decode_fetch_address,
        ))
    seller: Address = field(
        default=None,
        metadata=config(
            encoder=encode_fetch_address,
            decoder=decode_fetch_address,
        ))
    escrow: Address = field(
        default=None,
        metadata=config(
            encoder=encode_fetch_address,
            decoder=decode_fetch_address,
        ))
    balance: int = 0
    start: int = 0
    settledSinceBlock: int = 0xFFFFFFFFFFFFFFFF
    buyerOk: bool = False
    sellerOk: bool = False


def deploy_contract_local(api: LedgerApi, args):
    contract_owner_address = Address(args.contract_owner_address)

    with open(args.contract_file, 'r') as ct:
        contract_text = ct.read()

    # create the smart contract
    contract = Contract(contract_text, contract_owner_address, args.contract_deployment_nonce.encode())
    print(f"contract source code:\n{contract.source}\n\n")
    print(f"owner address: {contract.owner}")
    print(f"nonce: {contract.nonce}")
    print(f"contract address: {contract.address}")
    print(f"contract source code digest: {contract.digest}")

    resp = input("\n\nAre contract deployment data above correct? [y/N]").lower()

    if resp != "y":
        print("Exiting ...")
        exit(-1)

    transfers = parse_transfers(args)
    if transfers:
        print("Transfers:")
        for address, amount in transfers:
            print(f"Dest. address {{{address}}}: amount={amount} [Canonical FET]")

        resp = input("\n\nAre transfers correct? [y/N]: ").lower()

        if resp != "y":
            print("Exiting ...")
            exit(-1)

    signatories = collect_private_keys_from_user_input()

    with track_cost(api.tokens, contract.owner, "Cost of creation: "):
        api.sync(deploy_contract(api, contract, args.fee, signatories, transfers))

    print("Contract has been successfully deployed.")


def query_contract_status_ex(api: LedgerApi, args) -> Tuple[ContractStatus, Address]:
    addr = Address(args.contract_address)
    success, contract_status = api.contracts.query(addr, "status")
    ms = None
    if success and contract_status and contract_status["status"] == "success":
        ms = ContractStatus.from_dict(contract_status["result"])
    return ms, addr


def query_contract_status(api: LedgerApi, args):
    ms, addr = query_contract_status_ex(api, args)
    print(f'Contract status of the contract at the {{{addr}}} address: {ms!s}')


def action_deposit(api: LedgerApi, args):
    fetch_contract_addr = Address(args.contract_address)
    source_fetch_addr = Address(args.source_fetch_address)
    signatories = collect_private_keys_from_user_input()

    tx = ContractTxFactory.action(source_fetch_addr,
                                  fetch_contract_addr,
                                  "deposit",
                                  args.fee,
                                  signatories)

    api.set_validity_period(tx)
    tx.add_transfer(fetch_contract_addr, args.amount)
    for signatory in signatories:
        tx.sign(signatory)

    with track_cost(api.tokens, source_fetch_addr, "Cost of migration action Tx: "):
        api.sync(api.submit_signed_tx(tx))

    print(f'Deposit has been successful')


def action_accept(api: LedgerApi, args):
    fetch_contract_addr = Address(args.contract_address)
    source_fetch_addr = Address(args.source_fetch_address)
    signatories = collect_private_keys_from_user_input()

    tx = ContractTxFactory.action(source_fetch_addr,
                                  fetch_contract_addr,
                                  "accept",
                                  args.fee,
                                  signatories)

    api.set_validity_period(tx)
    for signatory in signatories:
        tx.sign(signatory)

    with track_cost(api.tokens, source_fetch_addr, "Cost of migration action Tx: "):
        api.sync(api.submit_signed_tx(tx))

    print(f'Accept action has been successful')


def action_cancel(api: LedgerApi, args):
    fetch_contract_addr = Address(args.contract_address)
    source_fetch_addr = Address(args.source_fetch_address)
    signatories = collect_private_keys_from_user_input()

    tx = ContractTxFactory.action(source_fetch_addr,
                                  fetch_contract_addr,
                                  "cancel",
                                  args.fee,
                                  signatories)

    api.set_validity_period(tx)
    for signatory in signatories:
        tx.sign(signatory)

    with track_cost(api.tokens, source_fetch_addr, "Cost of migration action Tx: "):
        api.sync(api.submit_signed_tx(tx))

    print(f'Cancel action has been successful')


def action_kill(api: LedgerApi, args):
    fetch_contract_addr = Address(args.contract_address)
    source_fetch_addr = Address(args.source_fetch_address)
    signatories = collect_private_keys_from_user_input()

    tx = ContractTxFactory.action(source_fetch_addr,
                                  fetch_contract_addr,
                                  "kill",
                                  args.fee,
                                  signatories)

    api.set_validity_period(tx)
    for signatory in signatories:
        tx.sign(signatory)

    with track_cost(api.tokens, source_fetch_addr, "Cost of migration action Tx: "):
        api.sync(api.submit_signed_tx(tx))

    print(f'Kill action has been successful')


def action_withdrawExcessBalance(api: LedgerApi, args):
    fetch_contract_addr = Address(args.contract_address)
    source_fetch_addr = Address(args.source_fetch_address)
    signatories = collect_private_keys_from_user_input()

    tx = ContractTxFactory.action(source_fetch_addr,
                                  fetch_contract_addr,
                                  "withdrawExcessBalance",
                                  args.fee,
                                  signatories)

    api.set_validity_period(tx)
    for signatory in signatories:
        tx.sign(signatory)

    with track_cost(api.tokens, source_fetch_addr, "Cost of migration action Tx: "):
        api.sync(api.submit_signed_tx(tx))

    print(f'Kill action has been successful')


def action_withdrawExcessBalance(api: LedgerApi, args):
    ms, fetch_contract_addr = query_contract_status_ex(api, args)
    if ms is None:
        raise RuntimeError("Unable to fetch MigrationStatus from the contract")

    signatories = collect_private_keys_from_user_input()

    tx = ContractTxFactory.action(ms.authAddr,
                                  fetch_contract_addr,
                                  "refund",
                                  args.fee,
                                  signatories,
                                  args.swap_id)
    api.set_validity_period(tx)
    for signatory in signatories:
        tx.sign(signatory)

    with track_cost(api.tokens, ms.authAddr, "Cost of refund action Tx: "):
        api.sync(api.submit_signed_tx(tx))

    print(f'Refund has been successful')


def parse_arguments():
    parser = ap.ArgumentParser(description='Interaction with Migration Etch contract for Native->ERC20 direction.')

    parser.add_argument("--hostname", type=str, default="127.0.0.1", help="Hostname of the node")
    parser.add_argument("--port", type=int, default="8000", help="Port of the node")
    parser.add_argument("--network", type=str, default=None, help="Fetch network to deploy contract to")

    subparsers = parser.add_subparsers(help='sub-command help')

    parser_deploy = subparsers.add_parser('deploy', help='Deploys the contract')
    parser_deploy.register('action', 'extend', ExtendAction)
    parser_deploy.add_argument("contract_file", type=str, metavar="contract_file", help="Filename of the etch contract code")
    parser_deploy.add_argument("contract_owner_address", type=str, help="Contract owner address")
    parser_deploy.add_argument("contract_deployment_nonce", type=str, help="Nonce of the contract deployment")
    parser_deploy.add_argument('--fee', type=int, default=600000,
                           help="Fee for Tx execution in [Canonical FET]")
    parser_deploy.add_argument("--transfers", type=str, action="extend", nargs="+",
                        help="List of transfers, each transfer in form of coma separated vector DEST_FET_ADDR,AMOUNT \
                              where AMOUNT is specified in Canonical FET unit")
    parser_deploy.set_defaults(func=deploy_contract_local)

    parser_query = subparsers.add_parser('query', help='Query contract states')
    parser_query.add_argument('contract_address', type=str, help="Address where the contract is deployed")
    query_subparsers = parser_query.add_subparsers(help='sub-command help')

    parser_query_migration_status = query_subparsers.add_parser('migration_status', help='Query contract migration status structure')
    parser_query_migration_status.set_defaults(func=query_contract_status)


    parser_action = subparsers.add_parser('action', help='Executes contract actions')
    parser_action.add_argument('contract_address', type=str, help="Address where the contract is deployed")
    parser_action.add_argument('--fee', type=int, default=10000,
                                       help="Fee for Tx execution in [Canonical FET]")
    action_subparsers = parser_action.add_subparsers(help='sub-command help')

    parser_action_migrate = action_subparsers.add_parser('deposit', help='Deposits funds to escrow contract')
    parser_action_migrate.add_argument('source_fetch_address', type=str, help="Fetch native address where funds will be withdrawn FROM")
    parser_action_migrate.add_argument('amount', type=int,
                                       help="Amount of FET tokens to deposit in [Canonical FET]")
    parser_action_migrate.set_defaults(func=action_deposit)


    parser_action_migrate = action_subparsers.add_parser('accept', help='Accepts the terms in escrow')
    parser_action_migrate.set_defaults(func=action_accept)


    parser_action_migrate = action_subparsers.add_parser('cancel', help='Cancels participation in escrow contract, and returns locked balance funds to buyer IF both sides cancelled')
    parser_action_migrate.set_defaults(func=action_cancel)


    parser_action_migrate = action_subparsers.add_parser('kill', help='Kills escrow contract and refunds locked balnce funds to buyer')
    parser_action_migrate.set_defaults(func=action_cancel)


    parser_action_migrate = action_subparsers.add_parser('withdraw-excess', help='Withdraws excess balance(= everything **above** locked balance) from contract and sends it to owner/escrow address.')
    parser_action_migrate.set_defaults(func=action_withdrawExcessBalance)

    return parser.parse_args(), parser


def parse_transfers(args):
    transfers = []
    for tran in args.transfers:
        address, amount_str = tuple(tran.split(","))
        transfers.append((Address(address), int(amount_str)))
    return transfers


def main():
    args, parser = parse_arguments()
    print(f"Arguments = {args}")

    api = connect_ledger(network=args.network, host=args.hostname, port=args.port)
    try:
        print("=======================")
        args.func(api, args)
        print("=======================")
    except AttributeError:
        traceback.print_exc()
        parser.print_help()
        parser.exit()


if __name__ == '__main__':
    main()
