DEBUG = True  # flip to True only for local debugging — output_log is expensive (~2.5M pts/call)

MAX_FLOOD_NODES = 50
SAFETY_BUFFER = 2

MAX_A_STAR_NODES = 25
MAX_REACHABILITY_NODES = 80
# having max reachability at 200 seems like the highest limit
# tune verus map size?

EXPLORATION_LOOKAHEAD = 5     # how far to peek for unexplored tiles per direction
EXPLORATION_WEIGHT = 1.0
CROWD_AVOIDANCE_WEIGHT = 2  # tune higher to prioritize spreading out over exploring