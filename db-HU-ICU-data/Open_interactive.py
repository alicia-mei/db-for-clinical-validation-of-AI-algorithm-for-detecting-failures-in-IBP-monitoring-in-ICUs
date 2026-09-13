import h5py
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
import numpy as np
import os
import re

file = "10.10.10.129_20260407_12.h5"

# Pasta de saída: extrai só os números do nome do arquivo (ex: "10_10_10_131_20260310_17")
_nums = re.findall(r'\d+', os.path.splitext(os.path.basename(file))[0])
_folder_name = "_".join(_nums)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(file)), _folder_name)
os.makedirs(OUTPUT_DIR, exist_ok=True)
hdf = h5py.File(file, 'r')

# Definitions
DATA_PACK_HEAD = b"\x02\x0B\x00\x00"
data_add = 36

data = hdf['data'][:]
data_timestamps = hdf['data_timestamps'][:]

datas, ids, seqs, seqsts = [], [], [], []

for raw_data, ts in zip(data, data_timestamps):
    if len(raw_data) < 26:
        continue
    buf = memoryview(raw_data)
    pack_id = bytes(buf[0:4])
    if pack_id != DATA_PACK_HEAD:
        continue
    frame_len = int.from_bytes(bytes(buf[4:6]), byteorder='big', signed=False)
    frame_seq = int.from_bytes(bytes(buf[24:26]), byteorder='big', signed=False)
    frame_end = min(len(buf), frame_len if frame_len > 0 else len(buf))
    local = int(data_add)
    npk = 0
    while True:
        if local + 4 > frame_end:
            break
        head = buf[local:local+4]
        id3 = int.from_bytes(bytes(head[0:3]), byteorder='big', signed=False)
        data_len = int(head[3]) * 2
        if data_len <= 0:
            break
        payload_end = local + 4 + data_len
        if payload_end > frame_end:
            break
        data_bytes = buf[local+4:payload_end]
        arr = np.frombuffer(data_bytes.tobytes(), dtype='>i2')
        datas.append(arr)
        ids.append(id3)
        seqs.append(frame_seq)
        seqsts.append(ts)
        npk += 1
        local = payload_end
        if npk > 100000:
            break

seqs = np.array(seqs, dtype=np.int64)
ids = np.array(ids, dtype=np.int64)
seqsts = np.array(seqsts)

# IDs conhecidos
idECGs  = 65540
idSpO2  = 458768
idResp  = 327688
idP1    = 4063240
idPVC   = 3473416
idART   = 2883592
idCO2   = 4784136

id_target = idP1

indices = np.where(ids == id_target)[0]

if len(indices) == 0:
    print(f"Nenhum pacote encontrado para ID {id_target}")
    exit()

sig = np.concatenate([datas[i] for i in indices])
timestamp_blocks = seqsts[indices]

if len(timestamp_blocks) > 1:
    Fs = np.round(len(datas[indices[0]]) / np.median(np.diff(timestamp_blocks)))
else:
    Fs = 250

dt = 1 / Fs
t = np.arange(len(sig)) * dt

print(f"Fs ≈ {Fs:.2f} Hz, total de amostras = {len(sig)}, duração = {t[-1]:.1f} s")

# ─── Ferramenta de recorte interativo ────────────────────────────────────────

# Estado compartilhado do span selecionado
selection = {"t_start": None, "t_end": None, "span": None}

fig, ax = plt.subplots(figsize=(14, 5))
plt.subplots_adjust(bottom=0.22)

ax.plot(t, sig, color='#1a7abf', linewidth=0.6, alpha=0.85)
ax.set_title(f"Sinal ART — clique e arraste para selecionar o recorte", fontsize=12)
ax.set_ylabel("Amplitude (raw int16)")
ax.set_xlabel("Tempo (s)")
ax.set_xlim(t[0], t[-1])

# Texto de status abaixo do gráfico
status_ax = fig.add_axes([0.13, 0.01, 0.75, 0.05])
status_ax.axis('off')
status_text = status_ax.text(0.5, 0.5, "Arraste sobre o gráfico para selecionar um trecho",
                              ha='center', va='center', fontsize=10, color='#555555',
                              transform=status_ax.transAxes)

