#!/usr/bin/env python3
import os
import re

# Read app.py and extract template names
with open('app.py', 'r') as f:
    content = f.read()

# Find all render_template calls with template names
pattern = r'render_template\(\s*["\']([^"\']+)["\']'
templates_used = sorted(set(re.findall(pattern, content)))

# Get actual template files
template_dir = 'templates'
actual_templates = sorted([f for f in os.listdir(template_dir) if f.endswith('.html')])

print("=" * 60)
print("TEMPLATE FILES CHECK")
print("=" * 60)

print("\nTemplates referenced in app.py:")
for t in templates_used:
    exists = os.path.exists(os.path.join(template_dir, t))
    status = "✅" if exists else "❌ MISSING"
    print(f"  {status} {t}")

print("\nActual template files in templates/:")
for t in actual_templates:
    used = t in templates_used
    status = "✅" if used else "⚠️  UNUSED"
    print(f"  {status} {t}")

print("\n" + "=" * 60)
missing = [t for t in templates_used if not os.path.exists(os.path.join(template_dir, t))]
if missing:
    print(f"❌ Missing templates: {missing}")
else:
    print("✅ All required templates exist!")
