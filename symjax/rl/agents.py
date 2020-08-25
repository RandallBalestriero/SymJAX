import symjax
import symjax.tensor as T
import numpy as np


class Agent(object):
    @property
    def batch_size(self):
        return self.actor.batch_size

    def get_action(self, state):
        return self.actor.get_action(state)

    def get_noise_action(self, state):
        return self.actor.get_noise_action(state)

    def get_actions(self, states):
        return self.actor.get_actions(states)

    def get_noise_actions(self, states):
        if not hasattr(self, "_noise_actions"):
            raise RuntimeError("actor not well initialized")
        return self.actor.get_noise_actions(states)


class Actor(object):
    def __init__(self, batch_size, state_shape, tau=0.99):
        self.tau = tau
        self.batch_size = batch_size
        self.states = T.Placeholder((batch_size,) + state_shape, "float32")
        self.state = T.Placeholder((1,) + state_shape, "float32")
        with symjax.Scope("actor"):
            self.actions = self.create_network(self.states)
            self.action = self.actions.clone({self.states: self.state})

        with symjax.Scope("target_actor"):
            self.target_actions = self.create_network(self.states)
            self.target_action = self.target_actions.clone({self.states: self.state})

        self.params = symjax.get_variables(scope="*actor", trainable=True)

        self._get_actions = symjax.function(self.states, outputs=self.target_actions)
        self._get_noise_actions = symjax.function(
            self.states, outputs=self.target_actions
        )
        self._get_action = symjax.function(self.state, outputs=self.action[0])
        self._get_noise_action = symjax.function(
            self.state, outputs=self.target_action[0]
        )

        self._get_target_actions = symjax.function(
            self.states, outputs=self.target_actions
        )
        self._get_target_noise_actions = symjax.function(
            self.states, outputs=self.target_actions
        )
        self._get_target_action = symjax.function(
            self.state, outputs=self.target_action[0]
        )
        self._get_target_noise_action = symjax.function(
            self.state, outputs=self.target_action[0]
        )

        tau = T.Placeholder((), "float32")
        updates = {
            t: t * tau + a * (1 - tau)
            for t, a in zip(
                symjax.get_variables(scope="/target_actor/"),
                symjax.get_variables(scope="/actor/"),
            )
        }
        self._update_target = symjax.function(tau, updates=updates)
        self.update_target(0)

    def get_action(self, state):
        if state.ndim < 2:
            state = state[np.newaxis, :]
        if not hasattr(self, "_get_action"):
            raise RuntimeError("actor not well initialized")
        return self._get_action(state)

    def get_noise_action(self, state):
        if state.ndim < 2:
            state = state[np.newaxis, :]
        if not hasattr(self, "_get_noise_action"):
            raise RuntimeError("actor not well initialized")
        return self._get_noise_action(state)

    def get_actions(self, state):
        if not hasattr(self, "_get_actions"):
            raise RuntimeError("actor not well initialized")
        return self._get_actions(state)

    def get_noise_actions(self, state):
        if not hasattr(self, "_get_noise_actions"):
            raise RuntimeError("actor not well initialized")
        return self._get_noise_actions(state)

    def get_target_action(self, state):
        if state.ndim < 2:
            state = state[np.newaxis, :]
        if not hasattr(self, "_get_target_action"):
            raise RuntimeError("actor not well initialized")
        return self._get_target_action(state)

    def get_target_noise_action(self, state):
        if state.ndim < 2:
            state = state[np.newaxis, :]
        if not hasattr(self, "_get_target_noise_action"):
            raise RuntimeError("actor not well initialized")
        return self._get_target_noise_action(state)

    def get_target_actions(self, state):
        if not hasattr(self, "_get_target_actions"):
            raise RuntimeError("actor not well initialized")
        return self._get_target_actions(state)

    def get_target_noise_actions(self, state):
        if not hasattr(self, "_get_target_noise_actions"):
            raise RuntimeError("actor not well initialized")
        return self._get_target_noise_actions(state)

    def update_target(self, tau=None):
        tau = tau or self.tau
        if not hasattr(self, "_update_target"):
            raise RuntimeError("actor not well initialized")
        self._update_target(tau)

    def create_network(self, states, action_dim):
        raise RuntimeError("Not implemented, user should define its own")


