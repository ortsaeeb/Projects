"""Offline tests for the Trade Guardian (no Webull connection). Run:  python test_guard.py"""
import sys, os, tempfile
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bot
bot.LOG_DIR = tempfile.mkdtemp()
bot.HERE = tempfile.mkdtemp()  # KILL file lives here during tests
clock = [None]
bot.now_ct = lambda: clock[0]
OCC = "QQQ260928C00744000"
PASS = []

class Fake:
    def __init__(self, path, held=1, cost=0.56, events=None, reject_stops=0, empty_at=(), zero_px=False,
                 status_raise_at=(), reject_sells=0):
        self.path, self.k, self.orders, self.n = path, 0, {}, 0
        self.held, self.cost, self.events = held, cost, events or {}
        self.reject_stops, self.empty_at, self.zero_px = reject_stops, set(empty_at), zero_px
        self.status_raise_at, self.reject_sells = set(status_raise_at), reject_sells
    def tick(self):
        self.k += 1
        for o in self.orders.values():
            if o["status"] == "SUBMITTED" and o["side"] == "SELL":
                bid = self.bid()
                if (o["stop"] is None or bid <= o["stop"]) and bid >= o["limit"] and bid > 0:
                    o.update(status="FILLED", px=bid); self.held -= o["qty"]
        ev = self.events.get(self.k)
        if ev: ev(self)
    def bid(self): return self.path[min(self.k, len(self.path) - 1)]
    def option_positions(self):
        if self.k in self.empty_at: return {}
        return {OCC: {"qty": self.held, "cost": self.cost}} if self.held > 0 else {}
    def option_quotes(self, occs): return {o: {"bid": self.bid(), "ask": self.bid() + 0.02} for o in occs}
    def balance(self): return {"total_net_liquidation_value": "160.00"}
    def place_option(self, occ, side, qty, limit, stop=None):
        live_sells = sum(o["qty"] for o in self.orders.values() if o["status"] == "SUBMITTED" and o["side"] == "SELL")
        if side == "SELL" and qty + live_sells > self.held: raise RuntimeError("HTTP 400 insufficient position")
        if stop and self.reject_stops > 0:
            self.reject_stops -= 1; raise RuntimeError("HTTP 400 order type not supported (simulated)")
        if not stop and self.reject_sells > 0:
            self.reject_sells -= 1; raise RuntimeError("HTTP 400 market closed (simulated)")
        self.n += 1; oid = f"o{self.n}"
        self.orders[oid] = dict(side=side, qty=qty, limit=limit, stop=stop, status="SUBMITTED", px=0)
        return oid
    def cancel(self, oid):
        if self.orders[oid]["status"] == "SUBMITTED": self.orders[oid]["status"] = "CANCELLED"
    def order_status(self, oid):
        if self.k in self.status_raise_at: raise RuntimeError("HTTP 503 (simulated)")
        o = self.orders[oid]
        return o["status"], (o["qty"] if o["status"] == "FILLED" else 0), (0 if self.zero_px else o["px"])
    def resting(self): return [o for o in self.orders.values() if o["status"] == "SUBMITTED"]

def run(F_, start="10:50", end="10:58", day=(2026, 9, 28)):
    global F; F = F_
    clock[0] = datetime(*day, *map(int, start.split(":")), tzinfo=bot.CT)
    cfg = {"risk": {"max_cost_per_trade": 50, "max_trades_per_day": 2, "max_daily_loss": 40,
                    "take_profit_pct": 0.8, "stop_loss_pct": 0.35, "flatten_time_ct": "14:50"},
           "poll_seconds": 5, "guard": {"end_time_ct": end}}
    lines = []
    orig = bot.log
    bot.log = lambda m: (lines.append(m), orig(m))
    try: bot.guard(F, bot.RiskState(cfg), cfg)
    finally: bot.log = orig
    return lines

def sleep(s):
    clock[0] += timedelta(seconds=s); F.tick()
bot.time.sleep = sleep

def check(name, cond):
    PASS.append(cond); print(("PASS " if cond else "FAIL ") + name)

L = run(Fake([0.56, 0.60, 0.70, 0.80, 0.95, 1.05, 1.30, 1.50, 1.80, 2.10, 2.40, 2.52, 2.40, 2.20, 2.00, 1.90, 1.85, 1.70, 1.60]))
check("1 runner: trails up and exits with profit", any("CLOSED" in l and "P/L $+1" in l for l in L) and not F.resting())

F2 = Fake([0.56] * 3 + [0.60] * 30, empty_at={3})
L = run(F2)
check("2 one empty positions reply does not drop the position", not any("CLOSED" in l for l in L) and len(F2.resting()) == 1)

