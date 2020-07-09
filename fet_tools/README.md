# Pre-requisites / Setup:

```shell script
pipenv install
pipenv shell
```


# Test Keys:
Keys used for testing:

```json
[
    {   "NAME": "contract owner/escrow",
        "address": "EytD7XFBDdw9J2KdaAmnpWKTwC6meKrFsCmzf1VZPV6vGSSWn",
        "priv_key_b64": "28lVZPVnF2nxUPr5NwGiUUv8SWs4e/qa9nW6n1UQ/pQ=",
        "priv_key_hex": "dbc95564f5671769f150faf93701a2514bfc496b387bfa9af675ba9f5510fe94",
        "pub_key_b64": "ADEpiFnB0+SDCXAMcyU+3ngI2QQDAhw/izgU/Hhh4TxSCJkaSLjrQHdVxqmmC7x1Qd2/kgthpT4cLwp0btRYrw==",
        "pub_key_hex": "0031298859c1d3e48309700c73253ede7808d90403021c3f8b3814fc7861e13c5208991a48b8eb407755c6a9a60bbc7541ddbf920b61a53e1c2f0a746ed458af"
    },
    {
        "NAME": "seller",
        "address": "EytD7XFBDdw9J2KdaAmnpWKTwC6meKrFsCmzf1VZPV6vGSSWn",
        "priv_key_b64": "MedebE2kD9dMVskGP+2fCz8DUZvdxbNXJ8VHtGXlt+w=",
        "priv_key_hex": "31e75e6c4da40fd74c56c9063fed9f0b3f03519bddc5b35727c547b465e5b7ec",
        "pub_key_b64": "JubZ14UU8JuaM3+HN5xfF0K/bkEKErdXekltcwWAtBQRlYXqwfGaiy2VDVUcfLmnxNIsJtYPLGnlHpn1J/WZOw==",
        "pub_key_hex": "26e6d9d78514f09b9a337f87379c5f1742bf6e410a12b7577a496d730580b414119585eac1f19a8b2d950d551c7cb9a7c4d22c26d60f2c69e51e99f527f5993b"
    },
    {
        "NAME": "buyer",
        "address": "2s83Wma33nDUdfqRRoBjNXBN3RxXH7B45Zw55WNhgus2YECjh1",
        "priv_key_b64": "fegLnkHXBmyJHAkO1OO234nR/9MuNTPNfcuGHZpBn/w=",
        "priv_key_hex": "7de80b9e41d7066c891c090ed4e3b6df89d1ffd32e3533cd7dcb861d9a419ffc",
        "pub_key_b64": "W5OKg+XYC6YYjhbYnlR2VENTFv/pPrYCnVUiLRFs7GpQdAYPhdO5N9EulpnNeEmFEUf42g6bmVqPhZH+2E4/XQ==",
        "pub_key_hex": "5b938a83e5d80ba6188e16d89e547654435316ffe93eb6029d55222d116cec6a5074060f85d3b937d12e9699cd7849851147f8da0e9b995a8f8591fed84e3f5d"
    }
]
```

# Deployment:

