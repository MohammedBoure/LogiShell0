# 🦁 Albion Market Nexus

**Albion Market Nexus** is a professional desktop application designed for *Albion Online* traders. It helps you find profitable trade routes, arbitrage opportunities, and high-ROI items using real-time data from the *Albion Data Project*.

![Version](https://img.shields.io/badge/Version-8.0-blue) ![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)

## 🚀 Features

* **Global Arbitrage:** Automatically finds the best "Buy Low, Sell High" deals across all Royal Cities.
* **Route Scanner:** Targeted analysis between specific cities (e.g., Martlock → Caerleon).
* **Smart Filters:** Filter results by **Net Profit**, **ROI %**, **Item Weight**, and **Max Budget**.
* **Real-time Dashboard:** Live search and sort capabilities without re-scanning.
* **Data Export:** Save your findings to `CSV` for further analysis in Excel.
* **Professional UI:** Dark-themed, responsive interface built with PySide6.

## 🛠️ Prerequisites

You need **Python 3** installed. Then, install the required libraries:

```bash
pip install PySide6 requests
```

## 📦 Installation & Usage

1.  Download the script (`main.py`) to a folder.
2.  Run the application via terminal/command prompt:

    ```bash
    python main.py
    ```

### First Run:

*   The app will automatically download the latest `items.json` database (approx. 5-10 MB).

### Start Trading:

1.  Select your strategy (Global or Route).
2.  Click `START SCAN`.
3.  Use the dashboard filters to find the best items.

## 📊 How to Read the Data

| Column      | Description                                                    |
| :---------- | :------------------------------------------------------------- |
| Item Name   | The in-game name of the item (e.g., Adept's Bag).              |
| Net Profit  | Profit after deducting the 6% market tax.                      |
| Weight      | The item's weight in kg (crucial for transport).               |
| Prof/Wgt    | Profit per Weight. The higher this number, the better for transport mounts. |
| ROI %       | Return on Investment. Higher % means safer investment.         |

## ⚠️ Disclaimer

This tool relies on the Albion Online Data Project. Market data is crowdsourced and depends on players running the Albion Data Client. Prices may vary slightly from the live game server.