"""
Basic scan/loops examples
=========================

In this example we demonstrate how to employ the :py:func:`symjax.tensor.scan`
and other similar functions.

We first demonstrate how to compute a moving average with
:py:func:`symjax.tensor.scan`

We then demonstrate how to do a simple for loop and then a while loop.

"""

import matplotlib.pyplot as plt

import symjax
import symjax.tensor as T
import numpy as np


# suppose we are given a time-serie and we want to compute an
# exponential moving average, we also use the EMA coefficient alpha
# based on the user input

signal = T.Placeholder((512,), "float32", name="signal")
alpha = T.Placeholder((), "float32", "alpha")

# to use a scan function one needs a function to be applied at each step
# in our case an exponential moving average function
# this function should output the new value of the carry as well as an
# additional output, in our case, the carry (EMA) is also what we want to
# output at each tiem step


def fn(at, xt, alpha):
    # the function first input is the carry, then are the (ordered)
    # values from sequences and non_sequences similar to Theano
    EMA = at * alpha + (1 - alpha) * xt
    return EMA, EMA


# the scan function will return the carry at each time steps (first arg.)
# as well as the last one, we also need to provide an init.
last_ema, all_ema = T.scan(
    fn, init=signal[0], sequences=[signal[1:]], non_sequences=[alpha]
)


f = symjax.function(signal, alpha, outputs=all_ema)

# generate a signal
x = np.cos(np.linspace(-3, 3, 512)) + np.random.randn(512) * 0.2

fig, ax = plt.subplots(3, 1, figsize=(3, 9))

for k, alpha in enumerate([0.1, 0.5, 0.9]):
    ax[k].plot(x, c="b")
    ax[k].plot(f(x, alpha), c="r")
    ax[k].set_title("EMA: {}".format(alpha))
    ax[k].set_xticks([])
    ax[k].set_yticks([])

plt.tight_layout()


# Now let's do a simple map for which we can compute a simple
# moving average. The for loop will consist of moving a window and
# average the values on that window

# in that case the function also needs to be defined


def fn(window):
    # the function first input is the current index of the for loop
    # the other inputs are the (ordered) sequences and non_sequnces
    # values

    return T.mean(window)


windowed = T.extract_signal_patches(signal, 10)
output = T.map(fn, sequences=[windowed])
f = symjax.function(signal, outputs=output)

fig, ax = plt.subplots(1, 1, figsize=(5, 2))

ax.plot(x, c="b")
ax.plot(f(x), c="r")
ax.set_title("SMA: 10")
ax.set_xticks([])
ax.set_yticks([])

plt.tight_layout()
