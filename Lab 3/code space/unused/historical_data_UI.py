import subprocess
# Set ngrok authtoken
from flask import Flask, render_template
from pyngrok import ngrok
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import io

from congestion_calculation_control import CongestionCalculationControl, multi_code_stations

class HistoricalDataUI:
    def display_heatmap(self, hour):
        heatmap = CongestionCalculationControl()
        heatmap.congestion_percentage(hour)
        heatmap.get_heatmap()  # Return image buffer
        return "/static/congestion_heatmap.png"

    
# graph=HistoricalDataUI()
# graph.display_heatmap(5)