```shell script
(etch_escrow_contract) bash-3.2$ ./contract_cli.py deploy escrow.etch WzXAme8fB7wpxXFAfvTpDgCQEVZjZcHt3UMnrP9t8vFUK3DN3 "abcd" --transfers EytD7XFBDdw9J2KdaAmnpWKTwC6meKrFsCmzf1VZPV6vGSSWn,1 2s83Wma33nDUdfqRRoBjNXBN3RxXH7B45Zw55WNhgus2YECjh1,1
Arguments = Namespace(contract_deployment_nonce='abcd', contract_file='escrow.etch', contract_owner_address='WzXAme8fB7wpxXFAfvTpDgCQEVZjZcHt3UMnrP9t8vFUK3DN3', fee=600000, func=<function deploy_contract_local at 0x104a439e0>, hostname='127.0.0.1', network=None, port=8000, transfers=['EytD7XFBDdw9J2KdaAmnpWKTwC6meKrFsCmzf1VZPV6vGSSWn,1', '2s83Wma33nDUdfqRRoBjNXBN3RxXH7B45Zw55WNhgus2YECjh1,1'])
=======================
WARNING:root:Etch parsing failed, shard masks will be set to wildcard
WARNING:root:No terminal defined for '(' at line 70 col 30

        if (buyerOk.get() && (!sellerOk.get()) && (context.block().bl
                             ^

Expecting: {'STRING_LITERAL', 'FLOAT_TYPE', 'BASIC_TYPE', 'NAME', 'NUMBER', 'PRE_UNARY', 'FIXED_TYPE'}

contract source code:
persistent deposited_balance : UInt64;
persistent buyer  : Address;
persistent seller : Address;
persistent escrow : Address;
persistent start : UInt64;
persistent buyerOk : Bool;
persistent sellerOk: Bool;
persistent settledSinceBlock: UInt64;


@init
function init(owner: Address)
    use deposited_balance;
    use buyer;
    use seller;
    use escrow;
    use start;
    use buyerOk;
    use sellerOk;
    use settledSinceBlock;

    var context = getContext();
    var tx: Transaction = context.transaction();
    var transfers: Array<Transfer> = tx.transfers();
    assert(transfers.count() == 2i32, "There must be 2 native transfers defined in the transaction.");

    deposited_balance.set(0u64);
    escrow.set(owner);
    seller.set(transfers[0].to());
    buyer.set(transfers[1].to());
    //NOTE: Suggested check
    //assert((buyer.get() != owner) && (seller.get() != owner) && (buyer.get() != seller.get()), "Owner, buyer and seller must be mutually different.");

    start.set(context.block().blockNumber());
    buyerOk.set(false);
    sellerOk.set(false);
    settledSinceBlock.set(18446744073709551615u64);
endfunction


@action
function accept()
    verifyIsActive();

    use buyer;
    use seller;
    use start;
    use buyerOk;
    use sellerOk;

    var context = getContext();
    var tx: Transaction = context.transaction();
    var from = tx.from();

    if (from == buyer.get())
        buyerOk.set(true);
    else
        if (from == seller.get())
            sellerOk.set(true);
        endif
    endif

    if (buyerOk.get() && sellerOk.get())
        payBalance();
    else
        var releaseTimeout = 259200u64; // 259200[block/30xDay] = 30[Day]*24[h/Day]*60[m/h]*60[s/m] / 10[s/block]
        var expirationBlock = start.get() + releaseTimeout;

        // Freeze 30 days before release to buyer. The customer has to remember to call this method after freeze period.
        if (buyerOk.get() && (!sellerOk.get()) && (context.block().blockNumber() > expirationBlock))
            selfdestruct();
        endif
    endif
endfunction


@action
function deposit()
    verifyIsActive();

    use deposited_balance;
    use buyer;

    var context = getContext();
    var tx: Transaction = context.transaction();
    var transfers: Array<Transfer> = tx.transfers();

    assert(transfers.count() == 1i32, "There must be 1 native transfers defined in the transaction.");
    assert(transfers[0].to() == tx.contractAddress(), "Transfer destination address must be contract address.");
    assert(tx.from() == buyer.get(), "Deposit must be done from buyer address.");

    deposited_balance.set(deposited_balance.get() + transfers[0].amount());
endfunction


@action
function cancel()
    verifyIsActive();

    use buyer;
    use seller;
    use buyerOk;
    use sellerOk;

    var context = getContext();
    var tx: Transaction = context.transaction();
    var from = tx.from();

    if (from == buyer.get())
        buyerOk.set(false);
    else
        if (from == seller.get())
            sellerOk.set(false);
        endif
    endif

    // if both buyer and seller would like to cancel, money is returned to buyer
    if ((!buyerOk.get()) && (!sellerOk.get()))
        selfdestruct();
    endif
endfunction


@action
function kill()
    authoriseTx();
    verifyIsActive();

    selfdestruct();
endfunction


@action
function withdrawExcessBalance()
    use deposited_balance;
    use escrow;

    authoriseTx();

    var contract_balance = balance();
    var bonded_balance = deposited_balance.get();
    assert(contract_balance >= bonded_balance, "INCONSISTENCY: Insufficient contract deposited_balance.");

    transfer(escrow.get(), contract_balance - bonded_balance);
endfunction


@query
function deposited_balance() : UInt64
    use deposited_balance;
    return deposited_balance.get();
endfunction


@query
function status() : StructuredData
    use deposited_balance;
    use buyer;
    use seller;
    use escrow;
    use start;
    use buyerOk;
    use sellerOk;
    use settledSinceBlock;

    var status = StructuredData();
    status.set("deposited_balance", deposited_balance.get());
    status.set("buyer", buyer.get());
    status.set("seller", seller.get());
    status.set("escrow", escrow.get());
    status.set("start", start.get());
    status.set("buyerOk", toString(buyerOk.get()));
    status.set("sellerOk", toString(sellerOk.get()));
    status.set("settledSinceBlock", settledSinceBlock.get());

    return status;
endfunction



// ******   Private functions   *************************

function payBalance()
    // we are sending ourselves (contract creator) a fee
    use deposited_balance;
    use seller;
    use escrow;

    var fee = deposited_balance.get() / 100u64;
    var amountPayable = deposited_balance.get() - fee;

    transfer(escrow.get(), fee);
    transfer(seller.get(), amountPayable);
    deposited_balance.set(0u64);

    selfdestruct();
endfunction

function selfdestruct()
    use deposited_balance;
    use buyer;
    use settledSinceBlock;

    if (deposited_balance.get() > 0u64)
        transfer(buyer.get(), deposited_balance.get());
        deposited_balance.set(0u64);
    endif

    settledSinceBlock.set(getContext().block().blockNumber());
endfunction

function isActive() : Bool
    use settledSinceBlock;
    return (getContext().block().blockNumber() < settledSinceBlock.get());
endfunction

function verifyIsActive()
    assert(isActive(), "Contract has been settled and is no more active.");
endfunction

function authoriseTx() : Transaction
    use escrow;
    var tx: Transaction = getContext().transaction();
    assert(tx.from() == escrow.get(), "Tx sender must be owner address of the contract.");
    return tx;
endfunction



owner address: WzXAme8fB7wpxXFAfvTpDgCQEVZjZcHt3UMnrP9t8vFUK3DN3
nonce: YWJjZA==
contract address: 2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3
contract source code digest: d0f95670ff06019a1c2fb7ca1a259f69243476866c9c55a2f3337bb3d9d72700


Are contract deployment data above correct? [y/N]y
Transfers:
Dest. address {EytD7XFBDdw9J2KdaAmnpWKTwC6meKrFsCmzf1VZPV6vGSSWn}: amount=1 [Canonical FET]
Dest. address {2s83Wma33nDUdfqRRoBjNXBN3RxXH7B45Zw55WNhgus2YECjh1}: amount=1 [Canonical FET]


Are transfers correct? [y/N]: y
Private key for signee (hex or base64):
Added new signatory[0] with address WzXAme8fB7wpxXFAfvTpDgCQEVZjZcHt3UMnrP9t8vFUK3DN3

Continue with next key? [y/N]:
WARNING:root:Defaulting to wildcard shard mask as none supplied
Cost of creation: -11752 TOK
Contract has been successfully deployed.
=======================
(etch_escrow_contract) bash-3.2$
```

