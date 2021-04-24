def one_order(seq, prob=1):
    """
    Calculates probabilities for one new order.
    Returns a dictionary of new sequences and probabilities given a sequence
    and its probability.
    """
    # seq: tuple of ints
    # returns: dict of tuple:float
    odds = [max(0, (sum(seq)+2)/len(seq) - i) for i in seq]
    prob_list = [o/sum(odds) for o in odds]
    newseqs = {}
    for i, p in enumerate(prob_list):
        if p == 0:
            continue
        newseq = list(seq)
        newseq[i] += 1
        newseqs[tuple(newseq)] = prob * p
    return newseqs

def sequence_prediction(recipes, depth, start):
    """
    Returns the breakdown of order distributions and their probabilities.
    Static orders (1p only) are not counted as part of the formula, and should
    not be included in the "depth" parameter.
    """
    # recipes: list of str, short name for each recipe
    # depth: int, number of total orders
    # start: (list of int) or None, start from this point
    # returns: dict {dist: prob}
    if start is None:
        start = [0 for _ in recipes]
    elif len(start) != len(recipes):
        print("Initial orders do not line up with recipes!")
        return False
    dists = {tuple(start): 1}
    curdepth = sum(start)
    while curdepth < depth:
        newdists = {}
        for dist, prob in dists.items():
            next_seqs = one_order(dist, prob=prob)
            for seq, p in next_seqs.items():
                if seq not in newdists:
                    newdists[seq] = 0
                newdists[seq] += p
        dists = newdists
        curdepth += 1
    return dists


def matches(aggr, seq):
    """
    Checks if a sequence matches an aggregation.
    """
    if len(aggr) != len(seq):
        print("matches() arguments' lengths mismatched")
        return False
    for i in range(len(aggr)):
        if aggr[i] == 'x':
            continue
        elif aggr[i] != seq[i]:
            return False
    return True

def menu_dist(recipes, depth, start=None, aggr=None):
    """
    Calculates the distribution of possible menu sequences at a given depth,
    with optional aggregation(s).
    """
    print("<Function call to menu_dist>")
    # Convert number of recipes to name for each recipe
    if isinstance(recipes, int):
        recipes = [chr(65+i) for i in range(recipes)]
    # Search
    seq_pred = sequence_prediction(recipes, depth, start=start)
    # Output
    print(f"{len(recipes)} recipes: {', '.join(recipes)}")
    if start is not None:
        print(f"Starting from {start} (depth {sum(start)})")
    print(f"Searching until depth {depth}")
    if aggr is None:
        print("Showing all results")
        # No aggregation: print all options
        for s, p in seq_pred.items():
            print(f"{s}: {100*p:.2f}%")
    else:
        print("Showing aggregated results")
        if isinstance(aggr[0], (int, str)):
            aggr = [aggr]
        # Aggregation: sum and print
        aggr_probs = [0 for _ in aggr]
        for s, p in seq_pred.items():
            for i, a in enumerate(aggr):
                if matches(a, s):
                    aggr_probs[i] += p
                    break
        print(f"Total probability: {100 * sum(aggr_probs):.2f}%")
        for i in range(len(aggr)):
            print(f"{aggr[i]}: {100 * aggr_probs[i]:.2f}%")
    print()


### SAMPLE USAGE:
# menu_dist(5, 11)
# menu_dist(
#     5, 11, start=(2, 2, 1, 1, 0),
#     aggr=[(3, 'x', 'x', 'x', 'x'), ('x', 3, 2, 'x', 'x')]
# )
### Arguments:
# -- REQUIRED --
# recipes: menu set size (int) or list of recipe names (list of str)
# depth: how many orders to calculate probability for
# -- OPTIONAL --
# start: where to begin probability calculations (tuple of int)
# aggr: types of menus to group together (list of (tuple of int))

menu_dist(3, 17)
menu_dist(3, 18)
menu_dist(3, 19)


def seq_matches_target(target, seq):
    """
    Calculates the difference between seq and target.
    Negative indicates extra orders.
    Positive indicates missing orders.
    """
    status = [0 for _ in target]
    for i in range(len(target)):
        if target[i] == 'x':
            continue
        status[i] = target[i] - seq[i]
    return status

