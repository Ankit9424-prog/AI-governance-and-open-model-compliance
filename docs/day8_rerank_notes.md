# Day 8 – Reranking Notes

## Summary
Tested cross-encoder reranking on top of dense retrieval.

## Result
Reranking gave mixed results:
- helped some action-oriented NIST queries
- hurt some privacy-focused NIST queries
- did not clearly improve already-strong EU AI Act queries
- did not justify replacing dense retrieval as the default yet

## Conclusion
Dense retrieval remains the current baseline.
Reranking is promising but unstable for this corpus and query set.

## Next Step
Add a small manual evaluation set and score dense retrieval systematically.