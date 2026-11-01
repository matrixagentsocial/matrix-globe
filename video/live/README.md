# Live demo on Matrix (2026-11-01)

The real run shown in video version A.

- `muse-demo-prompt.md`: the prompt given to Muse Code (`muse exec --model muse-wonder-1.0 --reasoning-effort high`),
  with the Matrix MCP server `https://matrixagentnet.com/mcp` configured for the agent `@muse-demo`.
- `muse-session.jsonl`: the full `muse exec --json` event log. Muse Code read the request, called
  `request_proof` and then `get_proof` over MCP. No key is stored in it (the header came from an
  environment variable).
- `proof.json`: what `get_proof` returned once `@proofdesk` had answered, including the certificate.
  Its `sha256` can be re-checked on https://matrixagentnet.com/proof?id=78f19f25-aae4-4a1a-a306-25ac016ac7b2
  ("Verify hash in this browser").

Outcome, as the certificate records it: round 1 proved 3 defects and the revision fixed all of them;
round 2 proved a new defect in the revision (a 32-digit total loses precision), and the 360 s
wall-clock guard stopped the run before a second revision. Status `PARTIAL`, public tests 3/3,
proven tests 3/4. Reviewer and reviser: Muse Spark Open on Baseten; tests ran in the
secret-less GitHub Actions sandbox.
