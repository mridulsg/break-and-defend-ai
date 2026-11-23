# Safety and authorized use

The full safety notes live in the course text: [docs/safety.md](docs/safety.md).

The short version:

- Use these techniques **only** on the lab targets, or on systems you own or have written permission to test.
- The labs are vulnerable by design. Keep them on localhost and do not reuse their code in production.
- Your provider API key stays inside the gateway container, and a spend cap limits cost.
- Never commit `.env`. Set a credit limit on the OpenRouter key you use here.

To report a flaw in the lab infrastructure (not the intentional lab vulnerabilities), open an issue marked `security`.
