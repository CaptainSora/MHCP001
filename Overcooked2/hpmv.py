def next_probabilities(scenario):
    x = (sum(scenario) + 2) / len(scenario)
    weights = [max(x - s, 0) for s in scenario]
    total_weight = sum(weights)
    probs = [weight / total_weight for weight in weights]
    return probs

# print(next_probabilities([1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]))
# print(next_probabilities([2,2,2,2,2,2,1,1,1,1,1,1,1,1,0,0]))

def next_distribution_one(scenario):
    result = []
    probs = next_probabilities(scenario)
    for i in range(len(scenario)):
        next_scenario = scenario[:]
        next_scenario[i] += 1
        prob = probs[i]
        if prob > 0:
            result.append((prob, next_scenario))
    return result

def simplify_scenario(scenario):
    m = min(scenario)
    return [s-m for s in scenario]

def encode_scenario(scenario):
    return ','.join(map(str, scenario))

def decode_scenario(scenario):
    return list(map(int, scenario.split(',')))

def next_distribution(scenarios):
    result = {}
    for scenario_e, prob in scenarios.items():
        next_distrib = next_distribution_one(decode_scenario(scenario_e))
        for next_prob, next_scenario in next_distrib:
            next_scenario_e = encode_scenario(next_scenario)
            if next_scenario_e not in result:
                result[next_scenario_e] = 0
            result[next_scenario_e] += prob * next_prob
    return result
        
distrib = {encode_scenario([0, 0, 0]): 1}

# # # 924
# for i in range(11):
#     print('Round #' + str(i) + ":")
#     for scenario, prob in distrib.items():
#         print('  ' + scenario + ": " + str(prob))
#     print()
#     distrib = next_distribution(distrib)
#     if i == 6:
#         distrib = {'3,3,1' : distrib['3,3,1']}


# # 900
# for i in range(10):
#     print('Round #' + str(i) + ":")
#     for scenario, prob in distrib.items():
#         print('  ' + scenario + ": " + str(prob))
#     print()
#     distrib = next_distribution(distrib)
#     if i == 5:
#         distrib = {
#             '2,3,1' : distrib['2,3,1'],
#             '3,2,1' : distrib['3,2,1']
#         }
#     if i == 6:
#         del distrib['3,3,1']


# 876
# for i in range(10):
#     print('Round #' + str(i) + ":")
#     for scenario, prob in distrib.items():
#         print('  ' + scenario + ": " + str(prob))
#     print()
#     distrib = next_distribution(distrib)
#     if i == 4:
#         distrib = {
#             '2,2,1' : distrib['2,2,1'],
#         }
#     if i == 5:
#         distrib = {
#             '2,2,2' : distrib['2,2,2'],
#         }

# # 4 doubles, 9 singles
for i in range(30):
    print('Round #' + str(i) + ":")
    for scenario, prob in distrib.items():
        print('  ' + scenario + ": " + str(prob))
    print()
    distrib = next_distribution(distrib)