# Rewrite Stage3 AB example ledger
## 1. a_rewrite — `smoke:a_success`
### before
```text
def f():
    very_long_identifier_for_tokenizer_alias_demo_case = 1
    return very_long_identifier_for_tokenizer_alias_
```
### after
```text
def f():
    a = 1
    return a + a

```
- payload: `{'assignments': [{'field': 'variable', 'literal': 'very_long_identifier_for_tokenizer_alias_demo_case', 'alias': 'a'}], 'net': 9}`
## 2. b_cluster — `smoke:b_cluster`
### before
```text
msg_a = "this_is_a_shared_literal_token_sink_abc"
msg_b = "this_is_a_shared_literal_token_sink_abc"
msg_c = "this_is_a_shared_literal_token_sink_abc"
```
### after
```text
_BREF0 = 'this_is_a_shared_literal_token_sink_abc'

msg_a = _BREF0
msg_b = _BREF0
msg_c = _BREF0

```
- payload: `{'refs': [{'symbol': '_BREF0', 'representative': '"this_is_a_shared_literal_token_sink_abc"', 'net_true': 33}], 'net': 33}`
## 3. routing — `smoke:route`
- reason: short_comment_delete_plus_docstring_retained
### before
```text
# x
def g():
    """routing_case_docstring_asset"""
    return 1

```
### after
```text

def g():
    """routing_case_docstring_asset"""
    return 1

```
- payload: `{'events': 10}`
