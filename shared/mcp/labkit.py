"""The web console backend that every Course 2 lab shares: start the lab's MCP servers, connect a host to them, and serve the console.

A lab writes a small `console.py` that builds its servers and calls `Lab(...).run()`. This file supplies the rest:
  /api/config   what the page shows         /api/state    missions, evidence, flag      /api/ask      the assistant
  /api/servers  every server's tool list    /api/tester   send a raw request           /api/fixes    the lab's fixes switch
Run inside the lab's console container; open http://127.0.0.1:8300.
"""
import json
import os
import pathlib
import sys
import threading
import time

sys.path.insert(0, os.environ.get("BDAI_CONSOLE_DIR", "/console"))

import openai  # noqa: E402

import host as hostmod  # noqa: E402
import mcpmini  # noqa: E402
import server as web  # noqa: E402

DATA = pathlib.Path(os.environ.get("BDAI_DATA_DIR", "/data"))
STATIC = pathlib.Path(os.environ.get("BDAI_CONSOLE_DIR", "/console")) / "static"
MODELS = [{"id": "bdai-victim", "label": "Local model (Qwen3 1.7B, free)", "hosted": False},
          {"id": "bdai-default", "label": "Hosted model (Claude Haiku 5.5, about $0.001 a question)", "hosted": True}]
MAX_QUESTION = 1500
BREAKS = {"version": ("MCP-Protocol-Version", "2025-11-25"), "method": ("Mcp-Method", "tools/zap"), "origin": ("Origin", "http://evil.example")}


