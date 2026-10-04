"""Morning levels for the brief: floor pivots from the prior regular session + premarket range + gap.

Usage:  python tools/morning_levels.py SYMBOL PREV_HIGH PREV_LOW PREV_CLOSE [PM_HIGH PM_LOW PM_LAST]
Example: python tools/morning_levels.py QQQ 744.67 736.25 742.03 753.07 745.70 751.87
"""
import sys


def levels(h, l, c):
    p = (h + l + c) / 3
    return {"R3": h + 2 * (p - l), "R2": p + (h - l), "R1": 2 * p - l, "P": p,
            "S1": 2 * p - h, "S2": p - (h - l), "S3": l - 2 * (h - p)}


if __name__ == "__main__":
    sym, *nums = sys.argv[1:]
    h, l, c = map(float, nums[:3])
    lv = levels(h, l, c)
    print(f"{sym} pivots (from prior session H {h:.2f} L {l:.2f} C {c:.2f}):")
    print("  " + "  ".join(f"{k} {v:.2f}" for k, v in lv.items()))
    if len(nums) >= 6:
        ph, pl, last = map(float, nums[3:6])
        gap = (last / c - 1) * 100
        print(f"  premarket high {ph:.2f}  low {pl:.2f}  last {last:.2f}  gap {gap:+.2f}%"
              f"{'  (BIG GAP: expect stretched RSI at the open)' if abs(gap) >= 0.5 else ''}")
        above = sorted((v, k) for k, v in lv.items() if v > last)
        below = sorted(((v, k) for k, v in lv.items() if v < last), reverse=True)
        if above:
            print(f"  next level up: {above[0][1]} {above[0][0]:.2f} (+{above[0][0] - last:.2f})")
        if below:
            print(f"  next level down: {below[0][1]} {below[0][0]:.2f} (-{last - below[0][0]:.2f})")
