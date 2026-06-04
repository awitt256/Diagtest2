import sys, traceback, os
import importlib.util as importlib_util

p = os.path.join(r'c:/Users/Anthony/Desktop/ALL BAT AND PS1 FILES', 'touchpad_test.py')
print('Importing', p)
try:
    spec = importlib_util.spec_from_file_location('touchpad_test', p)
    m = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(m)
    print('OK')
except Exception:
    traceback.print_exc()
    sys.exit(1)