def target_menu_probability(recipes, served, visible, target,
        final_orders=1, start=None, exact=False, detailed=False):
    """
    Calculates the total probability of getting a favourable menu, taking into
    account the last order being later in the sequence.
    """
    print("<Function call to target_menu_probability>")
    prob_dict = {}
    # Convert number of recipes to name for each recipe
    if isinstance(recipes, int):
        recipes = [chr(65+i) for i in range(recipes)]
    else:
        recipes = [str(r) for r in recipes]
    # Find all menu sequences up to the second-last order
    depth = served - final_orders
    seq_pred = sequence_prediction(recipes, depth, start)
    for dist, prob in seq_pred.items():
        # Find all menu sequences from the second last order given the number
        #   of orders visible
        view_pred = sequence_prediction(recipes, visible, dist)
        diff = seq_matches_target(target, dist)
        pos_diff = [max(d, 0) for d in diff]
        # Check status of dist
        if all([d == 0 for d in diff]) or (not exact and max(diff) <= 0):
            # dist satisfies target
            prob_dict[dist] = (prob, view_pred)
            continue
        elif exact and min(diff) < 0:
            # Overshot target, exact required
            continue
        elif sum(pos_diff) > final_orders:
            # Missing too many orders
            continue
        # filter and sort
        view_pred = {
            k: v for k, v in sorted(
                view_pred.items(), key=lambda item: item[1], reverse=True)
            if all([k[i] >= dist[i] + pos_diff[i] for i in range(len(k))]) \
                and not (exact and min(seq_matches_target(target, k)) < 0)
        }
        # No possibilities
        if not view_pred:
            continue
        # Save
        prob_dict[dist] = (prob * sum(view_pred.values()), view_pred)
    # Prepare output
    prob_dict = {
        k: v for k, v in sorted(
            prob_dict.items(), key=lambda item: item[1][0], reverse=True)
    }
    total_prob = sum([v[0] for v in prob_dict.values()])
    target_str = f"({', '.join([str(t) for t in target])})"
    print(f"{len(recipes)} recipes: {', '.join(recipes)}")
    if start is not None:
        print(f"Starting from {start}")
    print(f"Targeting {served} total orders served (excl. static)")
    print(f"    Final menu: {target_str}")
    print(f"    Final orders: {final_orders}")
    print(f"Searching until {visible} total orders visible on screen")
    print(f"    ({visible - served + final_orders} orders visible at the end)")
    print(f"\n=== Total probability: {100 * total_prob:.2f}% ===\n")
    print(f"Probability breakdown:")
    print(f"(Menu at {depth} orders): (Total probability of target menu)")
    if detailed:
        print(f"    (Total visible orders): (Relative probability)")
    prob_list = []
    for seq, prob in prob_dict.items():
        print(f"{seq}: {100 * prob[0]:.2f}%")
        if detailed:
            for subseq, subprob in prob[1].items():
                print(f"    {subseq}: {100 * subprob:.2f}%")
    print()


### SAMPLE USAGE:
# target_menu_probability(5, 7, 9, (2, 2, 'x', 'x', 'x'))
# target_menu_probability(
#     5, 7, 9, (2, 2, 'x', 'x', 'x'), final_orders=1,
#     start=(1, 1, 0, 0, 0), exact=False, detailed=True
# )
### Arguments:
# -- REQUIRED --
# recipes: menu set size (int) or list of recipe names (list of str)
# served: number of orders you plan to serve (including the last one)
# visible: total number of orders visible during the level
# target: target menu (tuple of int); use 'x' for any you don't care about
# -- OPTIONAL --
# final_orders: how many orders you're serving last second/guessing at the end
# start: start state (tuple of int) if you want to start probability
#        calculations from partway into a stage
# exact: whether you want the target numbers to reject going over
#   i.e. setting exact=True will reject (2, 3, 1) if the target is (2, 2, 'x')
#   This is applied to all orders on screen
# detailed: if you want detailed breakdown of each possibility

target_menu_probability(
    3, 21, 22, (8, 8, 'x'), final_orders=2, start=(0, 0, 0),
    exact=False, detailed=True
)


# Next targets:
# Write a function which gives probabilities for exact lengths
# - f((7, 7, 5), 3) and outputs (CAB: x, CBA: y, ...)
# Write a function which takes into account scoring and limiting action
# - f([('C', 40, 1), ('P', 40, 1), ('CP', 60, 2)], 3, 24) outputs 1396