from app import app
for rule in sorted(app.url_map.iter_rules(), key=lambda r: (r.rule, r.endpoint)):
    print(rule.rule, '->', rule.endpoint, sorted(rule.methods))
