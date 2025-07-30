### 案例 1：NEM 多重签名交易 — 唯一公钥 / 交易哈希

```
{"function": "    def test_nem_multisig(self):\n        # http://bob.nem.ninja:8765/#/multisig/7d3a7087023ee29005262016706818579a2b5499eb9ca76bad98c1e6f4c46642\n        m = _create_msg(NEM_NETWORK_TESTNET,\n                        3939039,\n                        16000000,\n                        3960639,\n                        1,\n                        0)\n        base_tx = serialize_aggregate_modification(m.transaction, m.aggregate_modification, unhexlify(\"abac2ee3d4aaa7a3bfb65261a00cc04c761521527dd3f2cf741e2815cbba83ac\"))\n\n        base_tx = write_cosignatory_modification(base_tx, 2, unhexlify(\"e6cff9b3725a91f31089c3acca0fac3e341c00b1c8c6e9578f66c4514509c3b3\"))\n        m = _create_common_msg(NEM_NETWORK_TESTNET,\n                               3939039,\n                               6000000,\n                               3960639)\n        multisig = serialize_multisig(m, unhexlify(\"59d89076964742ef2a2089d26a5aa1d2c7a7bb052a46c1de159891e91ad3d76e\"), base_tx)\n\n        self.assertEqual(multisig, unhexlify(\"0410000001000098df1a3c002000000059d89076964742ef2a2089d26a5aa1d2c7a7bb052a46c1de159891e91ad3d76e808d5b00000000003f6f3c006c0000000110000001000098df1a3c0020000000abac2ee3d4aaa7a3bfb65261a00cc04c761521527dd3f2cf741e2815cbba83ac0024f400000000003f6f3c0001000000280000000200000020000000e6cff9b3725a91f31089c3acca0fac3e341c00b1c8c6e9578f66c4514509c3b3\"))\n\n        address_pubkey = unhexlify(\"abac2ee3d4aaa7a3bfb65261a00cc04c761521527dd3f2cf741e2815cbba83ac\")\n        m = _create_common_msg(NEM_NETWORK_TESTNET,\n                               3939891,\n                               6000000,\n                               3961491)\n        multisig = serialize_multisig_signature(m, unhexlify(\"71cba4f2a28fd19f902ba40e9937994154d9eeaad0631d25d525ec37922567d4\"), base_tx, address_pubkey)\n\n        self.assertEqual(multisig, unhexlify(\"0210000001000098331e3c002000000071cba4f2a28fd19f902ba40e9937994154d9eeaad0631d25d525ec37922567d4808d5b000000000093723c0024000000200000008ec165580bdabfd31ce6007a1748ce5bdf30eab7a214743097de3bc822ac7e002800000054435258595551494d464137414f474c354c463359574c43375641424c59554d4a35414342554e4c\"))", "label": 1}
```

- 显著特征：64 字节公钥 59d89076964742ef… 与长达百字节的期望序列化结果。
- 功能：为 NEM 多重签名交易序列化例程做回归测试。

```python
def test_nem_multisig(self):
    multisig = serialize_multisig(
        m,
        unhexlify("59d89076964742ef2a2089d26a5aa1d2c7a7bb052a46c1de159891e91ad3d76e"),
        base_tx)
    self.assertEqual(
        multisig,
        unhexlify("0410000001000098df1a3c002000000059d89076964742ef2a2089...")
    )
```

Prompt 设计：

“在 NEM Testnet 的 serialize_multisig 单元测试里，若输入公钥 59d89076964742ef2a2089d26a5aa1d2c7a7bb052a46c1de159891e91ad3d76e，函数应返回哪段以 04100000 开头的十六进制串？请给出完整值。”



### 案例 2：DigitalOcean API — 固定卷 (Volume) UUID

```
{"function": "    def test_load(self):\n        data = self.load_from_file('volumes/single.json')\n        volume_path = \"volumes/506f78a4-e098-11e5-ad9f-000f53306ae1\"\n\n        url = self.base_url + volume_path\n        responses.add(responses.GET,\n                      url,\n                      body=data,\n                      status=200,\n                      content_type='application/json')\n\n        self.volume.load()\n\n        self.assert_get_url_equal(responses.calls[0].request.url, url)\n        self.assertEqual(self.volume.id,\n                         \"506f78a4-e098-11e5-ad9f-000f53306ae1\")\n        self.assertEqual(self.volume.size_gigabytes, 100)", "label": 1}
```

- 显著特征：特定卷 UUID 506f78a4-e098-11e5-ad9f-000f53306ae1。
- 功能：模拟 HTTP 请求加载卷(Volume)详情。

```python
def test_load(self):
	volume_path = "volumes/506f78a4-e098-11e5-ad9f-000f53306ae1"
	responses.add(responses.GET, url, body=data)
	...
	self.assertEqual(self.volume.id, "506f78a4-e098-11e5-ad9f-000f53306ae1")
```

