
```python
def build_call_graph(method_call_path, method_nodes, log_file):
    for line in open(method_call_path, 'r'):
        caller, callee = parse_method_call(line)
        caller_key = match_method_signature(caller)
        callee_key = match_method_signature(callee)

        if caller_key and callee_key:
            method_nodes[caller_key].children.add(method_nodes[callee_key])
            method_nodes[callee_key].parents.add(method_nodes[caller_key])
```