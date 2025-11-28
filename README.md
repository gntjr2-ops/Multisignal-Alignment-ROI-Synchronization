# Multisignal ECG·PPG Alignment & ROI-Based Synchronization Framework

## Overview
This project provides a **synchronization and multi-signal alignment algorithm** designed for analyzing *stored* ECG and PPG datasets, typically captured via wearable or research-oriented acquisition systems.

Because ECG and PPG often have:
- Different sampling rates  
- Different starting timestamps  
- Noise and motion differences  

…direct comparison is difficult without proper alignment.  
This software solves that by offering:

- **Time-axis synchronization**
- **ROI (Region of Interest) based multi-signal alignment**
- **Extraction of heartbeat templates**
- **BPM / HRV analysis**
- **PPG–ECG event comparison (PTT, morphology)**

This system provides a reproducible analysis environment for physiological research, sleep studies, and cardiovascular signal evaluation.

---

## Key Features

### 1. Load Stored ECG/PPG Data
- Reads `.mat` files (e.g., `ppg_raw.mat`, `ecg_raw.mat`)
- Auto-detects sampling rate  
- Generates time axis automatically  
- Supports optional median/bandpass filtering

---

### 2. Time-Axis Synchronization (Sync)
- Two or more plotted signals stay synchronized  
- Zooming or panning in one graph updates the others  
- Allows intuitive cross-modal comparison  
- Useful for inspecting:
  - Pulse Transit Time (PTT)
  - ECG–PPG phase differences
  - Motion-induced offsets

---

### 3. ROI-Based Extraction & Local Analysis
Selecting an ROI enables:

- Signal cropping  
- Local filtering  
- Peak detection  
- BPM calculation  
- HRV analysis  
- PPG/ECG heartbeat template extraction  

Enables detailed analysis of **specific time segments only** (e.g., sleep REM, workout burst, anomaly).

---

### 4. Multi-Signal Alignment
Supports PPG, ECG, and optional IMU:

- Aligns all signals to the same time interval  
- ROI-based alignment ensures all extracted segments match exactly  
- Event-level alignment for:
  - R-peak vs PPG-peak comparison  
  - Pulse transit delay estimation  
  - Multi-cycle template overlay  

---

### 5. Visualization Interface
Provides multiple tabs for:

- Raw vs Filtered waveforms  
- BPM / HR time series  
- ROI waveform overlay  
- PPG & ECG templates  
- Event-based multi-signal comparison

---

## Processing Pipeline

### 1. Load & Preprocess
- Import PPG/ECG `.mat` files
- Build time-series with detected sampling rate
- Apply standard filters:
  - Median filter  
  - Bandpass (ECG: 5–30 Hz, PPG: 0.5–8 Hz)

---

### 2. Time Synchronization
- User zooms/pans on ECG or PPG graph  
- Other plots immediately reflect identical time window  
- Maintains perfect temporal alignment  
- Ideal for:
  - Simultaneous beat inspection  
  - Artifact detection  
  - Template consistency

---

### 3. ROI Selection & Local Analysis
User selects a region via GUI:

The system extracts that ROI and performs:
- ECG R-peak detection  
- PPG peak detection  
- BPM estimation  
- HRV metrics (SDNN, RMSSD, LF/HF if needed)
- Template extraction:
  - R-peak centered template
  - PPG pulse template

---

### 4. Multi-Signal Re-Alignment
Within the ROI:
- ECG & PPG signals trimmed to identical timestamps  
- Heartbeat-level alignment for event comparisons  
- Supports multi-modality:
  - PPG
  - ECG
  - IMU (optional)
- Useful for identifying:
  - Pulse transit delay  
  - Vascular stiffness indicators  
  - Beat morphology differences  

---

### 5. Data Export
All results can be saved as:
- `.csv` → numerical signals, BPM, HRV  
- `.png` → waveform images, templates, overlays  
- `.json` → ROI metadata, alignment info  

Ensures full reproducibility for research environments.

---

## Usage Workflow

### 1. Load Data
