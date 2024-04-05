bitcoin transaction的思考
============

## 1、交易
交易（Transaction，简称 Tx）是比特币系统的重要组成部分。块（Block）就是将这些基础单元打包装箱，并链在一起。巨大算力保障了块的安全，也就保障了单个交易的安全。

[tx协议](https://en.bitcoin.it/wiki/Protocol_documentation#tx)

交易的transaction协议中包含了 `tx_in[]`和`tx_out[]`数组，不是应该有一个固定的转账额度吗？其实不然，这是由bitcoin的交易属性决定的。普通银行转账可以从账户余额中剥离出想要转出的额度，通过将交易申请转给目标银行账户完成交易。bitcoin账户并不是地址绑定余额这么简单的关系，而是一个地址绑定若干个`未消费余额块`，每个余额块中的金额是随机的且不能被分割，均来自于先前其他地址的转入。准确的说，某个地址的余额就是该地址下`未消费余额块`的总和，而全网bitcoin的总量就是bitcoin网络中，所有`未消费余额块`的总和。

举例说明：
A有10个bitcoin，要转7个bitcoin给B；那么A可以发起一次交易，其中 `tx_in[]`中为10个bitcoin输入，`tx_out[]`包含两个输出，分别是3个bitcoin输出到A的地址和7个bitcoin输出到B的地址；（在不考虑手续费的前提下）

## 2、协议拆分及详解
给出一个bitcoint交易反序列化json的例子：
```
{
    "version": 1,
    "locktime": 0,
    "tx_in: [
        {
            "txid": "7957a35fe64f80d234d76d83a2a8f1a0d8149a41d81de548f0a65a8a999f6f18",
            "vout": 0,
            "scriptSig" : "3045022100884d142d86652a3f47ba4746ec719bbfbd040a570b1deccbb6498c75c4ae24cb02204b9f039ff08df09cbe9f6addac960298cad530a863ea8f53982c09db8f6e3813[ALL] 0484ecc0d46f1918b30928fa0e4ed99f16a0fb4fde0735e7ade8416ab9fe423cc5412336376789d172787ec3457eee41c04f4938de5cc17b4a10fa336a8d752adf",
            "sequence": 4294967295
        }
    ],
    "tx_out": [
        {
            "value": 0.01500000,
            "scriptPubKey": "OP_DUP OP_HASH160 ab68025513c3dbd2f7b92a94e0581f5d50f654e7 OP_EQUALVERIFY OP_CHECKSIG"
        },
        {
            "value": 0.08450000,
            "scriptPubKey": "OP_DUP OP_HASH160 7f9b1a7fb68d60c536c2fd8aeaa53a8f3cc025a8 OP_EQUALVERIFY OP_CHECKSIG",
        }
    ]
}
```
这里详细介绍下`scriptSig`和`scriptPubkey`，分别成为解锁脚本和锁定脚本；

#### 2.1、锁定脚本（scriptPubKey）：
- 锁定脚本是在交易输出（UTXO）中的一部分，用于锁定比特币资金
- 锁定脚本定义了接收者可以花费这笔资金的条件，通常包含了接收者的地址和一些条件逻辑
- 锁定脚本使用公钥哈希（P2PKH）或脚本哈希（P2SH）等形式来表示
- 例如，一个典型的锁定脚本可能是：
  ```
  OP_DUP OP_HASH160 <Recipient's Public Key Hash> OP_EQUALVERIFY OP_CHECKSIG
  ```
- 锁定脚本中的条件逻辑通常由发送者创建，用于指定接收者可以解锁资金的条件

#### 2.2、解锁脚本（scriptSig）：
- 解锁脚本是在交易输入中的一部分，用于提供解锁交易所需的签名和公钥
- 解锁脚本包含了发送者提供的签名和公钥，用于满足锁定脚本中的条件逻辑
- 解锁脚本的内容必须与锁定脚本中的条件逻辑相匹配，才能成功解锁资金
- 例如，一个典型的解锁脚本可以是：
  ```
  <Signature> <Public Key>
  ```
- 解锁脚本中的签名和公钥是发送者提供的数据，用于证明发送者有权花费这笔资金

##### 2.2.1、签名<Signature>生成规则及流程
参考 [比特币交易中的签名](https://aaron67.cc/2020/10/10/bitcoin-sign-transaction/)

总的来说，锁定脚本和解锁脚本之间的关系可以理解为锁和钥匙的关系。锁定脚本相当于锁，它定义了资金的使用条件；解锁脚本相当于钥匙，它提供了解锁资金所需的信息。在交易验证过程中，解锁脚本提供的信息必须能够成功解锁锁定脚本，才能有效花费资金。

关于解锁脚本和锁定脚本的图解说明可以参考：[有状态的 UTXO 和 OP_PUSH_TX 的技术原理](https://aaron67.cc/2022/03/06/bsv-stateful-utxo-and-op-push-tx/) `UTXO 模型`章节，这里不过多介绍  

##### 2.2.2、有状态的 UTXO
- 通常指锁定脚本中携带状态数据以及状态流转条件
  - 参考 [有状态的 UTXO 和 OP_PUSH_TX 的技术原理](https://aaron67.cc/2022/03/06/bsv-stateful-utxo-and-op-push-tx/) `“有状态”的 UTXO`章节
- 通常是使用`OP_RETURN`和`OP_DROP`组合使用的方式
  - `OP_RETURN`：用于向区块链添加数据而不影响交易的有效性，常用于存储元数据，放置于账本中
  - `OP_DROP`：用于从栈中弹出并丢弃一个元素，用于简化脚本操作
- 

#### 2.3、脚本运算
`scriptPubkey`中`OP_DUP`和`OP_HASH160`均属于操作码，对应于特定字节，可参考[脚本操作码](https://en.bitcoin.it/wiki/Script#Opcodes)

bitcoin的脚本运算是在栈上执行的，运算的过程在不同的网络节点进行（PC）等；先执行解锁脚本，然后执行锁定脚本：  

![script](https://github.com/jiuri-code/blockchain_playground/blob/main/picture/script.png)  

具体执行细节如下图所示：  

![process](https://github.com/jiuri-code/blockchain_playground/blob/main/picture/stack%20calculate.png)  

