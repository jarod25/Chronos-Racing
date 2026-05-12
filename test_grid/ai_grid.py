import numpy as np


class SimpleMLP:

    def __init__(self, input_size=8, hidden_size=32, output_size=2):

        # Couche 1
        self.W1 = np.random.randn(input_size, hidden_size) * 0.01
        self.b1 = np.zeros(hidden_size)

        # Couche 2
        self.W2 = np.random.randn(hidden_size, output_size) * 0.1
        self.b2 = np.zeros(output_size)

    def forward(self, x):

        x = np.array(x)

        h = np.tanh(np.dot(x, self.W1) + self.b1)

        out = np.tanh(np.dot(h, self.W2) + self.b2)

        return out

    def copy(self):

        clone = SimpleMLP(
            input_size=self.W1.shape[0],
            hidden_size=self.W1.shape[1],
            output_size=self.W2.shape[1]
        )

        clone.W1 = np.copy(self.W1)
        clone.b1 = np.copy(self.b1)

        clone.W2 = np.copy(self.W2)
        clone.b2 = np.copy(self.b2)

        return clone

    def mutate(self, rate=0.01):

        self.W1 += np.random.randn(*self.W1.shape) * rate
        self.b1 += np.random.randn(*self.b1.shape) * rate

        self.W2 += np.random.randn(*self.W2.shape) * rate
        self.b2 += np.random.randn(*self.b2.shape) * rate