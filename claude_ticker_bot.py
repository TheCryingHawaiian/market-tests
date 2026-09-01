# market_sim.py
# A simple market price simulator with a live chart, buy/sell signals,
# and a profit/loss tracker.
#
# HOW TO INSTALL:  pip install matplotlib
# HOW TO RUN:      python market_sim.py
# STOP:            close the chart window

import random
import matplotlib.pyplot as plt
import matplotlib.animation as animation


# ------------------------------------------------------------------
# SETTINGS - change these numbers to adjust how the program behaves
# ------------------------------------------------------------------

STARTING_PRICE   = 100.0   # the first price value
VOLATILITY       = 0.5     # how much the price jumps each tick (bigger = more jumpy)
SIGNAL_LOOKBACK  =3        # how many consecutive rises/falls trigger a signal
MAX_PRICES_SHOWN = 100     # how many prices to show on the chart at once
REFRESH_MS       = 500     # how often the chart updates, in milliseconds
UNITS_PER_TRADE  = 1       # how many units are bought or sold on each signal


# ------------------------------------------------------------------
# PRICE STORAGE
# These plain lists hold all the data we need.
# ------------------------------------------------------------------

all_prices = []   # every price value, in order
all_ticks  = []   # the tick number for each price (1, 2, 3 ...)

# These lists store the tick and price for every BUY and SELL signal.
# We use them to draw the green and red dots on the chart.
buy_ticks   = []   # x positions of BUY signals
buy_prices  = []   # y positions of BUY signals
sell_ticks  = []   # x positions of SELL signals
sell_prices = []   # y positions of SELL signals

current_tick   = 0
current_price  = STARTING_PRICE
current_signal = "HOLD"


# ------------------------------------------------------------------
# TRADE TRACKER
#
# We need to remember whether we currently hold a position or not,
# and at what price we bought/sold into it.
#
# position = "NONE"  means we are not in any trade right now
# position = "LONG"  means we bought and are waiting to sell
# position = "SHORT" means we sold and are waiting to buy back
#
# entry_price is the price we paid when we opened the current trade.
# realised_pnl is the total profit/loss from all completed trades so far.
# ------------------------------------------------------------------

position      = "NONE"   # current position: "NONE", "LONG", or "SHORT"
entry_price   = 0.0      # price when we entered the current trade
realised_pnl  = 0.0      # total profit/loss from closed trades


def update_trades(signal, price):
    # This function looks at the new signal and decides whether to open,
    # close, or flip a trade. It updates the trade tracker variables.

    global position, entry_price, realised_pnl

    # ----- BUY signal received -----
    if signal == "BUY":

        if position == "NONE":
            # We have no trade open, so open a LONG (buy) trade
            position    = "LONG"
            entry_price = price
            print("  --> OPENED LONG at", price)

        elif position == "SHORT":
            # We were short (sold), so close that trade first, then go long
            # Profit on a short = entry price - current price (we sold high, buy back low)
            trade_profit = (entry_price - price) * UNITS_PER_TRADE
            realised_pnl = realised_pnl + trade_profit
            print("  --> CLOSED SHORT at", price, " | Trade P&L:", round(trade_profit, 4), " | Total P&L:", round(realised_pnl, 4))

            # Now open a new long trade
            position    = "LONG"
            entry_price = price
            print("  --> OPENED LONG at", price)

        # If we already have a LONG open, do nothing - we are already in the right direction

    # ----- SELL signal received -----
    elif signal == "SELL":

        if position == "NONE":
            # We have no trade open, so open a SHORT (sell) trade
            position    = "SHORT"
            entry_price = price
            print("  --> OPENED SHORT at", price)

        elif position == "LONG":
            # We were long (bought), so close that trade first, then go short
            # Profit on a long = current price - entry price (we bought low, sell high)
            trade_profit = (price - entry_price) * UNITS_PER_TRADE
            realised_pnl = realised_pnl + trade_profit
            print("  --> CLOSED LONG at", price, " | Trade P&L:", round(trade_profit, 4), " | Total P&L:", round(realised_pnl, 4))

            # Now open a new short trade
            position    = "SHORT"
            entry_price = price
            print("  --> OPENED SHORT at", price)

        # If we already have a SHORT open, do nothing - we are already in the right direction


