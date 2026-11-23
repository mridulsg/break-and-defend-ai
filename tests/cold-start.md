# Cold-start tests (manual, Windows with WSL)

These check what recovers by itself after WSL idles or restarts. Run them from PowerShell.
Last run: 2026-11-21.

## Scenario A: terminate the Ubuntu instance and start it again

```powershell
wsl --terminate <your WSL distro>
wsl -d <your WSL distro> -- bash -c 'docker ps --format "{{.Names}} {{.Status}}"'
```

**Result:** pass. The gateway and the docs site restart by themselves (`restart: unless-stopped`), the spend ledger is intact, and the local chat and embedding models answer through the gateway.

## Scenario B: full WSL shutdown

```powershell
wsl --shutdown
wsl -d <your WSL distro> -- bash -c 'docker ps --format "{{.Names}} {{.Status}}"'
```

**Result:** pass, same as scenario A. The Windows address as seen from WSL did not change, so the local model kept working.

## Scenario C: restart the local model server

The local models run in the `bdai-ollama` container (restart policy `unless-stopped`), and the gateway reaches it by name on the
`bdai-egress` network, so there is no host address to go stale.

```bash
docker restart bdai-ollama
docker exec bdai-ollama ollama list          # both models are still there (they live in the bdai-ollama-models volume)
```

**Expected:** the models are listed, and the gateway answers a `bdai-victim` call again within about a minute (the first answer
loads the model into memory).

If you use an Ollama installed on the host instead (`./shared/scripts/dev-gateway-up.sh`), a Windows reboot can change the address
WSL sees for Windows. Run `dev-gateway-up.sh` again to refresh it.
