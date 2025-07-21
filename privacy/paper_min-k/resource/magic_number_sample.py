# Extracted from positive.jsonl benchmark (tests/test_message_director.py)
# Unique magic number snippet used in the case study

dg = Datagram.create([12345654321], 0, 1234)
# 32-bit sentinel value
dg.add_uint32(0xDEADBEEF)
