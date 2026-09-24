DEBUG_ACTIVE = False  # flip to True only for local debugging — output_log is expensive (extra ~5M pts)

MAX_FLOOD_NODES = 50
SAFETY_BUFFER = 2

MAX_A_STAR_NODES = 25
MAX_REACHABILITY_NODES = 80
# having max reachability at 200 seems like the highest limit
# tune verus map size?
PATHFINDING_CACHE_ENABLED = False

# ----------------------- Exploration (in searching behaviour) ----------------------------
EXPLORATION_LOOKAHEAD = 5     # how far to peek for unexplored tiles per direction
EXPLORATION_WEIGHT = 1.0
CROWD_AVOIDANCE_WEIGHT = 2  # tune higher to prioritize spreading out over exploring
PEARL_ANCHOR_WEIGHT = 0.5
PEARL_ANCHOR_PRIMARY_SEARCH_NODES = 10
PEARL_ANCHOR_SECONDARY_SEARCH_NODES = 10
PEARL_ANCHOR_SAMPLES_PER_TURN = 5

DISTANCE_FROM_PEARL_ANCHOR_PENALTY_WEIGHT = 0.2


PORTAL_EXPLORATION_SCORE = 2 # a tile is worth 1
# ----------------------- Exploration (in searching behaviour) ----------------------------

# ------------------------- Pathfinding penalities ------------------------------
# PORTALS: 
# # base_penality + (current_round * round_weight) + (dragon_length * length_weight)
portal_traverse_base_penalty = 2.0
portal_traverse_round_weight = 0.005   # Scales up as the match goes on
portal_traverse_dragon_length_weight = 1.5    # Heavier penalty for longer, more valuable snakes

# Normal Roads:
# road_traverse_base_penalty



# ---------------------- Pearl board ------------------------------------
TOP_PEARL_PERCENTILE = 0.3
UNOBSERVED_PEARL_TIME = -2