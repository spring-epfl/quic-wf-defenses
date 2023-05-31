CONFIG_FILE = 'front_glue/config.ini'

# MPU
TOR_CELL_SIZE = 512

# LB: values taken from the collected dataset. Front/Glue originally works with 1's
PADDED_SIZE_QUIC = 1400
PADDED_SIZE_TLS = 32*1024

# Directions
IN = -1
OUT = 1
DIR_NAMES = {IN: "in", OUT: "out"}
DIRECTIONS = [OUT, IN]

# AP states
GAP = 0x00
BURST = 0x01
WAIT = 0x02

# Mappings
EP2DIRS = {'client': OUT, 'server': IN}
MODE2STATE = {'gap': GAP, 'burst': BURST}

# Histograms
INF = float("inf")