F3 = Fake([0.56] * 40, reject_stops=1)
L = run(F3)
check("3 rejected stop is retried and ends up resting", any("rejected" in l for l in L) and len(F3.resting()) == 1
      and sum("PROTECTED" in l for l in L) == 1)

F4 = Fake([0.25] * 40, cost=0.56)
L = run(F4)
check("4 position found already under its stop is re-stopped, not dumped",
      any("already under its stop" in l for l in L) and not any("CLOSED" in l for l in L) and len(F4.resting()) == 1)

F5 = Fake([0.56, 0.50, 0.45, 0.40, 0.35, 0.30, 0.30], zero_px=True)
L = run(F5)
check("5 missing fill price falls back to a real price (no -$56 P/L)",
      any("CLOSED" in l for l in L) and not any("P/L $-56" in l for l in L))

F6 = Fake([0.56, 0.60, 0.70, 0.85, 0.90, 0.90, 0.90, 0.90, 0.90, 0.90, 0.90], status_raise_at={3, 4})
L = run(F6)
check("6 status API errors during a trail still end with a resting stop", len(F6.resting()) == 1)

def user_sell(f): f.held = 0
F7 = Fake([0.56, 0.60, 0.62, 0.65, 0.66, 0.66, 0.66], events={3: user_sell})
L = run(F7)
check("7 sold in the app: stop order cleaned up", any("sold in the app" in l for l in L) and not F7.resting())

F8 = Fake([0.56] * 60, reject_sells=5)
L = run(F8, start="14:49", end="14:57")
check("8 failed flatten is retried until sold", any("not filled" in l for l in L) and any("CLOSED" in l and "flatten" in l for l in L)
      and F8.held == 0)

def user_cancel(f):
    for o in f.orders.values():
        if o["status"] == "SUBMITTED": o["status"] = "CANCELLED"
F9 = Fake([0.56] * 30, events={2: user_cancel})
L = run(F9)
check("9 stop cancelled in the app is put back", any("was cancelled" in l for l in L) and len(F9.resting()) == 1)

# smart warnings: a far out-of-the-money midday re-entry after a loss
class FW(Fake):
    def stock_quote(self, sym): return {"price": 741.0}
def reopen(f): f.held = 1
FWn = FW([0.56, 0.45, 0.40, 0.36, 0.30, 0.30, 0.30, 0.30, 0.30, 0.30], events={6: reopen})
L = run(FWn, start="11:00", end="11:02")
check("12 warnings: midday + re-entry + far from the money",
      any("MIDDAY TRADE" in l for l in L) and any("RE-ENTRY" in l for l in L) and any("FAR FROM THE MONEY" in l for l in L))
FWq = FW([0.56] * 20)
L = run(FWq, start="09:00", end="09:01")
check("13 no warnings for a position found at startup in the morning", not any("MIDDAY" in l or "RE-ENTRY" in l for l in L))

# testorder: fake live broker that accepts, reports and cancels orders
class T(bot.Broker):
    def __init__(self, reject=False, hold=False):
        self.live, self.account, self.reject, self.hold, self.orders = True, "ACC123", reject, hold, {}
        me = self
        class OV2:
            def get_order_detail(_, acc, oid):
                class R:
                    status_code = 200
                    def json(_): return {"account_id": "ACC123", "orders": [{"status": me.orders[oid]}]}
                return R()
        class TR: order_v2 = OV2()
        self.trade = TR()
    def stock_quote(self, s): return {"price": 767.4}
    def option_quotes(self, occs): return {o: {"bid": 1.10, "ask": 1.12} for o in occs}
    def option_positions(self): return {"QQQ260928C00744000": {"qty": 1, "cost": 0.5}} if self.hold else {}
    def place_option(self, occ, side, qty, limit, stop=None):
        if self.reject: raise RuntimeError("HTTP 400 invalid order type")
        oid = f"t{len(self.orders)}"; self.orders[oid] = "SUBMITTED"; return oid
    def cancel(self, oid): self.orders[oid] = "CANCELLED"
    def order_status(self, oid): return self.orders[oid], 0, 0
clock[0] = datetime(2026, 9, 28, 8, 10, tzinfo=bot.CT)
lines = []; orig = bot.log; bot.log = lambda m: (lines.append(m), orig(m))
F = Fake([1]); bot.testorder(T(hold=True))
bot.log = orig
check("14 testorder places and cancels both test orders", any("TEST 1" in l and "PASSED" in l for l in lines)
      and any("TEST 2" in l and "PASSED" in l for l in lines) and not any("ACC123" in l for l in lines))
lines = []; bot.log = lambda m: (lines.append(m), orig(m))
bot.testorder(T(reject=True))
bot.log = orig
check("15 testorder reports a rejection clearly", any("FAILED" in l for l in lines))

