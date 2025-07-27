"""
Statlib by upio
very simple library for generating graphs

edited by mstudio45
"""

import enum
import io

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image
import cv2

import os
from variables import StaticVariables

class StatVisualEnum(enum.Enum):
    line_chart = "line"
    pie_chart = "pie"
    bar_chart = "bar"

class Layout(enum.Enum):
    grid = "grid"
    default = "default"

class StatLib:
    def __init__(self, layout: Layout = Layout.default, compact=True) -> None:
        self.compact = compact
        self.layout = layout

        plt.style.use(os.path.abspath(os.path.join(StaticVariables.rose_pine_lib_path, "rose-pine.mplstyle")))

    def generate(self, data: list, size: int = 5):
        right_charts = sum(isinstance(d, StatVisualType) and d.right for d in data)
        left_charts = sum(isinstance(d, StatVisualType) and not d.right for d in data)

        ncols = 2 if right_charts and left_charts else 1
        nrows = max(right_charts, left_charts, 1)

        fig = plt.figure(figsize=(size, size))
        spec = fig.add_gridspec(nrows=nrows, ncols=ncols)

        right_index = 0
        left_index = 0

        for item in data:
            if not isinstance(item, StatVisualType):
                continue

            col = 1 if item.right and ncols == 2 else 0
            row = right_index if item.right else left_index
            ax = fig.add_subplot(spec[row, col])

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
            fig.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close(fig)
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