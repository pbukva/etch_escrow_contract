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
                            encode_bool, decode_bool, \
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
    sellerOk: bool = field(
        default=None,
        metadata=config(
            encoder=encode_bool,
            decoder=decode_bool,
        ))
    buyerOk: bool = field(
        default=None,
        metadata=config(
            encoder=encode_bool,
            decoder=decode_bool,
        ))


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

    resp = input("\n\nAre contract deployment data above correct? [y/N]: ").lower()

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

def query_deposited_balance(api: LedgerApi, args):
    addr = Address(args.contract_address)
    success, response = api.contracts.query(addr, "deposited_balance")
    ms = None
    if success and response and response["status"] == "success":
        balance = response["result"]
    print(f'Deposited balance of the contract: {balance} [Canonical FET]')

def action_deposit(api: LedgerApi, args):
    fetch_contract_addr = Address(args.contract_address)
    source_fetch_addr = Address(args.from_address)
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
    source_fetch_addr = Address(args.from_address)
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
    source_fetch_addr = Address(args.from_address)
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
    source_fetch_addr = Address(args.from_address)
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
    source_fetch_addr = Address(args.from_address)
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
    parser = ap.ArgumentParser(description='Interaction with Escrow Etch contract')
    parser.set_defaults(func=lambda *args: parser.print_help())

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
                        help="List of exactly 2 transfers - the first transfer' dest. address represents SELLER, the second transfer' dest. address represents BUYER. Each transfer in form of coma separated vector DEST_FET_ADDR,AMOUNT \
                              where AMOUNT is specified in Canonical FET unit (**minimum** amount value is 1 [Canonical FET] (due to limitation in python fetch ledger api, not ledger itself)")
    parser_deploy.set_defaults(func=deploy_contract_local)

    parser_query = subparsers.add_parser('query', help='Query contract states')
    parser_query.add_argument('contract_address', type=str, help="Address where the contract is deployed")
    query_subparsers = parser_query.add_subparsers(help='sub-command help')

    parser_query_deposited_balance = query_subparsers.add_parser('balance', help='Query value of deposited balance, prints in [Canonical FET]')
    parser_query_deposited_balance.set_defaults(func=query_deposited_balance)

    parser_query_contract_status = query_subparsers.add_parser('status', help='Query contract status structure')
    parser_query_contract_status.set_defaults(func=query_contract_status)

    parser_action = subparsers.add_parser('action', help='Executes contract actions')
    parser_action.add_argument('contract_address', type=str, help="Address where the contract is deployed")
    parser_action.add_argument('from_address', type=str,
                                      help="Fetch native address of the party which is interacting with the contract (escrow, buyer, seller, etc. ...)")
    parser_action.add_argument('--fee', type=int, default=10000,
                                       help="Fee for Tx execution in [Canonical FET]")
    action_subparsers = parser_action.add_subparsers(help='sub-command help')

    parser_action_deposit = action_subparsers.add_parser('deposit', help='Deposits funds to escrow contract')
    parser_action_deposit.add_argument('amount', type=int,
                                       help="Amount of FET tokens to deposit in [Canonical FET]")
    parser_action_deposit.set_defaults(func=action_deposit)


    parser_action_accept = action_subparsers.add_parser('accept', help='Accepts the terms in escrow')
    parser_action_accept.set_defaults(func=action_accept)


    parser_action_cancel = action_subparsers.add_parser('cancel', help='Cancels participation in escrow contract, and returns locked balance funds to buyer IF both sides cancelled')
    parser_action_cancel.set_defaults(func=action_cancel)


    parser_action_kill = action_subparsers.add_parser('kill', help='Kills escrow contract and refunds locked balnce funds to buyer')
    parser_action_kill.set_defaults(func=action_cancel)


    parser_action_withdraw_excess = action_subparsers.add_parser('withdraw-excess', help='Withdraws excess balance(= everything **above** locked balance) from contract and sends it to owner/escrow address.')
    parser_action_withdraw_excess.set_defaults(func=action_withdrawExcessBalance)

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
    print("=======================")
    args.func(api, args)
    print("=======================")

if __name__ == '__main__':
    main()
