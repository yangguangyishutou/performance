# A3 string_exact_path

## allow=False mismatch_expected_occ=False
- probe: {'allow_string_exact_path': False, 'regex_ok': True, 'occurrences_in_text': 1, 'expected_occ': 1, 'occ_matches_expected': True, 'would_enter_candidates': False}
- candidate fields: []

## allow=False mismatch_expected_occ=True
- probe: {'allow_string_exact_path': False, 'regex_ok': True, 'occurrences_in_text': 1, 'expected_occ': 99, 'occ_matches_expected': False, 'would_enter_candidates': False}
- candidate fields: []

## allow=True mismatch_expected_occ=False
- probe: {'allow_string_exact_path': True, 'regex_ok': True, 'occurrences_in_text': 1, 'expected_occ': 1, 'occ_matches_expected': True, 'would_enter_candidates': True}
- candidate fields: ['string_exact_path']

## allow=True mismatch_expected_occ=True
- probe: {'allow_string_exact_path': True, 'regex_ok': True, 'occurrences_in_text': 1, 'expected_occ': 99, 'occ_matches_expected': False, 'would_enter_candidates': False}
- candidate fields: []

