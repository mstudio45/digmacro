import collections
import time

class MovementTracker:
    def __init__(self, position_history_length: int = 10, velocity_history_length: int = 5):
        self.position_history = collections.deque(maxlen=position_history_length)
        self.velocity_history = collections.deque(maxlen=velocity_history_length)

        self._last_timestamp = None
        self._last_position = None

    def update(self, current_position_x: float):
        current_timestamp = time.monotonic()

        # add current position and timestamp to the history #
        self.position_history.append((current_timestamp, current_position_x))

        # calculate velocity #
        if self._last_timestamp is not None:
            time_delta = current_timestamp - self._last_timestamp
            if time_delta > 0:
                position_delta = current_position_x - self._last_position
                current_velocity = position_delta / time_delta
                self.velocity_history.append(current_velocity)

        self._last_timestamp = current_timestamp
        self._last_position = current_position_x

    def get_velocity(self) -> float:
        if len(self.position_history) < 2:
            return 0.0

        # unzip into two lists #
        timestamps, positions = zip(*self.position_history)

        total_time_delta = timestamps[-1] - timestamps[0]
        total_position_delta = positions[-1] - positions[0]

        if total_time_delta == 0:
            return 0.0

        return total_position_delta / total_time_delta

    def get_acceleration(self) -> float:
        if len(self.velocity_history) < 2:
            return 0.0

        return sum(self.velocity_history) / len(self.velocity_history)