def get_unrealised_pnl(price):
    # This calculates how much the open trade is currently worth,
    # even though we haven't closed it yet (so it hasn't been "banked").
    # This number changes every tick as the price moves.

    if position == "LONG":
        # We bought, so we profit if price has risen since we bought
        return (price - entry_price) * UNITS_PER_TRADE

    elif position == "SHORT":
        # We sold, so we profit if price has fallen since we sold
        return (entry_price - price) * UNITS_PER_TRADE

    else:
        # No open trade, so no unrealised profit or loss
        return 0.0


# ------------------------------------------------------------------
# FUNCTION: get the next price
#
# This is the only function you need to change if you want to use
# real market data instead of random numbers.
# Just replace the code inside with an API call that returns a number.
# ------------------------------------------------------------------

def get_next_price():
    global current_price

    # Move the price up or down by a small random amount
    change = random.gauss(0, VOLATILITY)
    current_price = current_price + change

    # Make sure the price never goes below 0.01
    if current_price < 0.01:
        current_price = 0.01

    return round(current_price, 4)

    # --- TO USE REAL DATA INSTEAD, DELETE EVERYTHING ABOVE AND DO THIS: ---
    # import requests
    # response = requests.get("https://your-broker-api.com/price/EURUSD")
    # return response.json()["bid"]


# ------------------------------------------------------------------
# FUNCTION: work out the trading signal
#
# Looks at the last few prices and checks if they all went up or down.
# Returns "BUY", "SELL", or "HOLD".
# ------------------------------------------------------------------

def get_signal():
    # We need enough prices before we can check for a run of ups or downs
    if len(all_prices) < SIGNAL_LOOKBACK + 1:
        return "HOLD"

    # Grab just the last few prices we need to look at
    recent_prices = all_prices[-(SIGNAL_LOOKBACK + 1):]

    all_went_up   = True
    all_went_down = True

    for i in range(1, len(recent_prices)):
        if recent_prices[i] <= recent_prices[i - 1]:
            all_went_up = False
        if recent_prices[i] >= recent_prices[i - 1]:
            all_went_down = False

    if all_went_up:
        return "BUY"
    if all_went_down:
        return "SELL"
    return "HOLD"


# ------------------------------------------------------------------
# SET UP THE CHART
# ------------------------------------------------------------------

fig, ax = plt.subplots(figsize=(12, 5))

line, = ax.plot([], [], color="royalblue", linewidth=1.5)

# Create empty scatter plots for the buy and sell dots.
# We will fill them with data each tick, just like the price line.
buy_dots,  = ax.plot([], [], marker="o", color="green", linestyle="None", markersize=8, label="BUY",  zorder=5)
sell_dots, = ax.plot([], [], marker="o", color="red",   linestyle="None", markersize=8, label="SELL", zorder=5)
# zorder=5 makes the dots draw on top of the price line

ax.legend(loc="upper right")
ax.set_xlabel("Tick number")
ax.set_ylabel("Price")
ax.set_title("Market Price Simulator")

# Text label in the top-left: shows price, signal, and P&L
label = ax.text(
    0.01, 0.97,
    "",
    transform=ax.transAxes,
    fontsize=12,
    verticalalignment="top",
    fontfamily="monospace"
)


# ------------------------------------------------------------------
# FUNCTION: update the chart (called automatically every REFRESH_MS)
# ------------------------------------------------------------------