# guard runs the order test itself once the market opens, and confirms the first real stop
class FL(Fake):
    live = True
    def stock_quote(self, sym): return {"price": 767.4 if sym == "SPY" else 741.0}
def buy(f): f.held = 1
FLn = FL([1.10] * 200, held=0, events={40: buy})
L = run(FLn, start="08:25", end="08:35")
check("16 guard: order test waits for 8:30, passes, and the first stop is confirmed",
      any("ORDER TEST PASSED" in l for l in L) and any("STOP ORDER CONFIRMED" in l for l in L)
      and not any("TEST 1" in l for l in L[:3]) and len(FLn.resting()) == 1)
FLr = FL([1.10] * 200, held=0, reject_sells=0); FLr.place_option = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("HTTP 400 bad order"))
L = run(FLr, start="08:29", end="08:32")
check("17 guard: a failed order test is reported and the guard keeps running",
      any("ORDER TEST FAILED" in l for l in L) and any("GUARD summary" in l for l in L))

# selling by hand: cancel the guard's stop in the app, then sell within the grace period
def cancel_then_sell(f):
    for o in f.orders.values():
        if o["status"] == "SUBMITTED": o["status"] = "CANCELLED"
    f.events[f.k + 3] = lambda g: setattr(g, "held", 0)
F18 = Fake([0.70] * 60, events={4: cancel_then_sell})
L = run(F18)
check("18 cancel the stop + sell by hand: guard waits, doesn't fight, cleans up",
      any("selling by hand" in l for l in L) and any("sold in the app" in l for l in L) and not F18.resting()
      and sum("PROTECTED" in l for l in L) == 1)

# a one-tick bid spike must not drag the stop up
F19 = Fake([0.56, 0.56, 0.85, 0.56, 0.57, 0.56, 0.58, 0.56] + [0.57] * 30)
L = run(F19)
check("19 one-tick spike ignored (no move to breakeven)", not any("TRAIL" in l for l in L))
F19b = Fake([0.56, 0.56, 0.85, 0.85, 0.86] + [0.86] * 30)
L = run(F19b)
check("19b a real move (two checks) still trails", any("TRAIL" in l for l in L))

# KILL file: yesterday's is removed, today's is obeyed
kill = os.path.join(bot.HERE, "KILL")
open(kill, "w").close(); t0 = datetime(2026, 9, 25, 12, 0).timestamp(); os.utime(kill, (t0, t0))
F20 = Fake([0.56] * 60); L = run(F20)
check("20 old KILL file from a previous day is removed", any("removed an old KILL" in l for l in L)
      and not os.path.exists(kill) and len(F20.resting()) == 1)
open(kill, "w").close()
t1 = datetime(2026, 9, 28, 10, 0, tzinfo=bot.CT).timestamp(); os.utime(kill, (t1, t1))
F20b = Fake([0.56] * 60); L = run(F20b)
check("20b today's KILL file is obeyed (position sold)", any("KILL file is present" in l for l in L) and F20b.held == 0)
os.remove(kill)

# only one guard at a time
LOCK = os.path.join(bot.LOG_DIR, "guard.lock")
def other_window_alive(f):  # the other window keeps writing the lock every 5s
    open(LOCK, "w").write(str(clock[0].timestamp()))
open(LOCK, "w").write(str(datetime(2026, 9, 28, 10, 49, 50, tzinfo=bot.CT).timestamp()))
real_tick = Fake.tick
Fake.tick = lambda self: (real_tick(self), other_window_alive(self))
F21 = Fake([0.56] * 20); L = run(F21)
Fake.tick = real_tick
check("21 a second guard window refuses to start", any("already running" in l for l in L) and not F21.orders)
if os.path.exists(LOCK): os.remove(LOCK)

# closed the window and restarted within 30s: the new one waits, then takes over
open(LOCK, "w").write(str(datetime(2026, 9, 28, 10, 49, 50, tzinfo=bot.CT).timestamp()))
F21b = Fake([0.56] * 20); L = run(F21b)
check("21b restarted right after closing: takes over after a short wait",
      not any("already running" in l for l in L) and len(F21b.resting()) == 1)

# a state file cut off mid-save (window closed at the wrong moment) doesn't stop the guard
st = os.path.join(bot.LOG_DIR, "state-2026-09-28.json")
keep = open(st).read() if os.path.exists(st) else None
open(st, "w").write('{"trades": 1, "real')
F21c = Fake([0.56] * 20); L = run(F21c)
check("21c damaged state file: guard still starts and protects", any("damaged" in l for l in L) and len(F21c.resting()) == 1)
if keep is not None: open(st, "w").write(keep)

