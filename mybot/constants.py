DEBUG_ACTIVE = False  # flip to True only for local debugging — output_log is expensive (extra ~5M pts)

MAX_FLOOD_NODES = 25
SAFETY_BUFFER = 2

MAX_A_STAR_NODES = 25
MAX_REACHABILITY_NODES = 25
# having max reachability at 200 seems like the highest limit
# tune verus map size?
PATHFINDING_CACHE_ENABLED = False

# ----------------------- Exploration (in searching behaviour) ----------------------------
EXPLORATION_LOOKAHEAD = 5     # how far to peek for unexplored tiles per direction
EXPLORATION_WEIGHT = 1.0
CROWD_AVOIDANCE_WEIGHT = 2  # tune higher to prioritize spreading out over exploring
PEARL_ANCHOR_WEIGHT = 0.5
PEARL_ANCHOR_PRIMARY_SEARCH_NODES = 20
PEARL_ANCHOR_SECONDARY_SEARCH_NODES = 10
PEARL_ANCHOR_SAMPLES_PER_TURN = 2
PEARL_ANCHOR_UPDATE_INTERVAL = 1

DISTANCE_FROM_PEARL_ANCHOR_PENALTY_WEIGHT = 0.2

DISTANCE_FROM_ZONE_GOAL_PENALTY_WEIGHT = 0.2
ZONE_SCORE_WEIGHT = 0.2


PORTAL_EXPLORATION_SCORE = 2 # a tile is worth 1
# ----------------------- Exploration (in searching behaviour) ----------------------------


# ----------------------- Pearl selection --------------------------
# constants.py — pearl target selection

PEARL_DISTANCE_WEIGHT = 1.0
# Same convention as EXPLORATION_WEIGHT / the existing distance penalty weight:
# 1 point of score lost per tile of wrapped Manhattan distance to the pearl.
# Keeping this at 1.0 makes "tiles away" the natural unit the other weights
# below are calibrated against.

PEARL_FRESHNESS_WEIGHT = 5.0
# get_effective_pearl_frequency() returns values in roughly [0, 1] — most
# observed pearls will sit well under 0.5 (frequency = 1 / pearl_time, and
# pearl_time is rarely close to 1). At weight 5.0, a strong-frequency pearl
# (~0.5) contributes about +2.5 to the score — equivalent to ~2-3 tiles of
# distance advantage, which is enough to matter without letting freshness
# alone override a target that's meaningfully farther away.

PEARL_SWITCH_IMPROVEMENT_THRESHOLD = 3.0
# Vision is a 7x7 window (radius 3), so two simultaneously-visible pearls
# can differ by up to ~12 tiles of wrapped Manhattan distance at the
# extremes, but typically much less. A threshold of 3.0 filters out
# small, noisy fluctuations (e.g. the dragon's own movement shifting
# relative distances by 1-2 tiles turn to turn) while still allowing a
# genuinely better pearl elsewhere in vision to trigger a switch.
# -------------------- Pearl selection ------------------------------



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



# ---------------------- CPU Budget ------------------------------------
STARTING_BUDGET = 12_000_000