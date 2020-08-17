"""
RNN/GRU example
===========

example of vanilla RNN for time series regression
"""
import symjax.tensor as T
from symjax import nn
import symjax
import numpy as np
import matplotlib.pyplot as plt
import sys

sys.setrecursionlimit(3500)


def classif_tf(train_x, train_y, test_x, test_y):
    import tensorflow as tf
    from tensorflow.keras import layers

    batch_size = 128

    inputs = layers.Input(shape=(3, 32, 32))
    out = layers.Permute((2, 3, 1))(inputs)
    out = layers.Conv2D(32, 3, activation="relu")(out)
    for i in range(3):
        for j in range(10):

            conv = layers.Conv2D(32 * (i + 1), 3, activation="linear", padding="SAME")(
                out
            )
            bn = layers.BatchNormalization(axis=-1)(conv)
            relu = layers.Activation("relu")(bn)
            conv = layers.Conv2D(32 * (i + 1), 3, activation="linear", padding="SAME")(
                relu
            )
            bn = layers.BatchNormalization(axis=-1)(conv)

            out = layers.Add()([out, bn])
        out = layers.AveragePooling2D()(out)
        out = layers.Conv2D(32 * (i + 2), 1, activation="linear")(out)

    out = layers.GlobalAveragePooling2D()(out)
    outputs = layers.Dense(10, activation="linear")(out)

    model = tf.keras.Model(inputs, outputs)
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)

    for epoch in range(10):
        for x, y in symjax.data.utils.batchify(
            train_x, train_y, batch_size=batch_size, option="random"
        ):
            with tf.GradientTape() as tape:
                preds = model(x, training=True)
                loss = tf.reduce_mean(
                    tf.nn.sparse_softmax_cross_entropy_with_logits(y, preds)
                )

            grads = tape.gradient(loss, model.trainable_variables)
            optimizer.apply_gradients(zip(grads, model.trainable_variables))
        accu = 0
        for x, y in symjax.data.utils.batchify(
            test_x, test_y, batch_size=batch_size, option="continuous"
        ):
            preds = model(x, training=False)
            accu += tf.reduce_mean(tf.cast(y == tf.argmax(preds, 1), "float32"))
        print(accu / (len(test_x) // batch_size))


def classif_sj(train_x, train_y, test_x, test_y):
    symjax.current_graph().reset()
    from symjax import nn

    batch_size = 128

    input = T.Placeholder((batch_size, 3, 32, 32), "float32")
    labels = T.Placeholder((batch_size,), "int32")
    deterministic = T.Placeholder((), "bool")

    out = nn.relu(nn.layers.Conv2D(input, 32, (3, 3)))
    for i in range(3):
        for j in range(10):
            conv = nn.layers.Conv2D(out, 32 * (i + 1), (3, 3), pad="SAME")
            bn = nn.relu(
                nn.layers.BatchNormalization(conv, [1], deterministic=deterministic)
            )
            conv = nn.layers.Conv2D(bn, 32 * (i + 1), (3, 3), pad="SAME")
            bn = nn.layers.BatchNormalization(conv, [1], deterministic=deterministic)
            out = bn + out

        out = nn.layers.Pool2D(out, (2, 2), pool_type="AVG")
        out = nn.layers.Conv2D(out, 32 * (i + 2), (1, 1))

    out = nn.layers.Pool2D(out, out.shape[-2:], pool_type="AVG")
    outputs = nn.layers.Dense(out, 10)

    loss = nn.losses.sparse_softmax_crossentropy_logits(labels, outputs).mean()
    nn.optimizers.Adam(loss, 0.001)

    accu = T.equal(outputs.argmax(1), labels).astype("float32").mean()

    train = symjax.function(
        input, labels, deterministic, outputs=loss, updates=symjax.get_updates(),
    )
    test = symjax.function(input, labels, deterministic, outputs=accu)

    for epoch in range(10):
        for x, y in symjax.data.utils.batchify(
            train_x, train_y, batch_size=batch_size, option="random"
        ):
            train(x, y, 0)

        accu = 0
        for x, y in symjax.data.utils.batchify(
            test_x, test_y, batch_size=batch_size, option="continuous"
        ):
            accu += test(x, y, 1)
        print(accu / (len(test_x) // batch_size))


mnist = symjax.data.cifar10()
train_x, train_y = mnist["train_set/images"], mnist["train_set/labels"]
test_x, test_y = mnist["test_set/images"], mnist["test_set/labels"]
train_x /= train_x.max()
test_x /= test_x.max()

classif_sj(train_x, train_y, test_x, test_y)
classif_tf(train_x, train_y, test_x, test_y)