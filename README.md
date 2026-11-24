# Database for Clinical Validation of an AI Algorithm for Detecting Failures in IBP Monitoring in ICUs

Scripts used to build the **HU-USP Fast-Flush Database**, a set of invasive blood pressure (IBP) recordings annotated with fast-flush tests and collected in the adult Intensive Care Unit (ICU) of the Hospital Universitário da Universidade de São Paulo (HU-USP). The repository also contains the generator of the companion **synthetic database**.

[![Dataset DOI](https://img.shields.io/badge/Dataset-10.5281%2Fzenodo.24488605-blue)](https://doi.org/10.5281/zenodo.24488605)
[![Paper DOI](https://img.shields.io/badge/Paper%20(CBEB%202026)-10.5281%2Fzenodo.23214826-blue)](https://doi.org/10.5281/zenodo.23214826)
[![License: MIT](https://img.shields.io/badge/Code-MIT-green)](LICENSE)

## Context

IBP is the gold standard for haemodynamic monitoring in the ICU, but its accuracy depends on the dynamic response of the catheter–transducer system. Air bubbles, clots or loose connections can distort the waveform (e.g., underdamping overestimates systolic pressure). The **fast-flush test** produces a transient oscillation from which the system's **natural frequency (fₙ)** and **damping coefficient (ζ)** can be estimated and checked against **Gardner's criteria**.

At the Laboratório de Engenharia Biomédica (LEB) of the Escola Politécnica da Universidade de São Paulo (EP-USP), a convolutional neural network is being developed to detect these distortions from the arterial waveform alone. This project provides the real, annotated clinical data needed for its future validation. In parallel, it provides a synthetic database to test an auxiliary algorithm for automatic flush detection and fₙ/ζ estimation.

For details, see the [paper](https://doi.org/10.5281/zenodo.23214826). The resulting clinical data are on [Zenodo](https://doi.org/10.5281/zenodo.24488605).

## Repository structure

```
├── db-HU-ICU-data/                       Real data (HU-USP ICU)
│   ├── Open_interactive.py               Decode the monitor H5 file and export flush windows
│   ├── Analyze_flush.py                  Upsample a flush window and detect peaks/valleys
│   ├── gardner_plot_labeled.py           Plot catheters on Gardner's dynamic response chart
│   └── fronteira_gardner_e_uti.csv       Gardner chart boundary + fₙ/ζ of the ICU catheters
├── db-simulated-data/                    Synthetic data
│   ├── sim_pai.py                        Generate simulated IBP signals with true/fake flushes
│   └── csv_plot.py                       Plot a simulated signal
└── LICENSE
```

## Requirements

Python 3 with:

```bash
pip install numpy scipy pandas matplotlib h5py openpyxl
```

## Workflow: real ICU data

```
monitor H5 file ──► Open_interactive.py ──► flush_N.{csv,npy,h5} ──► Analyze_flush.py ──► peaks/valleys
                                                                                              │
                                                                         fₙ, ζ (Gardner's method)
                                                                                              │
                                                                     gardner_plot_labeled.py ◄┘
```

### 1. Acquisition (not in this repository)

Signals were acquired at 125 Hz from Nihon Kohden Lifescope® bedside monitors by LEB-USP software that captures the monitor packets from the hospital network. Each recording session is saved as an H5 file (`data`, `data_timestamps`, `info`, `info_timestamps`) with the raw network packets.

### 2. `Open_interactive.py`: decode and export the flushes

- Parses the proprietary packets and extracts the signal of the selected channel (`id_target`). Known channel IDs include ART, P1, ECG, SpO2, Resp, PVC and CO2. Channels labelled **RAD** or **FEM** on the monitor are not yet supported, which is why those recordings could not be extracted.
- Opens an interactive plot. Drag to select a window and click **Export** to save it as `flush_N.npy`, `flush_N.csv` (`time_s, amplitude`) and `flush_N.h5` (signal, time, Fs and metadata).
- The output goes to a folder named after the numbers in the H5 file name (e.g., `10_10_10_131_20260310_17/`).

**Usage:** set `file = "<recording>.h5"` and `id_target` (e.g., `idART` or `idP1`) at the top of the script, then run:

```bash
python db-HU-ICU-data/Open_interactive.py
```

### 3. `Analyze_flush.py`: prepare the flush for parameter estimation

- Converts raw values to mmHg (`CONV = 250 / 2048`).
- Upsamples the signal ×4 (125 → 500 Hz) with polyphase FIR interpolation (`scipy.signal.resample_poly`).
- Detects and plots the peaks and valleys of the post-flush oscillation (`find_peaks`, prominence = 1% of the signal range). The `prominence` and `distance` parameters can be adjusted.

```bash
python db-HU-ICU-data/Analyze_flush.py <folder>/flush_1.h5
```

From the plotted peak amplitudes and periods, ζ and the damped frequency ω_d are obtained by **Gardner's method**, and the natural frequency is calculated as **ωₙ = ω_d / √(1 − ζ²)**. This step was done manually. For each catheter, the reported value is the mean over the flushes whose oscillation occurred during diastole.

A flush was considered **valid** when the rise and fall each lasted < 300 ms, the plateau lasted 1–15 s, and the pulsatile component was present before, after and during the plateau. Oscillations with fewer than two peaks were treated as overdamped, and no parameters were estimated for them.

### 4. `gardner_plot_labeled.py`: Gardner's chart

Plots the adequate dynamic response region of Gardner's chart and the ICU catheters, coloured as adequate or inadequate. New catheters are added to the `cateteres` list. The output is `dynamic_response_chart_labeled.png`.

`fronteira_gardner_e_uti.csv` contains the same boundary points and the fₙ/ζ of the catheters (`;` separator, `,` decimal).

## Synthetic database

`sim_pai.py` generates 1-hour IBP signals at 125 Hz for four clinical profiles: normotensive, septic shock, cardiogenic shock and on norepinephrine. In each signal:

- The arterial pulse is approximated by a sinusoid, with heart rate, mean pressure and amplitude drawn from physiological ranges for each profile.
- **True flushes** have a fast rise (0.1 s), a plateau of 2–15 s at 250–300 mmHg, a fast fall (0.2 s) and an underdamped second-order oscillation.
- **Fake flushes** are artefacts with a slow logarithmic rise (2–30 s), a step fall and an oscillation.
- The oscillation parameters are drawn at random for each signal (`omega_n` ∈ [10, 50], ζ ∈ [0.1, 0.9]).

Each signal is saved as a CSV (`time, pressure`). A summary spreadsheet per profile lists the file name, profile, pressures, heart rate, number of true and fake flushes, the start times of each flush's fall, and the fₙ and ζ used, which serve as the ground truth for the detection algorithm.

```bash
cd db-simulated-data
python sim_pai.py           # generates the simulacoes_pressao_<profile>/ folders and summaries
python csv_plot.py          # plots one example simulation
```

## Ethics

Clinical data were collected under approval of the Comitê de Ética em Pesquisa (CEP) of HU-USP, Certificado de Apresentação de Apreciação Ética (CAAE) no. 86650625.3.0000.0076, with deferred family consent (Resolution 466/2012 of the Conselho Nacional de Saúde). **No patient data are included in this repository.** The anonymized dataset is available on [Zenodo](https://doi.org/10.5281/zenodo.24488605).

## How to cite

If you use this code, please cite the paper and/or the dataset:

- Camigauchi, A. M. K. et al. Creation of a Database for Clinical Validation of an Artificial Intelligence Algorithm for Detecting Failures in Invasive Blood Pressure Monitoring in Intensive Care Units. *Congresso Brasileiro de Engenharia Biomédica (CBEB)*, 2026. https://doi.org/10.5281/zenodo.23214826
- Camigauchi, A. M. K.; Lima, F. F.; Moriya, H. T. (2026). *HU-USP Fast-Flush Database: Invasive Arterial Pressure Recordings with Fast-Flush Tests from an Adult ICU* (Version 1.0) [Data set]. Zenodo. https://doi.org/10.5281/zenodo.24488605

## Authors

- **Alícia Mei Kato Camigauchi**: development, data collection and analysis ([ORCID](https://orcid.org/0009-0006-2310-7427)). Contact: aliciamei@usp.br
- **Felipe Fava de Lima**: supervision ([ORCID](https://orcid.org/0000-0002-7102-8532))
- **Henrique Takachi Moriya**: supervision ([ORCID](https://orcid.org/0000-0002-1595-1779))

Laboratório de Engenharia Biomédica (LEB), Departamento de Engenharia de Telecomunicações e Controle (PTC), Escola Politécnica da Universidade de São Paulo (EP-USP).

## Funding

Partly funded by the Conselho Nacional de Desenvolvimento Científico e Tecnológico (CNPq), grants 136156/2025-8 and 309464/2022-6.

## License

The code is released under the [MIT License](LICENSE). The dataset on Zenodo has its own license (CC BY-NC 4.0).
