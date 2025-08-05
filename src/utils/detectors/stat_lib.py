## STATLIB BY upio, modified by mstudio45 ##

import os
import enum
import io
import platform

import numpy as np
import cv2

from PIL import Image
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt
if platform.system() == "Darwin": matplotlib.use("MacOSX")

from variables import Variables, StaticVariables

class StatVisualEnum(enum.Enum):
    line_chart = "line"
    pie_chart = "pie"
    bar_chart = "bar"

class Layout(enum.Enum):
    grid = "grid"
    default = "default"

class StatLib:
    def __init__(self, layout: Layout = Layout.default, compact=True, size=5) -> None:
        self.compact = compact
        self.layout = layout
        self.stopped = False

        plt.style.use(os.path.abspath(os.path.join(StaticVariables.rose_pine_lib_path, "rose-pine.mplstyle")))
        self.fig = plt.figure(figsize=(size, size))

    def stop(self):
        if self.stopped: return
        self.stopped = True
        plt.close(self.fig)

    def generate(self, data):
        right_charts = sum(isinstance(d, StatVisualType) and d.right for d in data)
        left_charts = sum(isinstance(d, StatVisualType) and not d.right for d in data)

        ncols = 2 if right_charts and left_charts else 1
        nrows = max(right_charts, left_charts, 1)
        
        self.fig.clear() # clear current figure #
        spec = self.fig.add_gridspec(nrows=nrows, ncols=ncols)

        right_index = 0
        left_index = 0

        for item in data:
            if not isinstance(item, StatVisualType):
                continue

            col = 1 if item.right and ncols == 2 else 0
            row = right_index if item.right else left_index
            ax = self.fig.add_subplot(spec[row, col])

            if item.type == StatVisualEnum.line_chart:
                ax.set_title(item.title)
                ax.set_xlabel(item.data["x"]["label"])
                ax.set_ylabel(item.data["y"]["label"])

                x = np.array(item.data["x"]["data"])
                y = np.array(item.data["y"]["data"])
                ax.plot(x, y, color=item.color)

            elif item.type == StatVisualEnum.pie_chart:
                ax.set_title(item.title)
                pie_args = {
                    "labels": item.data["labels"],
                    "colors": item.data["colors"],
                    "autopct": '%1.1f%%',
                    "shadow": True,
                    "startangle": 90
                }
                if item.explode:
                    pie_args["explode"] = item.explode
                ax.pie(item.data["data"], **pie_args)

                if item.legend.get("on", False):
                    df = pd.DataFrame({
                        "labels": item.data["labels"],
                        "values": item.data["data"]
                    })
                    percent = 100. * df["values"] / df["values"].sum()
                    labels = [f"{i} - {j:.1f}%" for i, j in zip(df["labels"], percent)]
                    ax.legend(labels=labels, title=item.legend.get("title", ""), loc='upper left', bbox_to_anchor=(0.85, 1))
            
            elif item.type == StatVisualEnum.bar_chart:
                ax.set_title(item.title)
                ax.set_xlabel(item.data["x"]["label"])
                ax.set_ylabel(item.data["y"]["label"])

                x = item.data["x"]["data"]
                y = item.data["y"]["data"]
                ax.bar(x, y, color=item.color)

            if item.right:
                right_index += 1
            else:
                left_index += 1

        if self.compact:
            self.fig.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        self.fig.clear() # clear instead of close #
        buf.seek(0)

        img = Image.open(buf)
        return cv2.cvtColor(np.array(img, dtype=np.uint8), cv2.COLOR_RGBA2BGR)
        
class StatVisualType:
    def __init__(self, type, right: bool, data: dict, title: str, color:str="#ff5555", explode=None, legend:dict={"on":False}) -> None:
        self.type = type
        self.right = right
        self.explode = explode
        self.legend = legend
        self.data = data
        self.title = title
        self.color = color

############# CODE FOR THE MACRO DOWN BELOW #############

import datetime
import threading
import logging
import mss

