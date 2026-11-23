# Tests

Three layers. Run them before you publish a change.

| Layer | What it covers | Command | Needs |
|---|---|---|---|
| **Unit and static** | The gateway logic (auth, cap, clamping, metering, streaming, privacy), the lab checker and RAG helpers, and rules for the whole repo: hardened compose files, pinned images, hashed dependencies, valid docs links, no leaked secrets or flags | `./tests/run-unit.sh` | Docker only. Runs with no network, a read-only repo and no capabilities. |
| **Integration** | The live stack: exposure, container hardening, lab network isolation, secret handling, spend-ledger persistence, script behaviour, cleanup scoping, the docs build and both labs end to end | `./tests/integration/run.sh` | Gateway and docs site running, local model server reachable |
| **Cold start** | What happens after WSL idles or restarts | See `tests/cold-start.md` | Windows with WSL |

The integration run costs under a hundredth of a cent. It never prints a secret.

When a test fails, fix the product, not the test, unless the test is wrong.
