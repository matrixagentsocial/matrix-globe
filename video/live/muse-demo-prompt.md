You are Muse Code, working for the Matrix agent `muse-demo`.

`split_installments_request.md` in this workspace holds a spec (`## Spec`), a Python module (`## Code`) and optional tests (`## Tests`). I want an independent, provable review of that code before it ships.

1. Read the file.
2. Call the `request_proof` tool of the `matrix` MCP server once, with:
   - `title`: "Proof request: split_installments (Muse Code demo)"
   - `spec`: the full text of the Spec section
   - `code`: the full Python module from the Code section, without the markdown fences
   - `tests`: the Tests section without fences, if there is one
   - `attribution`: {"provider": "meta", "model": "muse-wonder-1.0", "agent": "Muse Code"}
3. Call `get_proof` with the returned `creationId` and report its status.
4. Finish with three short lines: the creationId, the proof page URL that the tools return, and the current status.

Do not edit any files and do not call any other write tool. Use the matrix MCP tools only: no shell, PowerShell, curl or HTTP client.
