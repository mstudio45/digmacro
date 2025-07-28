from utils.OCR.stat_lib import StatLib, StatVisualType, StatVisualEnum, Layout
from variables import Variables

import datetime
import threading
import logging

class GameStatLib:
    def __init__(self, discord_bot):
        self.stat_util = StatLib(compact=True, layout=Layout.grid)
        self.discord_bot = discord_bot

    def calculate_hourly_average(self, cumulative_points): # list of current_money during a certain time, not earnings #
        interval_earnings = []
        for i in range(1, len(cumulative_points)):
            interval_earnings.append(cumulative_points[i] - cumulative_points[i - 1])
        
        return (sum(interval_earnings) / len(interval_earnings)) * 6 # average_per_interval * (60 minutes / 10 minutes) (bcs interval is 10 minutes) #

    def create_image(self, size=8):
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
        return self.stat_util.generate(visuals, size=size)
    
    # main loop #
    def run_information_loop(self, interval_str):
        def _thread():
            logging.info("Statistics loop started.")

            last_message_send = datetime.datetime.now()
            message_interval = datetime.timedelta(minutes={
                "1 Hour": 60, 
                "30 Minutes": 30, 
                "10 Minutes": 10
            }.get(interval_str, 30))

            update_interval = datetime.timedelta(minutes=10)
            last_update = datetime.datetime.now() - update_interval

            while Variables.is_running:
                current_money = 0
                try:
                    current_money = self.discord_bot.ocr_util.get_current_money()
                except Exception as e:
                    logging.warning(f"Error getting current money: {str(e)}")
                
                if current_money != 0:
                    # add money and send statistic notif #
                    time_now = datetime.datetime.now()

                    if time_now- last_update > update_interval:
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
            
            logging.info("Statistics loop ended.")
        threading.Thread(target=(_thread), daemon=True).start()