# Query contract Status structure:
```shell script
(etch_escrow_contract) bash-3.2$ ./contract_cli.py query 2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3 status
Arguments = Namespace(contract_address='2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3', func=<function query_contract_status at 0x10d9dc290>, hostname='127.0.0.1', network=None, port=8000)
=======================
Contract status of the contract at the {2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3} address: ContractStatus(buyer=2s83Wma33nDUdfqRRoBjNXBN3RxXH7B45Zw55WNhgus2YECjh1, seller=EytD7XFBDdw9J2KdaAmnpWKTwC6meKrFsCmzf1VZPV6vGSSWn, escrow=WzXAme8fB7wpxXFAfvTpDgCQEVZjZcHt3UMnrP9t8vFUK3DN3, balance=0, start=1879, settledSinceBlock=-1, sellerOk=False, buyerOK=False)
=======================
(etch_escrow_contract) bash-3.2$
```

# Query contract deposited balance:
```shell script
(etch_escrow_contract) bash-3.2$ ./contract_cli.py query 2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3 balance
Arguments = Namespace(contract_address='2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3', func=<function query_deposited_balance at 0x1020fa320>, hostname='127.0.0.1', network=None, port=8000)
=======================
Deposited balance of the contract: 0 [Canonical FET]
=======================
(etch_escrow_contract) bash-3.2$
```


