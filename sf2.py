# SignFinder2 by d3ranged

import sys

if sys.version_info < (3, 8):
	print('\n\tSF2 requires Python 3.8+\n')
	sys.exit()

from core import *

if __name__ == '__main__':
	core = SF_CORE(__file__)
	core.start_cli()
