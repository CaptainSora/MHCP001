from datetime import datetime, timezone

from ortools.linear_solver import pywraplp

# [Flat, Round, Thick, Implantable, Small, Thin, Blank, Clay, Circuit, Dye]
REWARDS = [
    [6, 0, 0, 0, 0, 0, 0, 12,  3,  5],
    [0, 0, 0, 0, 0, 6, 0,  0,  8, 12],
    [0, 6, 0, 0, 0, 0, 0,  0, 12,  8],
    [0, 0, 0, 6, 0, 0, 0, 12,  5,  3],
    [0, 0, 0, 0, 6, 0, 0,  3,  5, 12],
    [0, 0, 6, 0, 0, 0, 0, 12,  8,  0],
    [0, 0, 0, 6, 0, 0, 0,  8,  0, 12], # 7
    [6, 0, 0, 0, 0, 0, 0,  8, 12,  0],
    [0, 0, 6, 0, 0, 0, 0,  3, 12,  5],
    [0, 0, 0, 0, 6, 0, 0, 12,  0,  8],
    [0, 0, 0, 0, 0, 6, 0,  5, 12,  3],
    [0, 6, 0, 0, 0, 0, 0,  5,  3, 12],
    [6, 0, 0, 0, 0, 0, 0,  9, 13,  0],
    [0, 0, 6, 0, 0, 0, 0,  3, 13,  6], # 14
    [0, 6, 0, 0, 0, 0, 0,  6,  3, 13],
    [0, 0, 0, 0, 0, 6, 0,  6, 13,  3],
    [0, 0, 0, 0, 6, 0, 0, 13,  0,  9]
]
BONUSES = [
    [6, 0, 0, 0, 0, 0, 0, 0, 2, 0],
    [0, 0, 0, 0, 0, 6, 0, 0, 2, 0],
    [0, 6, 0, 0, 0, 0, 0, 2, 0, 0],
    [0, 0, 0, 6, 0, 0, 0, 0, 0, 2],
    [0, 0, 0, 0, 6, 0, 0, 2, 0, 0],
    [0, 0, 6, 0, 0, 0, 0, 0, 0, 2],
    [0, 0, 0, 6, 0, 0, 0, 0, 2, 0], # 7
    [6, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [0, 0, 6, 0, 0, 0, 0, 2, 0, 0],
    [0, 0, 0, 0, 6, 0, 0, 0, 2, 0],
    [0, 0, 0, 0, 0, 6, 0, 0, 0, 2],
    [0, 6, 0, 0, 0, 0, 0, 2, 0, 0],
    [6, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [0, 0, 6, 0, 0, 0, 0, 2, 0, 0], # 14
    [0, 6, 0, 0, 0, 0, 0, 0, 2, 0],
    [0, 0, 0, 0, 0, 6, 0, 0, 0, 2],
    [0, 0, 0, 0, 6, 0, 0, 0, 2, 0]
]
STAGE_NAMES = [
    "The fellowship of the disc",
    "Switch and doors",
    "Command and conquer",
    "How to guard treasure",
    "Command center",
    "If you can't enjoy it dodge it",
    "Three-way split", # 7
    "Dangerous fishing",
    "No witness no problem",
    "Being a leader",
    "Training day",
    "Sabotage",
    "Mission impossible",
    "One way street", # 14
    "Elfheim",
    "The great escape",
    "Arms race"
]
# [Flat, Round, Thick, Implantable, Small, Thin, Blank]
COSTS = [
    [5, 2, 1],
    [1, 2, 5],
    [2, 5, 1],
    [5, 1, 2],
    [2, 1, 5],
    [1, 5, 2]
]
BP_TYPES = [
    'Flat', 'Round', 'Thick', 'Implantable', 'Small', 'Thin', 'Blank',
    'Blank from Flat', 'Blank from Round', 'Blank from Thick',
    'Blank from Implantable', 'Blank from Small', 'Blank from Thin'
]
WEEKDAYS = [
    'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday',
    'Friday', 'Saturday'
]

STAGE_CAP = 14

def stage_rewards(inventory, stagenum, boosted=True, first_clear=False):
    """
    Adds a stage's rewards to the inventory.
    inventory: tuple
    stagenum: int between 0 and 13 inclusive
    """
    global REWARDS
    if stagenum < 0 or stagenum >= len(REWARDS):
        return inventory
    return tuple([
        inventory[i] + (int(boosted and i < 7) + 1) * REWARDS[stagenum][i]
        + int(first_clear) * BONUSES[stagenum][i]
        for i in range(len(inventory))
    ])

def score(inventory, verbose=False):
    """
    Finds the maximum possible crafting score for the given inventory.
    """
    # Call Mixed-Integer Linear Programming solver
    solver = pywraplp.Solver.CreateSolver('SCIP')
    # variables
    var_dict = {}
    for j in range(len(BP_TYPES)):
        var_dict[j] = solver.IntVar(0, sum(inventory[:-3]), BP_TYPES[j])
    # constraints
    constraints = [
        #F  R  T  I  S  T  B  BF BR BT BI BS BT
        [6, 0, 0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0],
        [0, 6, 0, 0, 0, 0, 0, 0, 6, 0, 0, 0, 0],
        [0, 0, 6, 0, 0, 0, 0, 0, 0, 6, 0, 0, 0],
        [0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 6, 0, 0],
        [0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 6, 0],
        [0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0, 6],
        [0, 0, 0, 0, 0, 0, 6, 0, 0, 0, 0, 0, 0],
        [5, 1, 2, 5, 2, 1, 3, 3, 3, 3, 3, 3, 3],
        [2, 2, 5, 1, 1, 5, 3, 3, 3, 3, 3, 3, 3],
        [1, 5, 1, 2, 5, 2, 3, 3, 3, 3, 3, 3, 3]
    ]
    for i in range(len(constraints)):
        constraint_expr = [
            constraints[i][j] * var_dict[j] for j in range(len(BP_TYPES))
        ]
        solver.Add(sum(constraint_expr) <= inventory[i])
    # objective function
    scores = [100, 100, 100, 100, 100, 106, 101, 101, 101, 101, 101, 101, 101]
    obj_expr = [scores[j] * var_dict[j] for j in range(len(BP_TYPES))]
    solver.Maximize(sum(obj_expr))
    # solve
    status = solver.Solve()
    crafted = [var.solution_value() for var in solver.variables()]
    if verbose:
        if status == pywraplp.Solver.OPTIMAL:
            print("Found optimal solution:")
            print(f"Objective value = {solver.Objective().Value()}")
            print(f"Inventory: {inventory}")
            for var in solver.variables():
                print(f"{var.name()}: {var.solution_value()}")
        else:
            print("No optimal solution found.")
        print(f"Problem solved in {solver.wall_time()}ms")
    return (solver.Objective().Value(), crafted)

def plan(inventory, depth=3, start_day=-1, max_stage=1):
    # start_day is weekday:
    # Sun = 0, Mon = 1, ..., Sat = 6
    # defaults
    depth = max(1, min(7, depth))
    if start_day < 0 or start_day >= 7:
        start_day = (datetime.now(timezone.utc).weekday() + 1) % 7
    max_stage = max(1, min(max_stage, len(REWARDS)))
    # try all possibilities
    branches = {tuple(inventory): []}
    for d in range(depth):
        cur_day = (start_day + d) % 7
        newbranches = {}
        for inven, hist in branches.items():
            for s in range(max(max_stage, max(hist + [-1]) + 2)):
                # don't test past cap
                if s >= STAGE_CAP:
                    break
                # don't bother testing unboosted
                if cur_day < 6 and (s + cur_day) % 2 == 0:
                    continue
                first_clear = (s + 1 >= max_stage) and (s > max(hist + [-1]))
                new_inven = stage_rewards(inven, s, first_clear=first_clear)
                if new_inven not in newbranches:
                    newbranches[new_inven] = hist + [s]
        branches = newbranches
    # check for highest score
    max_score = 0
    max_hist = []
    crafted = [0 for _ in BP_TYPES]
    mats = [0, 0, 0]
    for inven, hist in branches.items():
        s, c = score(inven)
        if s > max_score:
            max_score = s
            max_hist = hist
            crafted = c
            mats = inven[-3:]
    for i in range(len(COSTS)):
        mats = [int(mats[j] - crafted[i] * COSTS[i][j]) for j in range(3)]
    mats = [int(mats[j] - 3 * sum(crafted[6:])) for j in range(3)]
    print(f"Started from {WEEKDAYS[start_day]}, searched depth {depth}")
    print(f"\nStage order:")
    for d, h in enumerate(max_hist):
        print(f"{WEEKDAYS[(start_day + d) % 7]} - {h+1}: {STAGE_NAMES[h]}")
    print(f"\nTotal crafts:")
    for i in range(len(BP_TYPES)):
        if int(crafted[i]) > 0:
            print(f"{BP_TYPES[i]}: {int(crafted[i])}")
    print(f"\nTotal score: {int(max_score)}")
    print(f"Starting materials: {inventory[-3:]}")
    print(f"Final materials: {mats}")


# [Flat, Round, Thick, Implantable, Small, Thin, Blank, Clay, Circuit, Dye]
plan([0, 6, 0, 0, 0, 12, 0, 30, 0, 33], depth=7, start_day=6, max_stage=13)
plan([0, 0, 0, 0, 0, 0, 0, 5, 6, 13], depth=7, start_day=6, max_stage=15)