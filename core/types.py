import statistics

class Agent_Type:
    def __init__(self):
        self.score = 0

        self.historical_returns = []

    def calc_score(self):
        self.score = statistics.mean(self.historical_returns)

agent_types = {0:Agent_Type(),1:Agent_Type(),2:Agent_Type()}