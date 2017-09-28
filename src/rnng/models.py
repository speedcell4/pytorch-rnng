from typing import Tuple

import torch
import torch.nn.functional as F
from torch.autograd import Variable
from torch.nn import Module, LSTMCell


class StackedLSTMCell(Module):
    def __init__(self, input_size: int, hidden_size: int, num_layers: int = 1,
                 dropout: float = 0.) -> None:
        if num_layers < 1:
            raise ValueError('number of layers is at least 1')

        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self._cells = [LSTMCell(input_size, hidden_size) for _ in range(num_layers)]

    def forward(self, inputs: Variable, init_states: Tuple[Variable, Variable]) -> Tuple[
            Variable, Variable]:
        # inputs: batch_size x input_size
        # init_states: (h0, c0)
        # h0: num_layers x batch_size x hidden_size
        # c0: num_layers x batch_size x hidden_size
        # outputs: (h1, c1)
        # h1: num_layers x batch_size x hidden_size
        # c1: num_layers x batch_size x hidden_size

        assert len(self._cells) >= 1

        h0, c0 = init_states
        h1, c1 = [], []

        if h0.dim() != 3 or c0.dim() != 3:
            raise ValueError('h0 and c0 should have dimension of 3')
        if h0.size()[0] != self.num_layers or c0.size()[0] != self.num_layers:
            raise ValueError('first dimension of h0 and c0 should match the number of layers')

        inputs = F.dropout(inputs, p=self.dropout, training=self.training)
        next_h, next_c = self._cells[0](inputs, (h0[0], c0[0]))
        next_h = F.dropout(next_h, p=self.dropout, training=self.training)
        h1.append(next_h)
        c1.append(next_c)
        for cell, h0_layer, c0_layer in zip(self._cells[1:], h0[1:], c0[1:]):
            next_h, next_c = cell(next_h, (h0_layer, c0_layer))
            next_h = F.dropout(next_h, p=self.dropout, training=self.training)
            h1.append(next_h)
            c1.append(next_c)
        return torch.stack(h1), torch.stack(c1)


class EmptyStackError(Exception):
    def __init__(self):
        super().__init__('stack is already empty')


class StackLSTM(Module):
    def __init__(self, input_size: int, hidden_size: int) -> None:
        super().__init__()
        self.input_size = input_size
        self.hidden_size = hidden_size
        self._cell = LSTMCell(input_size, hidden_size)
        self._history = [('dummy_h0', 'dummy_c0')]

    def forward(self, inputs):
        next_hist = self._cell(inputs, self._history[-1])
        self._history.append(next_hist)
        return next_hist

    def pop(self):
        if len(self._history) > 1:
            return self._history.pop()
        else:
            raise EmptyStackError()

    @property
    def top(self):
        return self._history[-1][0] if len(self._history) > 1 else None