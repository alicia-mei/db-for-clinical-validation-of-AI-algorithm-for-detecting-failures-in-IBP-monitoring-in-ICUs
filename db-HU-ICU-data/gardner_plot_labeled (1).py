import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# --- Dados da curva (contorno da região de Gardner) ---
fn = [48.9052537718578, 47.9742045956694, 46.5776308313869, 45.2586444984533, 43.8620707341708, 42.7758466952844, 41.3792729310018, 40.2930488921154, 39.361999715927, 38.1974780632535, 37.1112540243671, 36.0250299854807, 34.9388059465942, 33.8518717252698, 32.7649375039454, 31.599705668834, 30.6672361277697, 29.4237066788712, 28.1025897986238, 26.4697028281042, 24.9144032889337, 23.6687432927214, 22.422373114071, 21.0977053216337, 19.8520453254213, 18.37078230541, 16.6546264440376, 15.3271179218483, 13.922732150748, 12.6749416072217, 11.6599133577425, 10.6434647433874, 9.39354365254718, 8.53298008332807, 7.75000394545798, 8.44118900321949, 9.13379442585695, 9.82568966605643, 10.6727597689539, 11.7511718010226, 12.9043305346884, 14.0574892683542, 15.1366114828609, 16.2911905814026, 17.3681822485954, 18.5213409822612, 19.5997530143299, 20.6005776150495, 21.4462273530711, 22.6783938829619, 23.7553855501546, 24.9092544662584, 25.910079066978, 26.9109036676977, 27.9871851524524, 29.2955187488163, 30.6814397765292, 31.6046769458998, 32.6823787955305, 33.297396786819, 34.3750986364497, 35.4520903036424]

ksi = [0.0427474591250554, 0.0428137428192665, 0.0429131683605834, 0.0430070702607159, 0.0431064958020328, 0.0431838267786126, 0.0432832523199293, 0.0433605832965091, 0.0434268669907202, 0.04671343349536, 0.0467907644719398, 0.0468680954485196, 0.0469454264250994, 0.050226469288555, 0.0535075121520105, 0.059997790543526, 0.0664714980114895, 0.076171011931065, 0.0858760494918251, 0.102010605391073, 0.118139637649138, 0.137450287229341, 0.15996464869642, 0.185688245691559, 0.204998895271762, 0.237140963323022, 0.278910737958462, 0.317449182501104, 0.352789438798055, 0.381711224038886, 0.410616438356164, 0.445929076447193, 0.484461997348652, 0.516559876270437, 0.548652231551038, 0.580639637649138, 0.606219619973486, 0.63500331418471, 0.663775961113566, 0.69893946089262, 0.746912284577993, 0.794885108263367, 0.826844896155545, 0.868410296067167, 0.909981219619973, 0.957954043305347, 0.993117543084401, 1.02828656650464, 1.06346663720724, 1.10502651347768, 1.14659743703049, 1.19136654882898, 1.22653557224922, 1.26170459566946, 1.30647923110914, 1.35444100751215, 1.40239726027397, 1.43757180733539, 1.47593901900132, 1.50152452496685, 1.53989173663278, 1.58146266018559]

# --- Dados dos cateteres com classificação (da tabela) ---
# Ordem original do scatter: fn_uti e ksi_uti
# Mapeando cada ponto para o cateter correto pela tabela
cateteres = [
    {"id": 5,  "fn": 14.88, "zeta": 0.253341, "class": "Inadequate"},
    {"id": 8,  "fn": 17.43, "zeta": 0.375868, "class": "Adequate"},
    {"id": 6,  "fn": 18.33, "zeta": 0.223641, "class": "Inadequate"},
    {"id": 4,  "fn": 22.45, "zeta": 0.253346, "class": "Adequate"},
    {"id": 2,  "fn": 23.62, "zeta": 0.271582, "class": "Adequate"},
    {"id": 1,  "fn": 23.68, "zeta": 0.267377, "class": "Adequate"},
    {"id": 7,  "fn": 27.19, "zeta": 0.084601, "class": "Inadequate"},
    {"id": 3,  "fn": 28.12, "zeta": 0.264371, "class": "Adequate"},
]

adequate   = [c for c in cateteres if c["class"] == "Adequate"]
inadequate = [c for c in cateteres if c["class"] == "Inadequate"]

# --- Plot ---
fig, ax = plt.subplots(figsize=(10, 6))

# Região preenchida (polígono de Gardner)
xlim_right = 55
polygon_fill_x = fn + [xlim_right, xlim_right, fn[0]]
polygon_fill_y = ksi + [ksi[-1], ksi[0], ksi[0]]

ax.fill(polygon_fill_x, polygon_fill_y, color='#B0B0B0', alpha=0.5, label='Adequate Dynamic Response Region')
ax.plot(fn, ksi, color='black', linewidth=1.5)

# Scatter — Adequados (verde)
ax.scatter(
    [c["fn"] for c in adequate],
    [c["zeta"] for c in adequate],
    marker='x', color='#1a7a1a', s=100, linewidths=2.5, zorder=5,
    label='Adequate'
)

# Scatter — Inadequados (vermelho)
ax.scatter(
    [c["fn"] for c in inadequate],
    [c["zeta"] for c in inadequate],
    marker='x', color='#cc2200', s=100, linewidths=2.5, zorder=5,
    label='Inadequate'
)

# Anotações com número do cateter
offset_map = {
    1: (0.8,  0.02),   # Cat 1 e 2 ficam próximos — afasta Cat 1 para cima
    2: (0.8, -0.04),
    3: (0.8,  0.02),
    4: (0.8,  0.02),
    5: (0.8,  0.02),
    6: (0.8, -0.04),
    7: (0.8,  0.02),
    8: (0.8,  0.02),
}

for c in cateteres:
    color = '#1a7a1a' if c["class"] == "Adequate" else '#cc2200'
    dx, dy = offset_map.get(c["id"], (0.5, 0.02))
    ax.annotate(
        f'C{c["id"]}',
        xy=(c["fn"], c["zeta"]),
        xytext=(c["fn"] + dx, c["zeta"] + dy),
        fontsize=9,
        fontweight='bold',
        color=color,
        ha='left',
        va='bottom',
    )

# --- Formatação ---
ax.set_xlim(0, 55)
ax.set_ylim(0, 1.6)
ax.set_xlabel('$f_n$ — NATURAL FREQUENCY (Hz)', fontsize=12)
ax.set_ylabel('DAMPING COEFFICIENT $\\zeta$', fontsize=12)
ax.set_title('Dynamic Response Chart (Gardner)', fontsize=14)
ax.legend(loc='upper left', fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('dynamic_response_chart_labeled.png', dpi=150, bbox_inches='tight')
print("Gráfico salvo.")
