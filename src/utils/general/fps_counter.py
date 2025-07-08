from collections import deque

class FPSCounter:
    def __init__(self, max_buffer_seconds=1):
        self.frame_times = deque()
        self.max_buffer_seconds = max_buffer_seconds

    def accumulate_frame_time(self, timestamp):
        self.frame_times.append(timestamp)

        min_time = timestamp - self.max_buffer_seconds
        while self.frame_times and self.frame_times[0] < min_time:
            self.frame_times.popleft()

    def get_fps(self):
        num_frames = len(self.frame_times)
        if num_frames <= 1:
            return 0.0

        time_span = self.frame_times[-1] - self.frame_times[0]
        if time_span <= 0:
            return 0.0

        return num_frames / time_span