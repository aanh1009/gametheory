## input to take in: number of players, numer of queries, each person's valuation, type of constraint, constraint values
## steps to take:
##   - a function that runs tiny steps to check for: budget constraint and equilibrium using provided multipliers
##   - for each set of multipliers, calculate the bids, whoever wins each item, the price they need to pay (this fails if exceeded)
##   - return the first equilibrium/all equilibriums
from collections import defaultdict
from itertools import product
import copy

class AutobiddingBudget:
    def __init__(self, n_players: int, n_queries: int, valuations: list[list], budgets: list[int]):
        self.n_players = n_players
        self.n_queries = n_queries
        self.valuations = valuations
        self.budgets = budgets

    ## given the multipliers, check who wins, and check if it exceeds budget constraint
    def bid_outcome(self, multipliers: list[float]):
        ## check budget first 
        winning_bids= []
        payments = defaultdict(int)

        for i in range(self.n_queries):
            highest_bid = 0
            second_highest = 0
            winner = 0
            for j in range(self.n_players):
                bid = self.valuations[j][i]*multipliers[j]
                if bid > highest_bid:
                    second_highest = highest_bid
                    highest_bid = bid
                    winner = j
                elif bid > second_highest:
                    second_highest = bid

            winning_bids.append((i, highest_bid, second_highest, winner))

        values = [[0, 0] for _ in range(self.n_players)]
        for i, _, second_highest, winner in winning_bids:
            values[winner][0] += self.valuations[winner][i]
            values[winner][1] += second_highest 
        
        return winning_bids, values

    def check_equilibrium(self, multipliers: list[float]):
        ## need to check if changing the multipiers would improve without exceeding
        ## the budget

        ## for each person, loop through the items that they did not win,
        ## check if they change , would
        ## that excceed their budget?

        out, values = self.bid_outcome(multipliers=multipliers)
        for i in range(len(values)):
            if values[i][1] > self.budgets[i]:
                return False

        for i in range(self.n_players):
            losses = [win for win in out if win[3] != i]

            thresholds = {0.0, 1.0}
            for j in range(len(losses)):
                threshold = losses[j][1] / self.valuations[i][losses[j][0]]
                if 0 <= threshold <= 1:
                    thresholds.add(threshold)

            points = sorted(thresholds)
            candidates = points + [
                (left + right) / 2
                for left, right in zip(points, points[1:])
            ]
            for new_mu in candidates:
                new_mus = copy.deepcopy(multipliers)
                new_mus[i] = new_mu
                new_wins, new_values = self.bid_outcome(new_mus)
                if new_values[i][1] <= self.budgets[i] and new_values[i][0] > values[i][0]:
                    return False

        return True

    ## find multipliers that form equilibria with a step
    ## of 0.01 for all players
    def find_equilibria(self):
        grid = [step / 100 for step in range(101)]
        for candidate in product(grid, repeat=self.n_players):
            multipliers = list(candidate)
            if self.check_equilibrium(multipliers):
                yield multipliers

    ## check across all equilibria to see if there's an 
    ## equilibria that improves any person's value

    ## this is the intuition behind the non-AICness of autobidding:
    ## a generous constraint (budget) allows for worse payoffs,
    ## so people are incentivized to cheat (under some conditions)
    def check_deviation_incentive(self):
        best_worst_outcomes = [[0, float('inf')] for _ in range(self.n_players)]
        equilibria = self.find_equilibria()

        for multipliers in equilibria:
            _, out = self.bid_outcome(multipliers=multipliers)
            for i in range(self.n_players):
                best_worst_outcomes[i][0] = max(best_worst_outcomes[i][0], out[i][0])
                best_worst_outcomes[i][1] = min(best_worst_outcomes[i][1], out[i][0])

        return best_worst_outcomes

## will have 1 - 2 more classes that implement the new criteria

def test_1():
    game = AutobiddingBudget(n_players=2, n_queries=4, valuations=[[2.1, 40, 30, 20], [1, 20, 25, 100]], budgets=[20, 49])

    print(game.check_deviation_incentive())

def run_tests():
    test_1()

run_tests()


    