class GameStatLib:
    def __init__(self, discord_bot):
        self.stat_util = StatLib(compact=True, layout=Layout.grid, size=8)
        self.discord_bot = discord_bot

    def calculate_hourly_average(self, cumulative_points): # list of current_money during a certain time, not earnings #
        try:
            interval_earnings = []
            for i in range(1, len(cumulative_points)):
                interval_earnings.append(cumulative_points[i] - cumulative_points[i - 1])
            
            return (sum(interval_earnings) / len(interval_earnings)) * 6 # average_per_interval * (60 minutes / 10 minutes) (bcs interval is 10 minutes) #
        except ZeroDivisionError:
            return 0

    def create_image(self):
        visuals = []

        # money line chart #
        money_array = Variables.money_information
        if len(money_array) > 0:
            money_points = [entry["money"] for entry in money_array]
            hourly_avg = self.calculate_hourly_average(money_points)

            first_money = money_points[0]
            last_money = money_points[-1]
            earned = round(last_money - first_money)

            start_time = money_array[0]["timestamp"]
            end_time = money_array[-1]["timestamp"]

            # format #
            time_points_str = [str(entry["timestamp"]) for entry in money_array]
            start_time_str = start_time.strftime("%H:%M:%S")
            end_time_str = end_time.strftime("%H:%M:%S")

            visuals.append(StatVisualType(
                type=StatVisualEnum.line_chart,
                right=False,
                data={
                    "x": {
                        "data": time_points_str,
                        "label": "Time"
                    },
                    "y": {
                        "data": money_points,
                        "label": "Money"
                    }
                },
                title=(
                    f"Money ({start_time_str} → {end_time_str}) | "
                    f"Earned: {int(earned):,} | "
                    f"Hourly Average: {int(hourly_avg):,}"
                ),
                color="#a4ff8b"
            ))
        
        # stats bar chart #
        dig_count, failed_minigame_attempts, rejoin_count, failed_rejoin_attempts = Variables.dig_count, Variables.failed_minigame_attempts, Variables.rejoin_count, Variables.failed_rejoin_attempts

        visuals.append(StatVisualType(
            type=StatVisualEnum.bar_chart,
            right=False,
            data={
                "x": {
                    "data": [
                        f"Dig Count ({dig_count:,})",
                        f"Failed Minigames ({failed_minigame_attempts:,})",
                        f"Rejoin Count ({rejoin_count:,})",
                        f"Failed Rejoins ({failed_rejoin_attempts:,})"
                    ],
                    "label": "Action Type"
                },
                "y": {
                    "data": [
                        dig_count, 
                        failed_minigame_attempts, 
                        rejoin_count, 
                        failed_rejoin_attempts
                    ],
                    "label": "Count"
                }
            },
            title="Stats Summary",
            color=["#10b981", "#ef4444", "#6366f1", "#ef4444"]
        ))
        
        # generate bar chart #
        return self.stat_util.generate(visuals)
    
    # main loop #
    def run_information_loop(self, interval_str):
        def _thread():
            logging.info("Statistics loop started.")

            last_message_send = datetime.datetime.now()
            message_interval = datetime.timedelta(minutes={
                "1 hour": 60, 
                "30 minutes": 30, 
                "10 minutes": 10
            }.get(interval_str, 30))

            update_interval = datetime.timedelta(minutes=10)
            last_update = datetime.datetime.now() - update_interval
            
            sct = mss.mss()
            while Variables.is_running:
                current_money = 0
                try:
                    current_money = self.discord_bot.ocr_util.get_current_money(sct)
                except Exception as e:
                    logging.warning(f"Error getting current money: {str(e)}")
                
                if current_money != 0:
                    # add money and send statistic notif #
                    time_now = datetime.datetime.now()

                    if time_now - last_update > update_interval:
                        logging.info(f"Updated money information array. Current Money: {current_money:,}")
                        Variables.money_information.append({ "timestamp": datetime.time(hour=time_now.hour, minute=time_now.minute, second=time_now.second), "money": current_money })
                        last_update = time_now

                    if time_now - last_message_send > message_interval:
                        try:
                            self.discord_bot.send_statistic_embed()
                            last_message_send = time_now
                        except Exception as e:
                            logging.warning(f"Error sending statistic image: {str(e)}")

                if Variables.sleep(15, 1): break
            
            del sct
            logging.info("Statistics loop ended.")
        threading.Thread(target=(_thread), daemon=True).start()