# Webull partly down at 14:50: the same-day option still gets sold
F22 = Fake([0.56] * 300, status_raise_at=set(range(12, 400))); L = run(F22, start="14:45", end="14:56")
check("24 order-status calls failing: still sold at 14:50", F22.held == 0 and not any("guard error" in l for l in L))
class PosDown(Fake):
    def option_positions(self):
        if self.k >= 12: raise RuntimeError("HTTP 503 (simulated)")
        return super().option_positions()
F22b = PosDown([0.56] * 300); L = run(F22b, start="14:45", end="14:56")
check("24b positions call failing: still sold at 14:50", F22b.held == 0 and any("can't read positions" in l for l in L))
class QuotesDown(Fake):
    def option_quotes(self, occs):
        if self.k >= 12: raise RuntimeError("HTTP 503 (simulated)")
        return super().option_quotes(occs)
F22c = QuotesDown([0.56] * 300); L = run(F22c, start="14:45", end="14:56")
check("24c quotes failing: still sold at 14:50", F22c.held == 0)

# bought the same contract again right after the guard closed it: the new trade is protected
class Lag(Fake):
    lag = 1
    def option_positions(self):
        if self.held == 0 and self.lag > 0:
            self.lag -= 1; return {OCC: {"qty": 1, "cost": self.cost}}
        return super().option_positions()
def kill_on(f): open(kill, "w").close()
def kill_off_rebuy(f): os.remove(kill); f.held, f.cost = 1, 0.60
F23 = Lag([0.56] * 300, events={6: kill_on, 9: kill_off_rebuy}); L = run(F23, start="10:50", end="10:55")
check("25 re-bought right after a close: new trade protected",
      any("NEW POSITION" in l and "0.60" in l for l in L) and len(F23.resting()) == 1)

# cost reported per contract (56.00) instead of per share (0.56): not dumped
def add_one(f):  # buy a 2nd contract at 0.60: Webull's average cost becomes 58.00 (per contract)
    for o in f.orders.values():
        if o["status"] == "SUBMITTED": o["status"] = "CANCELLED"
    f.held, f.cost = 2, 58.0
F26 = Fake([0.56] * 60, cost=56.0, events={10: add_one}); L = run(F26)
check("26 per-contract cost is caught, trade kept and protected (also after adding a contract)",
      F26.held == 2 and len(F26.resting()) == 1 and 0.40 < F26.resting()[0]["stop"] < 0.58
      and any("per-contract" in l for l in L) and any("-> 2" in l for l in L))

# early close day (day after Thanksgiving): same-day options out at 11:50 CT
OCC_SAVE = OCC
OCC = "QQQ261127C00744000"
F22 = Fake([0.56] * 200); L = run(F22, start="11:45", end="23:00", day=(2026, 11, 27))
check("22 early close: flattened at 11:50 and guard stops at 12:00", any("EARLY CLOSE" in l for l in L)
      and any("CLOSED" in l and "11:50" in l for l in L) and F22.held == 0)
OCC = OCC_SAVE

# the order test uses a contract at least a week out
lines = []; bot.log = lambda m: (lines.append(m), orig(m))
clock[0] = datetime(2026, 9, 28, 8, 40, tzinfo=bot.CT)
bot.testorder(T())
bot.log = orig
occ_used = [l.split()[7] for l in lines if "placing BUY" in l][0]
check("23 order test contract expires 7+ days out", bot.parse_occ(occ_used)[1] >= datetime(2026, 10, 5).date())

# option_positions parsing with the real Webull JSON shape (from the account, Friday)
raw = [{"currency":"USD","quantity":"1","cost":"56.00","legs":[{"symbol":"QQQ","cost":"0.56","instrument_type":"OPTION",
        "option_type":"CALL","option_expire_date":"2026-09-25","option_exercise_price":"744"}],"symbol":"QQQ",
        "option_strategy":"SINGLE","instrument_type":"OPTION","cost_price":"0.56"},
       {"currency":"USD","quantity":"-1","legs":[{"symbol":"SPY","instrument_type":"OPTION","option_type":"PUT",
        "option_expire_date":"2026-09-25","option_exercise_price":"765"}],"instrument_type":"OPTION","cost_price":"0.40"},
       {"currency":"USD","quantity":"3","symbol":"INTC","instrument_type":"STOCK","cost_price":"20.1"}]
class P(bot.Broker):
    def __init__(self): pass
    def positions(self): return raw
got = P().option_positions()
check("10 positions parsed; short and stock rows ignored", got == {"QQQ250925C00744000".replace("25","26",1): {"qty": 1, "cost": 0.56}})
print(got)
check("11 tick rounding", bot.tick_down("SPY260928C00744000", 3.27) == 3.27 and bot.tick_down("INTC260928C00030000", 3.27) == 3.25)
print(f"\n{sum(PASS)}/{len(PASS)} passed")
sys.exit(0 if all(PASS) else 1)
