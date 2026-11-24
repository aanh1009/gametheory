## input to take in: number of players, numer of queries, each person's valuation, type of constraint, constraint values
## steps to take:
##   - a function that runs tiny steps to check for: budget constraint and equilibrium using provided multipliers
##   - for each set of multipliers, calculate the bids, whoever wins each item, the price they need to pay (this fails if exceeded)
##   - return the first equilibrium/all equilibriums
from collections import defaultdict
from itertools import product
import copy

class Autobidding:
    def __init__(self, n_players: int, n_queries: int, valuations: list[list], constraint_type: str, constraint_values: list[int]):
        self.n_players = n_players
        self.n_queries = n_queries
        self.valuations = valuations
        self.constraint_type = constraint_type
        self.constraint_values = constraint_values

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
            if values[i][1] > self.constraint_values[i]:
                return False
            
        for i in range(self.n_players):
            losses = [win for win in out if win[3] != i]

            ## as soon as we found a multiplier that would let this person win,
            ## it is not an equilbrium 
            for j in range(len(losses)):
                new_mu = losses[j][1]/self.valuations[i][losses[j][0]]
                if 0<= new_mu <= 1:
                    new_mus = copy.deepcopy(multipliers)
                    new_mus[i] = new_mu
                    new_wins, new_values = self.bid_outcome(new_mus)
                    if new_values[i][1] <= self.constraint_values[i] and new_values[i][0] > values[i][0]:
                        return False
            
        return True


    def find_equilibria(self):
        grid = [step / 100 for step in range(101)]
        for candidate in product(grid, repeat=self.n_players):
            multipliers = list(candidate)
            if self.check_equilibrium(multipliers):
                yield multipliers


    
