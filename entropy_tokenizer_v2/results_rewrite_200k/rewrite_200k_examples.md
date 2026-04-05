# rewrite_200k examples (ledger-backed snapshots)
## A success
```json
null
```
## A reject
```json
{
  "source_id": "frozen:21",
  "reasons": {
    "no_net_true_gain": 1
  },
  "snippet": "import FWCore.ParameterSet.Config as cms\nfindTtSemiLepJetCombMaxSumPtWMass = cms.EDProducer(\"TtSemiLepJetCombMaxSumPtWMass\",\njets  = cms.InputTag(\"selectedPatJets\"),\nleps  = cms.InputTag(\"selectedPatMuons\"),\nmaxNJets  = cms.int32(4),\nwMass    = cms.double(80.4),\nuseBTagging = cms.bool(False),\nbTagAlgorithm = cms.string(\"trackCountingHighEffBJetTags\"),\nminBDiscBJets     = cms.double(1.0),\nmaxBDiscL"
}
```
## B success
```json
{
  "source_id": "frozen:21",
  "before_b": "_b2 = 'trackCountingHighEffBJetTags'\n_b1 = 'selectedPatJets'\n_b0 = 'TtSemiLepJetCombMaxSumPtWMass'\nimport FWCore.ParameterSet.Config as cms\nfindTtSemiLepJetCombMaxSumPtWMass = cms.EDProducer(_b0,\njets  = cms.InputTag(\"selectedPatJets\"),\nleps  = cms.InputTag(\"selectedPatMuons\"),\nmaxNJets  = cms.int32(4),\nwMass    = cms.double(80.4),\nuseBTagging = cms.bool(False),\nbTagAlgorithm = cms.string(\"trackCountingHighEffBJetTags\"),\nminBDiscBJets     = cms.double(1.0),\nmaxBDiscLightJets = cms.double(3.0)\n)",
  "refs": [
    {
      "symbol": "_b0",
      "representative": "\"TtSemiLepJetCombMaxSumPtWMass\"",
      "net_true": 6,
      "intro_tokens_true": 18,
      "raw_total_true": 28,
      "ref_total_true": 22,
      "representative_token_len_true": 14,
      "cluster_path": "standard_hdbscan_or_lexical",
      "fallback_reason": ""
    },
    {
      "symbol": "_b1",
      "representative": "\"selectedPatJets\"",
      "net_true": 6,
      "intro_tokens_true": 8,
      "raw_total_true": 22,
      "ref_total_true": 16,
      "representative_token_len_true": 5,
      "cluster_path": "standard_hdbscan_or_lexical",
      "fallback_reason": ""
    },
    {
      "symbol": "_b2",
      "representative": "\"trackCountingHighEffBJetTags\"",
      "net_true": 3,
      "intro_tokens_true": 13,
      "raw_total_true": 20,
      "ref_total_true": 17,
      "representative_token_len_true": 10,
      "cluster_path": "standard_hdbscan_or_lexical",
      "fallback_reason": ""
    }
  ],
  "b_net": 15
}
```
## B reject
```json
{
  "source_id": "frozen:30",
  "reasons": {
    "rejected_for_low_quality": 1
  }
}
```
## Route
```json
{
  "source_id": "frozen:8",
  "route_summary_initial": {
    "total_route_delete_now": 0,
    "total_route_retain_for_b": 1,
    "total_route_retain_as_reference_candidate": 0,
    "total_route_pass_through": 0,
    "total_route_clean_after_b": 0,
    "total_docstrings_detected": 0,
    "total_comments_detected": 1
  },
  "snippet": "<reponame>tashidexiaoL/splashnew\n# -*- coding: utf-8 -*-\nimport os\nimport json\nfrom splash import defaults\nfrom splash.utils import to_bytes, path_join_secure\nfrom splash.errors import BadOption\nclass RenderOptions(object):\n\"\"\"\nOptions that control how to render a response.\n\"\"\"\n    _REQUIRED = object()\n    def __init__(self, data, max_timeout):\n        self.data = data\nself.max_timeout = max_timeo"
}
```
