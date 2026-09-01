import sys
print('start')
try:
    import pandas as pd
    print('pandas ok')
    import matplotlib
    print('matplotlib module ok, backend before:', matplotlib.get_backend())
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    print('matplotlib backend after set:', matplotlib.get_backend())
except Exception as e:
    print('import error', e)
    sys.exit(2)

# try simple plot
try:
    plt.figure()
    plt.plot([1,2,3])
    plt.savefig('debug_test.png')
    print('saved debug_test.png')
except Exception as e:
    print('plot error', e)
    sys.exit(3)

print('files in cwd:')
import os
print('\n'.join(os.listdir('.')))
print('end')
