def test_subscribe(self):
    ···
    dg = Datagram.create([12345654321], 0, 1234)
    dg.add_uint32(0xDEADBEEF)
    self.c2.send(dg)


def run_test(self):
    ···
    # Bitcoin transaction validation test
    inputs = [{'txid': txid, 'vout': 1, 'sequence': 4294967296}]
    assert_raises_rpc_error(-8, 'Invalid parameter, sequence number is out of range', self.nodes[0].createrawtransaction, inputs, outputs)
    # Valid boundary case
    inputs = [{'txid': txid, 'vout': 1, 'sequence': 4294967294}]
    rawtx = self.nodes[0].createrawtransaction(inputs, outputs)

def c2s_bra(l, gcart):
    if l == 0:
        return gcart * 0.282094791773878143
    elif l == 1:
        return gcart * 0.488602511902919921


def testbanOK(self):
    ···
    ticket_str = 'FailTicket: ip=193.168.0.128 time=1167605999.0 bantime=None'
    ticket.setTime(1000002000.0)
    self.assertEqual(ticket.getTime(), 1000002000.0)