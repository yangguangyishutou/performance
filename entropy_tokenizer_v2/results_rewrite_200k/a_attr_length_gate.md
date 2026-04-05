# A1 attribute length gate
Sample uses attrs: config(6), headers(7), profile(7), configuration(13)

> 注：`min_identifier_chars=8` 时仍只会留下 `configuration`，`headers`/`profile` 需阈值≤7。

## min_identifier_chars=10
- n_candidates_total: 1
- attribute_literals: ['configuration']

## min_identifier_chars=8
- n_candidates_total: 1
- attribute_literals: ['configuration']

## min_identifier_chars=6
- n_candidates_total: 4
- attribute_literals: ['config', 'configuration', 'headers', 'profile']

