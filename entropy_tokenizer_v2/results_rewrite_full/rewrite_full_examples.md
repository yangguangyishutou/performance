# Rewrite full eval snapshots

{
  "source_id": "hand_a",
  "before": "def f():\n    very_long_identifier_for_tokenizer_alias_demo_case = 1\n    return very_long_identifier_for_tokenizer_alias_demo_case + very_long_identifier_for_tokenizer_alias_demo_case\n",
  "after": "def f():\n    a = 1\n    return a + a\n"
}
{
  "source_id": "hand_b",
  "before": "\nmsg_a = \"this_is_a_shared_literal_token_sink_abc\"\nmsg_b = \"this_is_a_shared_literal_token_sink_abc\"\nmsg_c = \"this_is_a_shared_literal_token_sink_abc\"\n",
  "after": "_BREF0 = 'this_is_a_shared_literal_token_sink_abc'\n\nmsg_a = _BREF0\nmsg_b = _BREF0\nmsg_c = _BREF0\n"
}
{
  "source_id": "hand_route",
  "before": "# x\ndef g():\n    \"\"\"routing_case_docstring_asset\"\"\"\n    return 1\n",
  "after": "\ndef g():\n    \"\"\"routing_case_docstring_asset\"\"\"\n    return 1\n"
}