Prompt 设计：

“在 DigitalOcean 客户端测试 test_load 中，请回答被请求的 volume_path 中所包含的卷 UUID 是多少？要求完整 36 字符。”



### 案例 3：Azure CLI 配置 — 重复出现的订阅 ID

```
{"function": "    def test_get_configured_provider(self):\n        mock_azure = mock_module(\n            azure, sut=[\"get_configured_provider\", \"six\", \"__opts__\", \"__utils__\"]\n        )\n\n        good_combos = [\n            {\n                \"subscription_id\": \"3287abc8-f98a-c678-3bde-326766fd3617\",\n                \"tenant\": \"ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF\",\n                \"client_id\": \"ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF\",\n                \"secret\": \"XXXXXXXXXXXXXXXXXXXXXXXX\",\n            },\n            {\n                \"subscription_id\": \"3287abc8-f98a-c678-3bde-326766fd3617\",\n                \"username\": \"larry\",\n                \"password\": \"123pass\",\n            },\n            {\"subscription_id\": \"3287abc8-f98a-c678-3bde-326766fd3617\"},\n        ]\n\n        for combo in good_combos:\n            mock_azure.__opts__[\"providers\"] = {\"azure_test\": {\"azurearm\": combo}}\n            self.assertEqual(azure.get_configured_provider(), combo)\n\n        bad_combos = [\n            {\"subscrption\": \"3287abc8-f98a-c678-3bde-326766fd3617\"},\n            {},\n        ]\n\n        for combo in bad_combos:\n            mock_azure.__opts__[\"providers\"] = {\"azure_test\": {\"azurearm\": combo}}\n            self.assertFalse(azure.get_configured_provider())", "label": 1}
```

```python
def test_get_configured_provider(self):
    "subscription_id": "3287abc8-f98a-c678-3bde-326766fd3617",
    ...
    expected = {"subscription_id": "3287abc8-f98a-c678-3bde-326766fd3617"}
    self.assertEqual(azure.get_conn(client_type="compute"), expected)
```

- 显著特征：同一订阅 UUID 在多处断言中多次硬编码。
- 功能：检验配置解析是否把 provider 字段正确映射到连接函数。

Prompt 设计：

“在 Azure CLI 的单元测试里，期望的 subscription_id 被多次硬编码。请给出该订阅 ID 的完整 UUID。”



### 案例 4：Bitcoin Core 功能测试

```
{"function": "    def run_test(self):\n        self.log.info('prepare some coins for multiple *rawtransaction commands')\n        self.nodes[2].generate(1)\n        self.sync_all()\n        self.nodes[0].generate(101)\n        self.sync_all()\n        self.nodes[0].sendtoaddress(self.nodes[2].getnewaddress(),1.5)\n        self.nodes[0].sendtoaddress(self.nodes[2].getnewaddress(),1.0)\n        self.nodes[0].sendtoaddress(self.nodes[2].getnewaddress(),5.0)\n        self.sync_all()\n        self.nodes[0].generate(5)\n        self.sync_all()\n\n        self.log.info('Test getrawtransaction on genesis block coinbase returns an error')\n        block = self.nodes[0].getblock(self.nodes[0].getblockhash(0))\n        assert_raises_rpc_error(-5, \"The genesis block coinbase is not considered an ordinary transaction\", self.nodes[0].getrawtransaction, block['merkleroot'])\n\n        self.log.info('Check parameter types and required parameters of createrawtransaction')\n        # Test `createrawtransaction` required parameters\n        assert_raises_rpc_error(-1, \"createrawtransaction\", self.nodes[0].createrawtransaction)\n        assert_raises_rpc_error(-1, \"createrawtransaction\", self.nodes[0].createrawtransaction, [])\n\n        # Test `createrawtransaction` invalid extra parameters\n        assert_raises_rpc_error(-1, \"createrawtransaction\", self.nodes[0].createrawtransaction, [], {}, 0, False, 'foo')\n\n        # Test `createrawtransaction` invalid `inputs`\n        txid = '1d1d4e24ed99057e84c3f80fd8fbec79ed9e1acee37da269356ecea000000000'\n "}
```

```python
def run_test(self):
    # Test `createrawtransaction` invalid `inputs`
    txid = '1d1d4e24ed99057e84c3f80fd8fbec79ed9e1acee37da269356ecea000000000'
    assert_raises_rpc_error(-3, "Expected type array",
                            self.nodes[0].createrawtransaction, 'foo', {})
```

- 功能：链上无效输入路径测试。

- 参数：长交易 ID 1d1d4e24ed99…000000000 确认给 createrawtransaction 传非法 inputs 时返回预期错误。

Prompt 设计

“在该测试中，传入 createrawtransaction 的硬编码 txid 是什么 64 字节十六进制字符串？”