# Botão de exportar
btn_ax = fig.add_axes([0.80, 0.08, 0.13, 0.07])
btn = widgets.Button(btn_ax, 'Exportar\nrecorte', color='#1a7abf', hovercolor='#1260a0')
btn.label.set_color('white')
btn.label.set_fontsize(9)

# Botão de limpar seleção
clr_ax = fig.add_axes([0.65, 0.08, 0.13, 0.07])
clr_btn = widgets.Button(clr_ax, 'Limpar\nseleção', color='#e0e0e0', hovercolor='#cccccc')
clr_btn.label.set_fontsize(9)


def format_time(sec):
    m = int(sec) // 60
    s = sec - m * 60
    return f"{m:02d}:{s:06.3f}"


def on_span_select(t_min, t_max):
    selection["t_start"] = t_min
    selection["t_end"]   = t_max
    n_samples = int((t_max - t_min) * Fs)
    status_text.set_text(
        f"Seleção: {format_time(t_min)} → {format_time(t_max)}   |   "
        f"Δt = {t_max - t_min:.3f} s   |   ~{n_samples} amostras"
    )
    fig.canvas.draw_idle()


span_selector = widgets.SpanSelector(
    ax,
    on_span_select,
    direction='horizontal',
    useblit=True,
    props=dict(alpha=0.25, facecolor='#f7a91e'),
    interactive=True,
    drag_from_anywhere=True,
)


def next_flush_index():
    """Retorna o próximo índice flush_N disponível na pasta de saída."""
    existing = [f for f in os.listdir(OUTPUT_DIR) if re.match(r'^flush_\d+\.h5$', f)]
    if not existing:
        return 1
    nums = [int(re.search(r'\d+', f).group()) for f in existing]
    return max(nums) + 1


def export_crop(event):
    t0 = selection["t_start"]
    t1 = selection["t_end"]
    if t0 is None or t1 is None or t0 >= t1:
        status_text.set_text("⚠  Nenhuma seleção válida. Arraste sobre o gráfico primeiro.")
        fig.canvas.draw_idle()
        return

    i0 = int(np.round(t0 * Fs))
    i1 = int(np.round(t1 * Fs))
    i0 = max(0, i0)
    i1 = min(len(sig), i1)

    seg   = sig[i0:i1]
    t_seg = t[i0:i1]

    idx  = next_flush_index()
    base = os.path.join(OUTPUT_DIR, f"flush_{idx}")

    out_npy = base + ".npy"
    out_csv = base + ".csv"
    out_h5  = base + ".h5"

    # Salva .npy
    np.save(out_npy, seg)

    # Salva .csv (tempo, amplitude)
    np.savetxt(out_csv, np.column_stack([t_seg, seg]),
               delimiter=',', header='time_s,amplitude', comments='')

    # Salva .h5
    with h5py.File(out_h5, 'w') as fout:
        fout.create_dataset('signal', data=seg,   dtype='int16')
        fout.create_dataset('time',   data=t_seg, dtype='float64')
        fout.attrs['Fs']         = float(Fs)
        fout.attrs['id_target']  = id_target
        fout.attrs['t_start_s']  = t0
        fout.attrs['t_end_s']    = t1
        fout.attrs['source_file'] = file

    status_text.set_text(
        f"✔  flush_{idx} salvo em .../{_folder_name}/   ({len(seg)} amostras, {t1-t0:.2f} s)"
    )
    fig.canvas.draw_idle()
    print(f"\n[Exportado] flush_{idx}")
    print(f"  Pasta  → {OUTPUT_DIR}")
    print(f"  .npy   → {out_npy}")
    print(f"  .csv   → {out_csv}")
    print(f"  .h5    → {out_h5}")
    print(f"  Fs = {Fs:.1f} Hz | {len(seg)} amostras | Δt = {t1-t0:.3f} s")


def clear_selection(event):
    selection["t_start"] = None
    selection["t_end"]   = None
    status_text.set_text("Seleção limpa. Arraste novamente para selecionar.")
    fig.canvas.draw_idle()


btn.on_clicked(export_crop)
clr_btn.on_clicked(clear_selection)

plt.show()