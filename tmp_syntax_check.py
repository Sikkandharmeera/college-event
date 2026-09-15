import ast
from pathlib import Path
text = Path('app.py').read_text(encoding='utf-8')
try:
    ast.parse(text)
    print('ok')
except SyntaxError as e:
    print('SyntaxError', e.lineno, e.offset, repr(e.text))
    raise