class Lab:
    def __init__(self, *, product, lab, intro, suggestions, missions, progress, servers, views=("chat", "servers", "tester", "missions"),
                 missions_lede="Each mission is detected automatically.", flag_next="", bot="Acme Assistant", persona="engineer",
                 trusted=None, policy_for=None, mint=None, viewer_token=None, watch=None, on_tester=None, extra_state=None, fixes=False, system=None):
        self.product, self.lab, self.intro, self.suggestions, self.missions = product, lab, intro, suggestions, missions
        self.progress, self.views, self.missions_lede, self.flag_next, self.bot, self.persona = progress, list(views), missions_lede, flag_next, bot, persona
        self.server_defs = servers                  # id -> (display name, McpServer)
        self.trusted = trusted or {}
        self.viewer_token = viewer_token            # optional fn(server id) -> token, for the page that lists tools when servers need auth
        self.mint = mint                            # None, or {"audiences": [...]} to show the token minting row
        self.policy_for = policy_for                # fn(fixes_on) -> hostmod.Policy
        self.watch, self.on_tester, self.extra_state, self.has_fixes, self.system = watch, on_tester, extra_state, fixes, system
        self.clients: dict[str, mcpmini.McpClient] = {}
        self.fixes_file = DATA / "fixes"
        self.httpds = []

    # ------------------------------------------------------------ setup
    def start_servers(self):
        for sid, (_, srv) in self.server_defs.items():
            httpd = srv.serve("127.0.0.1", 0)
            self.httpds.append(httpd)
            self.clients[sid] = mcpmini.McpClient(f"http://127.0.0.1:{httpd.server_address[1]}/mcp")

    def fixes_on(self) -> bool:
        return self.has_fixes and self.fixes_file.exists() and self.fixes_file.read_text().strip() == "on"

    def make_host(self) -> hostmod.Host:
        policy = self.policy_for(self.fixes_on()) if self.policy_for else None
        kw = {"system": self.system} if self.system else {}
        return hostmod.Host(self.clients, policy, **kw)

    # ------------------------------------------------------------ handlers
    def config(self, _b, _q) -> dict:
        return {
            "company": "Acme Outdoor Gear", "product": self.product, "lab": self.lab, "persona": self.persona, "bot": self.bot,
            "intro": self.intro, "chat_label": "Assistant chat", "secret": False, "fixes": self.has_fixes, "tools_tab": True, "suite": getattr(self, "suite_cfg", {}),
            "models": MODELS, "default_model": hostmod.DEFAULT_MODEL, "suggestions": self.suggestions,
            "max_question": MAX_QUESTION, "max_note": 0, "max_notes": 0, "views": self.views, "mint": self.mint,
            "feedback": {"lede": "", "doors": []}, "missions_lede": self.missions_lede, "missions": self.missions, "flag_next": self.flag_next,
        }

    def state(self, _b, _q) -> dict:
        prog = self.progress.load()
        done = self.progress.is_complete(prog)
        out = {"ready": True, "problem": None, "sources": {}, "notes": [],
               "missions": {**{m: m in prog for m in self.progress.MISSIONS}, "complete": done},
               "evidence": {m: prog[m] for m in self.progress.MISSIONS if m in prog},
               "flag": self.progress.FLAG if done else None, "fixes": self.fixes_on()}
        if self.extra_state:
            out.update(self.extra_state())
        return out

    def servers(self, _b, _q) -> dict:
        out = []
        for sid, (name, _) in self.server_defs.items():
            c = self.clients[sid]
            c.token = self.viewer_token(sid) if self.viewer_token else None
            try:
                d = c.discover()
                out.append({"id": sid, "name": name, "version": mcpmini.PROTOCOL_VERSION, "ttl_ms": d.get("ttlMs", 0), "instructions": d.get("instructions", ""),
                            "trusted": self.trusted.get(sid, True), "tools": c.list_tools()})
            except mcpmini.McpError as exc:
                out.append({"id": sid, "name": name, "error": f"{exc.code}: {exc.message}"})
            finally:
                c.token = None
        return {"servers": out}

    def tester(self, body, _q) -> dict:
        sid, method = body.get("server"), body.get("method")
        if sid not in self.clients:
            raise web.ApiError(400, "Choose one of the servers.")
        if method not in ("server/discover", "tools/list", "tools/call"):
            raise web.ApiError(400, "Choose a method.")
        params = {}
        if method == "tools/call":
            name, args = body.get("name"), body.get("arguments", {})
            if not isinstance(name, str) or not name.strip():
                raise web.ApiError(400, "Name the tool to call.")
            if not isinstance(args, dict):
                raise web.ApiError(400, "The arguments must be a JSON object.")
            params = {"name": name.strip(), "arguments": args}
        brk = body.get("break") or ""
        if brk and brk not in BREAKS:
            raise web.ApiError(400, "Unknown way to break the request.")
        extra = {BREAKS[brk][0]: BREAKS[brk][1]} if brk else None
        client = self.clients[sid]
        err = None
        token = body.get("token")
        client.token = token.strip() if isinstance(token, str) and token.strip() else None
        try:
            client.request(method, params, extra_headers=extra)
        except mcpmini.McpError as exc:
            err = exc
        finally:
            client.token = None
        last = client.last
        result = {"status": last["status"], "request": {"headers": last["headers"], "body": last["request"]}, "response": last["response"],
                  "server": sid, "method": method, "tool": params.get("name"), "error": err.message if err else None}
        if self.on_tester:
            self.on_tester(result, brk)
        return result

    def ask(self, body, _q) -> dict:
        question = body.get("question")
        if not isinstance(question, str) or not question.strip():
            raise web.ApiError(400, "Type a question first.")
        if len(question) > MAX_QUESTION:
            raise web.ApiError(400, f"Keep the question under {MAX_QUESTION} characters.")
        model = body.get("model", hostmod.DEFAULT_MODEL)
        if model not in {m["id"] for m in MODELS}:
            raise web.ApiError(400, "Unknown model.")
        started = time.time()
        try:
            result = self.make_host().answer(question.strip(), model=model)
        except (openai.OpenAIError, OSError):
            raise web.ApiError(502, "The assistant could not get an answer from the model. Is the gateway running and the local model server up?")
        monitor = self.watch(result, question.strip()) if self.watch else {"alerts": [], "rows": []}   # a watcher may mark a call with "risk"
        calls = [{"name": f"{c['server']}.{c['tool']}", "args": c["args"], "result": {"text": c["text"], "isError": c["isError"]},
                  **({"risk": c["risk"]} if c.get("risk") else {"risk": "refused by the host"} if c.get("blocked") else {})} for c in result["tool_calls"]]
        return {"question": question.strip(), "model": model, "shown": result["shown"], "raw": result["raw"], "seconds": round(time.time() - started, 1),
                "chunks": [], "messages": result["messages"], "tool_calls": calls, "catalog": result["catalog"], "monitor": monitor}

    def set_fixes(self, body, _q) -> dict:
        DATA.mkdir(parents=True, exist_ok=True)
        self.fixes_file.write_text("on" if body.get("on") is True else "off")
        return self.state({}, {})

    # ------------------------------------------------------------ run
    def routes(self) -> dict:
        r = {("GET", "/api/config"): self.config, ("GET", "/api/state"): self.state, ("GET", "/api/servers"): self.servers,
             ("POST", "/api/tester"): self.tester, ("POST", "/api/ask"): self.ask}
        if self.has_fixes:
            r[("POST", "/api/fixes")] = self.set_fixes
        return r

    def run(self, extra_routes: dict | None = None) -> None:
        DATA.mkdir(parents=True, exist_ok=True)
        self.start_servers()
        routes = self.routes()
        routes.update(extra_routes or {})
        print(f"{self.product} listening on :8080 ({len(self.clients)} MCP servers inside)", flush=True)
        web.serve(routes, str(STATIC), port=8080)