def update_chart(frame):
    global current_tick, current_signal

    # Step 1: get a new price
    price = get_next_price()

    # Step 2: store it
    current_tick = current_tick + 1
    all_prices.append(price)
    all_ticks.append(current_tick)

    # Step 3: work out the signal
    current_signal = get_signal()

    # Step 4: update trades based on the signal
    update_trades(current_signal, price)

    # Step 4b: if a signal fired this tick, record the position for the dot
    if current_signal == "BUY":
        buy_ticks.append(current_tick)
        buy_prices.append(price)
    elif current_signal == "SELL":
        sell_ticks.append(current_tick)
        sell_prices.append(price)

    # Step 5: calculate unrealised P&L on any open trade
    unrealised = get_unrealised_pnl(price)
    total_pnl  = realised_pnl + unrealised   # total = banked + open trade value

    # Step 6: print a summary line to the terminal
    print("Tick:", current_tick,
          " | Price:", price,
          " | Signal:", current_signal,
          " | Position:", position,
          " | Realised:", round(realised_pnl, 2),
          " | Unrealised:", round(unrealised, 2),
          " | Total P&L:", round(total_pnl, 2))

    # Step 7: update the chart line
    visible_prices = all_prices[-MAX_PRICES_SHOWN:]
    visible_ticks  = all_ticks[-MAX_PRICES_SHOWN:]

    line.set_data(visible_ticks, visible_prices)

    # Only show dots that fall within the visible tick window
    oldest_visible_tick = visible_ticks[0]
    newest_visible_tick = visible_ticks[-1]

    # Filter buy dots to only those currently on screen
    visible_buy_ticks  = []
    visible_buy_prices = []
    for i in range(len(buy_ticks)):
        if oldest_visible_tick <= buy_ticks[i] <= newest_visible_tick:
            visible_buy_ticks.append(buy_ticks[i])
            visible_buy_prices.append(buy_prices[i])

    # Filter sell dots to only those currently on screen
    visible_sell_ticks  = []
    visible_sell_prices = []
    for i in range(len(sell_ticks)):
        if oldest_visible_tick <= sell_ticks[i] <= newest_visible_tick:
            visible_sell_ticks.append(sell_ticks[i])
            visible_sell_prices.append(sell_prices[i])

    buy_dots.set_data(visible_buy_ticks, visible_buy_prices)
    sell_dots.set_data(visible_sell_ticks, visible_sell_prices)

    ax.set_xlim(visible_ticks[0], visible_ticks[-1] + 1)

    lowest  = min(visible_prices)
    highest = max(visible_prices)
    padding = max((highest - lowest) * 0.1, 0.5)
    ax.set_ylim(lowest - padding, highest + padding)

    # Step 8: pick a colour for the label based on the signal
    if current_signal == "BUY":
        colour = "green"
    elif current_signal == "SELL":
        colour = "red"
    else:
        colour = "grey"

    # Step 9: update the on-chart text label
    # Show a + or - sign in front of the P&L numbers so it's easy to read
    if total_pnl >= 0:
        total_pnl_text = "+" + str(round(total_pnl, 2))
    else:
        total_pnl_text = str(round(total_pnl, 2))

    if unrealised >= 0:
        unrealised_text = "+" + str(round(unrealised, 2))
    else:
        unrealised_text = str(round(unrealised, 2))

    label.set_text(
        "Price:       " + str(price)          + "\n" +
        "Signal:      " + current_signal       + "\n" +
        "Position:    " + position             + "\n" +
        "Unrealised:  " + unrealised_text      + "\n" +
        "Total P&L:   " + total_pnl_text
    )
    label.set_color(colour)


# ------------------------------------------------------------------
# START THE PROGRAM
# ------------------------------------------------------------------

print("Market simulator starting. Close the chart window to stop.")
print("Signal triggers after", SIGNAL_LOOKBACK, "consecutive moves in the same direction.")
print()

ani = animation.FuncAnimation(
    fig,
    update_chart,
    interval=REFRESH_MS,
    cache_frame_data=False
)

plt.tight_layout()
plt.show()