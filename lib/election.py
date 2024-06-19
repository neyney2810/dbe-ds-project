# Defined a election calculator class to calculate the election results based on the input data.

class Election:
    def __init__(self, data):
        self.data = data

    def calculate(self):
        # Calculate the election results
        results = {}
        for candidate in self.data:
            results[candidate] = sum(self.data[candidate])
        return results
