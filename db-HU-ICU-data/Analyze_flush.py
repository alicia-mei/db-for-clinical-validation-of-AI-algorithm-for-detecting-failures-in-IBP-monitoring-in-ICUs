import h5py
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import resample_poly, find_peaks
import sys
import os

# ─── Configuração ─────────────────────────────────────────────────────────────
UPSAMPLE_FACTOR = 4
CONV = 250 / 2048            # conversão raw → mmHg

# Arquivo de entrada (pode passar como argumento: python Analyze_flush.py flush_1.h5)
if len(sys.argv) > 1:
    file = sys.argv[1]
else:
    file = "10_10_10_134_20251107_11_22,447_0,253/flush_2.h5"

if not os.path.exists(file):
    print(f"Arquivo não encontrado: {file}")
    sys.exit(1)

# ─── Leitura ──────────────────────────────────────────────────────────────────
with h5py.File(file, 'r') as f:
    sig_raw = f['signal'][:].astype(np.float64)
    t_orig  = f['time'][:]
    Fs_orig = float(f.attrs.get('Fs', 1 / np.median(np.diff(t_orig))))

# ─── Conversão para mmHg ──────────────────────────────────────────────────────
sig_mmhg = sig_raw * CONV

# ─── Upsampling com resample_poly ─────────────────────────────────────────────
sig_up = resample_poly(sig_mmhg, up=UPSAMPLE_FACTOR, down=1)
Fs_up  = Fs_orig * UPSAMPLE_FACTOR
t_up   = np.arange(len(sig_up)) / Fs_up + t_orig[0]

print(f"Arquivo      : {file}")
print(f"Fs original  : {Fs_orig:.1f} Hz  →  Fs upsampled: {Fs_up:.1f} Hz")
print(f"Amostras orig: {len(sig_mmhg)}  →  upsampled: {len(sig_up)}")

# ─── Detecção de picos e vales ────────────────────────────────────────────────
prominence = (np.max(sig_up) - np.min(sig_up)) * 0.01
peaks_idx,   _ = find_peaks( sig_up, prominence=prominence, distance=int(Fs_up * 0.005))
valleys_idx, _ = find_peaks(-sig_up, prominence=prominence, distance=int(Fs_up * 0.005))

peaks_t   = t_up[peaks_idx]
peaks_val = sig_up[peaks_idx]

print(f"\nPicos detectados: {len(peaks_idx)}")
for i, (tp, vp) in enumerate(zip(peaks_t, peaks_val)):
    print(f"  Pico {i+1}: t = {tp - t_orig[0]:.4f} s,  {vp:.2f} mmHg")

# ─── Plot ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(14, 5))
fig.suptitle(f"Flush — {os.path.basename(file)}", fontsize=13, fontweight='bold')

t_rel_orig = t_orig - t_orig[0]
t_rel_up   = t_up   - t_orig[0]

ax.plot(t_rel_orig, sig_mmhg, color='#aaaaaa', linewidth=1.0,
        label=f'Original ({Fs_orig:.0f} Hz)', alpha=0.7, zorder=2)
ax.plot(t_rel_up, sig_up, color='#1a7abf', linewidth=0.9,
        label=f'Upsampled ({Fs_up:.0f} Hz)', zorder=3)

if len(peaks_idx):
    ax.scatter(t_rel_up[peaks_idx], peaks_val,
               color='#e74c3c', s=40, zorder=5, label='Picos')
    for tx, vy in zip(t_rel_up[peaks_idx], peaks_val):
        ax.annotate(f"{vy:.1f}mmHg\n{tx:.4f}s", xy=(tx, vy), xytext=(0, 7),
                    textcoords='offset points', ha='center', va='bottom',
                    fontsize=7.5, color='#e74c3c')
if len(valleys_idx):
    ax.scatter(t_rel_up[valleys_idx], sig_up[valleys_idx],
               color='#f39c12', s=30, zorder=5, marker='v', label='Vales')
    for tx, vy in zip(t_rel_up[valleys_idx], sig_up[valleys_idx]):
        ax.annotate(f"{vy:.1f}mmHg\n{tx:.4f}s", xy=(tx, vy), xytext=(0, 7),
                    textcoords='offset points', ha='center', va='bottom',
                    fontsize=7.5, color='#f39c12')

ax.set_xlabel("Tempo relativo (s)")
ax.set_ylabel("Pressão (mmHg)")
ax.legend(fontsize=8, loc='upper right')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()