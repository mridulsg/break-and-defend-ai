#!/usr/bin/env bash
# Runs inside the Lab 9.3 scanner container: makes a pickle that only imports a harmless function and asks each tool about it.
set -uo pipefail
python -c "import pickle, builtins; pickle.dump(builtins.print, open('/tmp/p.pkl', 'wb'), protocol=2)"
picklescan --path /tmp/p.pkl | grep -q 'Suspicious globals: 1' && echo "picklescan: suspicious"
modelscan scan -p /tmp/p.pkl | grep -q 'No issues found' && echo "modelscan: no issues"
fickling --check-safety /tmp/p.pkl; echo "fickling: exit $?"