class Critic(object):
    def __init__(self, batch_size, state_shape, action_shape=None, tau=0.99):
        self.tau = tau
        self.batch_size = batch_size
        self.states = T.Placeholder(
            (batch_size,) + state_shape, "float32", name="critic_states"
        )
        self.state = T.Placeholder((1,) + state_shape, "float32", name="critic_state")
        if action_shape:
            self.actions = T.Placeholder(
                (batch_size,) + action_shape, "float32", name="critic_actions"
            )
            self.action = T.Placeholder(
                (1,) + action_shape, "float32", name="critic_action"
            )

            with symjax.Scope("critic"):
                self.q_values = self.create_network(self.states, self.actions)
                self.q_value = self.q_values.clone(
                    {self.states: self.state, self.actions: self.action}
                )

            self._get_q_values = symjax.function(
                self.states, self.actions, outputs=self.q_values
            )
            self._get_noise_q_values = symjax.function(
                self.states, self.actions, outputs=self.q_values
            )
            self._get_q_value = symjax.function(
                self.state, self.action, outputs=self.q_value
            )
            self._get_noise_q_value = symjax.function(
                self.state, self.action, outputs=self.q_value
            )

            # now for the target
            with symjax.Scope("target_critic"):
                self.target_q_values = self.create_network(self.states, self.actions)
                self.target_q_value = self.target_q_values.clone(
                    {self.states: self.state, self.actions: self.action}
                )
            self._get_target_q_values = symjax.function(
                self.states, self.actions, outputs=self.target_q_values
            )
            self._get_target_noise_q_values = symjax.function(
                self.states, self.actions, outputs=self.target_q_values
            )
            self._get_target_q_value = symjax.function(
                self.state, self.action, outputs=self.target_q_value
            )
            self._get_target_noise_q_value = symjax.function(
                self.state, self.action, outputs=self.target_q_value
            )
        else:
            with symjax.Scope("critic"):
                self.q_values = self.create_network(self.states)
                self.q_value = self.q_values.clone({self.states: self.state})

            self._get_q_values = symjax.function(self.states, outputs=self.q_values)
            self._get_noise_q_values = symjax.function(
                self.states, outputs=self.q_values
            )
            self._get_q_value = symjax.function(self.state, outputs=self.q_value)
            self._get_noise_q_value = symjax.function(self.state, outputs=self.q_value)

            with symjax.Scope("target_critic"):
                self.target_q_values = self.create_network(self.states)
                self.target_q_value = self.target_q_values.clone(
                    {self.states: self.state}
                )

            self._get_target_q_values = symjax.function(
                self.states, outputs=self.target_q_values
            )
            self._get_target_noise_q_values = symjax.function(
                self.states, outputs=self.target_q_values
            )
            self._get_target_q_value = symjax.function(
                self.state, outputs=self.target_q_value
            )
            self._get_target_noise_q_value = symjax.function(
                self.state, outputs=self.target_q_value
            )

        self.params = symjax.get_variables(scope="*/critic", trainable=True)

        tau = T.Placeholder((), "float32")
        updates = {
            t: t * tau + a * (1 - tau)
            for t, a in zip(
                symjax.get_variables(scope="/target_critic/"),
                symjax.get_variables(scope="/critic/"),
            )
        }
        self._update_target = symjax.function(tau, updates=updates)
        self.update_target(0)

    def get_q_value(self, state, action=None):
        if state.ndim < 2:
            state = state[np.newaxis, :]
        if action:
            if action.ndim < 2:
                action = action[np.newaxis, :]
        if not hasattr(self, "_get_q_value"):
            raise RuntimeError("critic not well initialized")
        if action:
            return self._get_q_value(state)
        else:
            return self._get_q_value(state, action)

    def get_q_values(self, states, actions=None):
        if not hasattr(self, "_get_q_values"):
            raise RuntimeError("critic not well initialized")
        if actions:
            return self._get_q_values(states, actions)
        else:
            return self._get_q_values(states)

    def get_target_q_value(self, state, action=None):
        if state.ndim < 2:
            state = state[np.newaxis, :]
        if action:
            if action.ndim < 2:
                action = action[np.newaxis, :]
        if not hasattr(self, "_get_target_q_value"):
            raise RuntimeError("critic not well initialized")
        if action:
            return self._get_target_q_value(state)
        else:
            return self._get_target_q_value(state, action)

    def get_target_q_values(self, states, actions=None):
        if not hasattr(self, "_get_target_q_values"):
            raise RuntimeError("critic not well initialized")
        if actions is not None:
            return self._get_target_q_values(states, actions)
        else:
            return self._get_target_q_values(states)

    def update_target(self, tau=None):
        tau = tau or self.tau
        if not hasattr(self, "_update_target"):
            raise RuntimeError("critic not well initialized")
        self._update_target(tau)

    def create_network(self, states, actions=None):
        raise RuntimeError("Not implemented, user should define its own")