# Execute `Deposit`
```shell script
(etch_escrow_contract) bash-3.2$ ./contract_cli.py action 2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3 2s83Wma33nDUdfqRRoBjNXBN3RxXH7B45Zw55WNhgus2YECjh1 deposit 1000
Arguments = Namespace(amount=1000, contract_address='2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3', fee=10000, from_address='2s83Wma33nDUdfqRRoBjNXBN3RxXH7B45Zw55WNhgus2YECjh1', func=<function action_deposit at 0x10e4d73b0>, hostname='127.0.0.1', network=None, port=8000)
=======================
Private key for signee (hex or base64):
Added new signatory[0] with address 2s83Wma33nDUdfqRRoBjNXBN3RxXH7B45Zw55WNhgus2YECjh1

Continue with next key? [y/N]:
WARNING:root:Defaulting to wildcard shard mask as none supplied
Cost of migration action Tx: -1017 TOK
Deposit has been successful
=======================
(etch_escrow_contract) bash-3.2$
```
```shell script
(etch_escrow_contract) bash-3.2$ ./contract_cli.py query 2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3 balance
Arguments = Namespace(contract_address='2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3', func=<function query_deposited_balance at 0x104e37320>, hostname='127.0.0.1', network=None, port=8000)
=======================
Deposited balance of the contract: 1000 [Canonical FET]
=======================
(etch_escrow_contract) bash-3.2$
```

# Execute `Accept`
```shell script
(etch_escrow_contract) bash-3.2$ ./contract_cli.py action 2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3 2s83Wma33nDUdfqRRoBjNXBN3RxXH7B45Zw55WNhgus2YECjh1 accept
Arguments = Namespace(contract_address='2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3', fee=10000, from_address='2s83Wma33nDUdfqRRoBjNXBN3RxXH7B45Zw55WNhgus2YECjh1', func=<function action_accept at 0x10a74e440>, hostname='127.0.0.1', network=None, port=8000)
=======================
Private key for signee (hex or base64):
Added new signatory[0] with address 2s83Wma33nDUdfqRRoBjNXBN3RxXH7B45Zw55WNhgus2YECjh1

Continue with next key? [y/N]:
WARNING:root:Defaulting to wildcard shard mask as none supplied
Cost of migration action Tx: -2 TOK
Accept action has been successful
=======================
(etch_escrow_contract) bash-3.2$
```
```shell script
(etch_escrow_contract) bash-3.2$ ./contract_cli.py query 2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3 status
Arguments = Namespace(contract_address='2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3', func=<function query_contract_status at 0x10a9ac290>, hostname='127.0.0.1', network=None, port=8000)
=======================
Contract status of the contract at the {2Rp79gG72XNMisi5ZeUxyt4xwGZtCbETG2otMQfrv88tnNzDf3} address: ContractStatus(buyer=2s83Wma33nDUdfqRRoBjNXBN3RxXH7B45Zw55WNhgus2YECjh1, seller=EytD7XFBDdw9J2KdaAmnpWKTwC6meKrFsCmzf1VZPV6vGSSWn, escrow=WzXAme8fB7wpxXFAfvTpDgCQEVZjZcHt3UMnrP9t8vFUK3DN3, balance=0, start=1879, settledSinceBlock=-1, sellerOk=False, buyerOK=False)
=======================
(etch_escrow_contract) bash-3.2$
```
