#!/usr/bin/env bash
# Run garak against the lab's model or against TrailBot behind one of the guardrails.
#
#   bash /lab/scan.sh <target> <probes> [generations] [report-name]
#
#   target       model                 the bare local model (bdai-victim), through the gateway
#                trailbot-none         TrailBot, no guardrail                      (the Lab 8.1 application)
#                trailbot-keyword      TrailBot behind the keyword blocklist
#                trailbot-judge        TrailBot behind the model judge
#                trailbot-output       TrailBot behind the output filter
#                trailbot-architecture TrailBot with the architectural fix
#   probes       garak probe names, comma separated, e.g. dan.Dan_11_0,goodside.WhoIsRiley   (list them: python -m garak --list_probes)
#   generations  replies per prompt (default 1)
#   report-name  the report is written to /data/<report-name>.report.jsonl (default: scan)
set -euo pipefail
target="${1:-}"; probes="${2:-}"; gens="${3:-1}"; name="${4:-scan}"
if [ -z "$target" ] || [ -z "$probes" ]; then sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 2; fi
case "$target" in
  model) opts=/lab/options-model.json; tname=bdai-victim ;;
  trailbot-none|trailbot-keyword|trailbot-judge|trailbot-output|trailbot-architecture) opts=/lab/options-trailbot.json; tname="$target" ;;
  *) echo "Unknown target: $target (see the list above)" >&2; exit 2 ;;
esac
exec python -m garak --target_type openai.OpenAICompatible --target_name "$tname" -G "$opts" --probes "$probes" --generations "$gens" --report_prefix "/data/$name"
