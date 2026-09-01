import csv
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine import ExecutionEngine

def export_session_data(engine: "ExecutionEngine", current_price: float, 
                        csv_filename: str = "trades.csv", 
                        json_filename: str = "summary.json"):
    """Writes detailed execution data and strategy metrics to CSV/JSON."""
    
    all_trades = list(engine.trade_history)
    if engine.active_trade:
        all_trades.append(engine.active_trade)

    with open(csv_filename, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Trade ID", "Side", "Status", "Exit Reason", "Entry Tick", 
            "Entry Price", "Exit Tick", "Exit Price", "Units", "Realized PnL"
        ])
        
        for trade in all_trades:
            status = "OPEN" if trade.is_open else "CLOSED"
            writer.writerow([
                trade.trade_id,
                trade.side,
                status,
                trade.exit_reason,
                trade.entry_tick,
                f"{trade.entry_price:.4f}",
                trade.exit_tick if trade.exit_tick is not None else "N/A",
                f"{trade.exit_price:.4f}" if trade.exit_price is not None else "N/A",
                trade.units,
                f"{trade.realized_pnl:.4f}"
            ])

    total_trades = len(engine.trade_history)
    winning_trades = sum(1 for t in engine.trade_history if t.realized_pnl > 0)
    losing_trades = sum(1 for t in engine.trade_history if t.realized_pnl < 0)
    even_trades = sum(1 for t in engine.trade_history if t.realized_pnl == 0)

    stop_loss_exits = sum(1 for t in engine.trade_history if t.exit_reason == "STOP_LOSS")
    time_exits = sum(1 for t in engine.trade_history if t.exit_reason == "TIME_EXIT")
    signal_exits = sum(1 for t in engine.trade_history if t.exit_reason == "SIGNAL")

    summary = {
        "starting_capital": engine.starting_capital,
        "ending_equity": round(engine.get_equity(current_price), 2),
        "total_realized_pnl": round(engine.realized_pnl, 2),
        "unrealized_pnl": round(engine.get_unrealized_pnl(current_price), 2),
        "metrics": {
            "total_completed_trades": total_trades,
            "win_rate_percent": round(engine.win_rate, 2),
            "wins": winning_trades,
            "losses": losing_trades,
            "breakeven": even_trades
        },
        "exit_breakdown": {
            "signal_exits": signal_exits,
            "stop_loss_exits": stop_loss_exits,
            "time_limit_exits": time_exits
        }
    }

    with open(json_filename, "w") as f:
        json.dump(summary, f, indent=4)

    print("\n================ SESSION EXPORT ================")
    print(f"  Trade Log:      {csv_filename}")
    print(f"  Summary Report: {json_filename}")
    print(f"  Final Equity:   ${summary['ending_equity']:.2f}")
    print(f"  Win Rate:       {summary['metrics']['win_rate_percent']}%")
    print(f"  Stop Losses:    {stop_loss_exits}")
    print(f"  Time Exits:     {time_exits}")
    print("================================================\n")