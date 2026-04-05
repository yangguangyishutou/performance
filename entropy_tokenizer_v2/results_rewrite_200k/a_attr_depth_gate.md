# A2 attribute depth gate

## depth2
- enumerated (name, base_depth, occ): [('b', 1, 1), ('token_name', 2, 1)]

## depth3
- enumerated (name, base_depth, occ): [('b', 1, 1), ('c', 2, 1), ('token_name', 3, 1)]

## depth4
- enumerated (name, base_depth, occ): [('b', 1, 1), ('c', 2, 1), ('d', 3, 1), ('token_name', 4, 1)]

## depth5
- enumerated (name, base_depth, occ): [('b', 1, 1), ('c', 2, 1), ('d', 3, 1), ('e', 4, 1), ('token_name', 5, 1)]

## collect on S5 with max_attr_depth=2
- attribute candidates: []

## collect on S5 with max_attr_depth=3
- attribute candidates: []

## collect on S5 with max_attr_depth=4
- attribute candidates: []

## collect on S5 with max_attr_depth=5
- attribute candidates: ['token_name']

## collect on S5 with max_attr_depth=6
- attribute candidates: ['token_name']


> 注：`a.b.c.d.e.token_name` 的值链 `base_depth` 为 6（默认 `max_attr_depth=3` 会丢弃该属性后缀）。
