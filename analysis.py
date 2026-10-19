"""Reproduce the main results: SPBE (digital government) scores of Indonesian
regencies and cities, 2021 vs 2024. Run: python analysis.py
Needs pandas, numpy, matplotlib. Writes results.txt and figures/*.png."""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

df = pd.read_csv("data/spbe_regions_2021_2024.csv")
df["java"] = df.province_2024.str.contains("Jawa|Banten|Yogyakarta|Jakarta").astype(int)
df["kota"] = (df.type == "Kota").astype(int)
df["log_pop"] = np.log(df.pop_2021_thousand)

# Regencies and cities scored in both years. A 2021 score of exactly 1.00 looks
# like a floor / not assessed, so those are dropped.
kk = df[(df.type != "Provinsi") & df.spbe_2021.notna() & df.spbe_2024.notna() & (df.spbe_2021 > 1.0)]
cols = ["spbe_2021", "hdi_2021", "poverty_2021", "log_pop", "kota", "java", "internet_2021"]
d = kk.dropna(subset=cols + ["change_2021_2024"]).copy()

out = []
def p(s=""): out.append(s); print(s)

def ols(y, X, groups=None, title=""):
    X1 = np.column_stack([np.ones(len(X)), X.values]); n, k = X1.shape
    b = np.linalg.lstsq(X1, y, rcond=None)[0]; e = y - X1 @ b
    XtXi = np.linalg.inv(X1.T @ X1)
    if groups is None:  # HC1 robust
        meat = (X1.T * e**2) @ X1; adj = n / (n - k)
    else:  # clustered by province
        meat = np.zeros((k, k))
        for g in np.unique(groups):
            s = X1[groups == g].T @ e[groups == g]; meat += np.outer(s, s)
        G = len(np.unique(groups)); adj = G / (G - 1) * (n - 1) / (n - k)
    se = np.sqrt(np.diag(XtXi @ meat @ XtXi * adj))
    r2 = 1 - e @ e / ((y - y.mean()) @ (y - y.mean()))
    p(f"== {title}  n={n}  R2={r2:.3f}")
    for nm, bb, s in zip(["const"] + list(X.columns), b, se):
        p(f"  {nm:15s} {bb:8.3f}  se {s:6.3f}  t {bb/s:6.2f}{'  *' if abs(bb/s) > 1.96 else ''}")
    p()

p("SPBE regencies and cities scored in 2021 and 2024")
p(f"n = {len(kk)} (descriptives), n = {len(d)} (regressions)")
p(f"Mean score: 2021 {kk.spbe_2021.mean():.2f}, 2024 {kk.spbe_2024.mean():.2f}")
p(f"Share that improved: {(kk.change_2021_2024 > 0).mean():.0%}")
p(f"Coefficient of variation: 2021 {kk.spbe_2021.std()/kk.spbe_2021.mean():.2f}, 2024 {kk.spbe_2024.std()/kk.spbe_2024.mean():.2f}")
g = kk.groupby("java")[["spbe_2021", "spbe_2024"]].mean()
p(f"Java minus outside Java (raw means): 2021 {g.loc[1,'spbe_2021']-g.loc[0,'spbe_2021']:.2f}, 2024 {g.loc[1,'spbe_2024']-g.loc[0,'spbe_2024']:.2f}")
p()
ols(d.change_2021_2024.values, d[cols], d.province_2024.values,
    "Change 2021-2024, SE clustered by province")
ols(d.spbe_2024.values, d[["hdi_2024", "poverty_2024", "log_pop", "kota", "java", "internet_2024"]],
    d.province_2024.values, "Level 2024, SE clustered by province")
open("results.txt", "w").write("\n".join(out) + "\n")

# Figure 1: Java gap, 2021 vs 2024
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(6, 4.2))
for j, c, lab in [(1, "#1f5fa8", "Java"), (0, "#d9822b", "Outside Java")]:
    ax.plot([2021, 2024], [g.loc[j, "spbe_2021"], g.loc[j, "spbe_2024"]], "o-", color=c, lw=2.5, ms=8)
    ax.text(2024.12, g.loc[j, "spbe_2024"], f"{lab} {g.loc[j,'spbe_2024']:.2f}", va="center", color=c)
    ax.text(2020.88, g.loc[j, "spbe_2021"], f"{g.loc[j,'spbe_2021']:.2f}", va="center", ha="right", color=c)
ax.set_xticks([2021, 2024]); ax.set_xlim(2020.4, 2025.3); ax.set_ylabel("Mean SPBE index (1-5)")
ax.set_title("Both groups improved, but the Java gap grew", loc="left")
fig.tight_layout(); fig.savefig("figures/fig1_java_gap.png", dpi=200)

# Figure 2: catch-up scatter
fig, ax = plt.subplots(figsize=(6, 4.2))
for j, c, lab in [(0, "#d9822b", "Outside Java"), (1, "#1f5fa8", "Java")]:
    s = kk[kk.java == j]
    ax.scatter(s.spbe_2021, s.change_2021_2024, s=14, alpha=.6, color=c, label=lab)
ax.axhline(0, color="#888", lw=.8)
ax.set_xlabel("SPBE index 2021"); ax.set_ylabel("Change 2021 to 2024")
ax.set_title("Low starters gained most (catch-up)", loc="left"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig("figures/fig2_catch_up.png", dpi=200)
