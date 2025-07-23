import time
from typing import Callable, Tuple

def smooth_move_to(
    start_pos: Tuple[int, int],
    dest_x: int,
    dest_y: int,
    cursor_func: Callable[[int, int], None],
    steps: int = 13,
    delay: float = 0.001
) -> None:
    if steps == 1:
        return cursor_func(dest_x, dest_y)

    current_x, current_y = start_pos
    
    step_x = (dest_x - current_x) / steps
    step_y = (dest_y - current_y) / steps
    
    for i in range(1, steps + 1):
        new_x = int(current_x + (step_x * i))
        new_y = int(current_y + (step_y * i))
        
        cursor_func(new_x, new_y)
        time.sleep(delay)