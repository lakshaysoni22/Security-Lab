// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TransactionTracer {

    struct TransactionData {
        address sender;
        address receiver;
        uint amount;
        uint timestamp;
    }

    TransactionData[] public transactions;

    function logTransaction(address _receiver, uint _amount) public {
        transactions.push(TransactionData(
            msg.sender,
            _receiver,
            _amount,
            block.timestamp
        ));
    }

    function getTransaction(uint index) public view returns (
        address, address, uint, uint
    ) {
        TransactionData memory t = transactions[index];
        return (t.sender, t.receiver, t.amount, t.timestamp);
    }
}
