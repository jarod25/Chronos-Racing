import numpy as np


class SimpleMLP:
    def __init__(self, input_size=4, hidden_size=8, output_size=2):

        self.W1 = np.random.randn(input_size, hidden_size) * 0.1
        self.b1 = np.zeros(hidden_size)

        self.W2 = np.random.randn(hidden_size, output_size) * 0.1
        self.b2 = np.zeros(output_size)

    def forward(self, x):
        x = np.array(x)

        h = np.tanh(np.dot(x, self.W1) + self.b1)
        out = np.tanh(np.dot(h, self.W2) + self.b2)

        return out