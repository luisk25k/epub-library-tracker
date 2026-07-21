# -*- coding: utf-8 -*-
"""Quick test: verify Flask app creation and route registration."""
from app import create_app

app = create_app()
print("[OK] Flask app created successfully")

rules = [rule.rule for rule in app.url_map.iter_rules() if not rule.rule.startswith("/static")]
for r in sorted(rules):
    print(f"  {r}")

print(f"\n[OK] Total routes registered: {len(rules)}")
