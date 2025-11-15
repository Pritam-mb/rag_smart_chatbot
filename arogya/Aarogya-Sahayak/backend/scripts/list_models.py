import importlib
import os
import traceback

print('PYTHON:', os.sys.executable)
print('GOOGLE_API_KEY present:', bool(os.getenv('GOOGLE_API_KEY')))

mod_name = 'langchain_google_genai'
try:
    mod = importlib.import_module(mod_name)
except Exception as e:
    print(f'Failed to import {mod_name}:', e)
    traceback.print_exc()
    raise SystemExit(1)

print('\nExports:')
exports = [n for n in dir(mod) if not n.startswith('_')]
print(exports)

def try_call(name):
    fn = getattr(mod, name, None)
    if not fn:
        print(f"{name} not available")
        return
    print(f"\nCalling {name}() ->")
    try:
        out = fn()
        print(out)
    except Exception as e:
        print(f"{name}() raised:", e)
        traceback.print_exc()

try_call('list_models')
try_call('chat_models')
try_call('model_list')

print('\nDone')
