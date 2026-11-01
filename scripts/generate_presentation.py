import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_HTML = BASE_DIR / "presentation_build" / "presentation.html"
OUTPUT_PDF = BASE_DIR / "Hotel_ML_Project_Presentation.pdf"

CHROME_PATHS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
]

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Hotel Reservation Cancellation & ADR Prediction - ML Project</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  @page {
    size: 1920px 1080px;
    margin: 0;
  }
  *, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }
  html, body {
    width: 1920px;
    background-color: #070a12;
    color: #e2e8f0;
    font-family: 'Plus Jakarta Sans', 'Segoe UI', -apple-system, sans-serif;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    -webkit-font-smoothing: antialiased;
  }
  .slide {
    width: 1920px;
    height: 1080px;
    max-height: 1080px;
    overflow: hidden;
    page-break-inside: avoid;
    page-break-after: always;
    break-after: page;
    position: relative;
    padding: 50px 75px 36px 75px;
    display: flex;
    flex-direction: column;
    background: radial-gradient(circle at 85% 15%, rgba(99, 102, 241, 0.09) 0%, transparent 50%),
                radial-gradient(circle at 15% 85%, rgba(6, 182, 212, 0.07) 0%, transparent 40%),
                #070a12;
  }
  .slide:last-of-type {
    page-break-after: auto;
    break-after: auto;
  }

  /* Slide Header */
  .slide-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 22px;
    position: relative;
    z-index: 2;
  }
  .slide-header-left {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .category-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #38bdf8;
    background: rgba(56, 189, 248, 0.1);
    border: 1px solid rgba(56, 189, 248, 0.25);
    padding: 4px 14px;
    border-radius: 20px;
    width: fit-content;
  }
  .slide-title {
    font-family: 'Outfit', sans-serif;
    font-size: 38px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: #ffffff;
    line-height: 1.2;
  }
  .slide-subtitle {
    font-size: 17px;
    color: #94a3b8;
    font-weight: 400;
  }
  .slide-counter {
    font-family: 'JetBrains Mono', monospace;
    font-size: 15px;
    font-weight: 600;
    color: #64748b;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.07);
    padding: 6px 14px;
    border-radius: 8px;
  }

  /* Slide Body */
  .slide-body {
    flex: 1;
    display: flex;
    gap: 24px;
    position: relative;
    z-index: 2;
    min-height: 0;
  }

  /* Slide Footer */
  .slide-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 14px;
    margin-top: 18px;
    border-top: 1px solid rgba(255, 255, 255, 0.07);
    font-size: 13.5px;
    color: #64748b;
  }
  .footer-tag {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .footer-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #6366f1;
  }

  /* Card Styles */
  .card {
    background: rgba(18, 25, 43, 0.72);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 22px 26px;
    backdrop-filter: blur(10px);
    display: flex;
    flex-direction: column;
    gap: 14px;
    position: relative;
  }
  .card-highlight {
    background: linear-gradient(135deg, rgba(30, 41, 71, 0.65) 0%, rgba(18, 25, 43, 0.85) 100%);
    border: 1px solid rgba(99, 102, 241, 0.35);
  }
  .card-title {
    font-family: 'Outfit', sans-serif;
    font-size: 21px;
    font-weight: 600;
    color: #f1f5f9;
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 2px;
  }
  .card-title svg {
    color: #38bdf8;
    flex-shrink: 0;
  }

  /* Stat & Metrics Card */
  .metric-box {
    display: flex;
    flex-direction: column;
    padding: 14px 18px;
    background: rgba(255, 255, 255, 0.025);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
  }
  .metric-value {
    font-family: 'Outfit', sans-serif;
    font-size: 32px;
    font-weight: 700;
    color: #ffffff;
    line-height: 1.1;
  }
  .metric-label {
    font-size: 13.5px;
    font-weight: 500;
    color: #94a3b8;
    margin-top: 4px;
  }
  .metric-tag {
    font-size: 11.5px;
    font-weight: 600;
    color: #10b981;
    margin-top: 4px;
  }

  /* Badges & Pills */
  .pill {
    font-size: 12px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
    gap: 5px;
  }
  .pill-indigo { background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); }
  .pill-emerald { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
  .pill-amber { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
  .pill-cyan { background: rgba(6, 182, 212, 0.15); color: #22d3ee; border: 1px solid rgba(6, 182, 212, 0.3); }
  .pill-rose { background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }

  /* Lists */
  ul.feature-list {
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  ul.feature-list li {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    font-size: 14.5px;
    line-height: 1.45;
    color: #cbd5e1;
  }
  ul.feature-list li strong {
    color: #ffffff;
    font-weight: 600;
  }
  .check-icon {
    width: 20px;
    height: 20px;
    min-width: 20px;
    border-radius: 50%;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #34d399;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    margin-top: 2px;
  }

  /* Tables */
  table.styled-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }
  table.styled-table th {
    text-align: left;
    padding: 10px 12px;
    background: rgba(255, 255, 255, 0.04);
    color: #94a3b8;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }
  table.styled-table td {
    padding: 10px 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    color: #cbd5e1;
  }
  table.styled-table tr.winner-row {
    background: rgba(99, 102, 241, 0.14);
  }
  table.styled-table tr.winner-row td {
    color: #ffffff;
    font-weight: 600;
    border-bottom: 1px solid rgba(99, 102, 241, 0.35);
  }

  /* Grid Layouts */
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; width: 100%; }
  .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; width: 100%; }
  .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; width: 100%; }

  /* Hero Slide */
  .hero-slide {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-start;
    padding: 90px 110px;
    background: radial-gradient(circle at 80% 30%, rgba(99, 102, 241, 0.18) 0%, transparent 60%),
                radial-gradient(circle at 20% 70%, rgba(6, 182, 212, 0.12) 0%, transparent 50%),
                #070a12;
  }
  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #a5b4fc;
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 600;
    padding: 6px 16px;
    border-radius: 24px;
    margin-bottom: 24px;
    letter-spacing: 1px;
  }
  .hero-title {
    font-family: 'Outfit', sans-serif;
    font-size: 64px;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.15;
    letter-spacing: -1px;
    margin-bottom: 18px;
    max-width: 1400px;
  }
  .hero-title span {
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .hero-desc {
    font-size: 21px;
    color: #94a3b8;
    max-width: 1200px;
    line-height: 1.6;
    margin-bottom: 46px;
  }
  .hero-stats {
    display: flex;
    gap: 24px;
    width: 100%;
  }

  /* Step box */
  .flow-step {
    display: flex;
    flex-direction: column;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px 18px;
  }
  .flow-step-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 700;
    color: #38bdf8;
    letter-spacing: 1px;
    margin-bottom: 4px;
  }
  .flow-step-title {
    font-size: 15.5px;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 3px;
  }
  .flow-step-desc {
    font-size: 13px;
    color: #94a3b8;
    line-height: 1.4;
  }
</style>
</head>
<body>

<!-- ==========================================
     SLIDE 1: TITLE / COVER
     ========================================== -->
<div class="slide hero-slide">
  <div class="hero-badge">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
    MACHINE LEARNING CAPSTONE &bull; HOSPITALITY ANALYTICS &bull; PRODUCTION PROTOTYPE
  </div>
  <h1 class="hero-title">
    Hotel Reservation <span>Cancellation Risk</span> &amp; <span>Rate Prediction (ADR)</span>
  </h1>
  <p class="hero-desc">
    An end-to-end Machine Learning pipeline and dual-model decision system trained on 160,000+ harmonized bookings. Features time-aware chronological validation, decision threshold tuning, and an interactive bilingual Streamlit deployment.
  </p>

  <div class="hero-stats">
    <div class="metric-box" style="flex: 1; border-color: rgba(99, 102, 241, 0.35); background: rgba(99, 102, 241, 0.08);">
      <div class="metric-value" style="color: #818cf8;">Dual-Target</div>
      <div class="metric-label">Classification + Pricing Regressor</div>
      <div class="metric-tag">Cancellation Risk &amp; Room Rate</div>
    </div>
    <div class="metric-box" style="flex: 1; border-color: rgba(6, 182, 212, 0.35); background: rgba(6, 182, 212, 0.08);">
      <div class="metric-value" style="color: #38bdf8;">160,482</div>
      <div class="metric-label">Harmonized Historical Bookings</div>
      <div class="metric-tag">3 Merged Datasets (2015&ndash;2018)</div>
    </div>
    <div class="metric-box" style="flex: 1; border-color: rgba(16, 185, 129, 0.35); background: rgba(16, 185, 129, 0.08);">
      <div class="metric-value" style="color: #34d399;">86.12% / 80.2%</div>
      <div class="metric-label">Classifier Accuracy &amp; F1-Score</div>
      <div class="metric-tag">Tuned Deep Extra Trees</div>
    </div>
    <div class="metric-box" style="flex: 1; border-color: rgba(245, 158, 11, 0.35); background: rgba(245, 158, 11, 0.08);">
      <div class="metric-value" style="color: #fbbf24;">$13.62 MAE</div>
      <div class="metric-label">Pricing Regressor Error</div>
      <div class="metric-tag">Random Forest (R&sup2; = 0.70)</div>
    </div>
  </div>

  <div class="slide-footer" style="width: 100%; margin-top: 55px;">
    <div><strong>Project Presentation:</strong> End-to-End Machine Learning System Architecture &amp; Empirical Results</div>
    <div class="footer-tag"><div class="footer-dot"></div> Slide 1 of 9</div>
  </div>
</div>

<!-- ==========================================
     SLIDE 2: PROBLEM STATEMENT & DUAL OBJECTIVE
     ========================================== -->
<div class="slide">
  <div class="slide-header">
    <div class="slide-header-left">
      <div class="category-badge">Executive Summary</div>
      <h2 class="slide-title">Problem Statement &amp; Dual ML Objectives</h2>
      <p class="slide-subtitle">Addressing revenue loss from unpredictable booking cancellations and sub-optimal room pricing</p>
    </div>
    <div class="slide-counter">02 / 09</div>
  </div>

  <div class="slide-body">
    <div class="card" style="flex: 1.05;">
      <div class="card-title">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        The Hospitality Industry Bottleneck
      </div>
      <ul class="feature-list">
        <li>
          <div class="check-icon" style="background: rgba(244, 63, 94, 0.15); border-color: rgba(244, 63, 94, 0.3); color: #fb7185;">!</div>
          <div><strong>Severe Cancellation Volatility (36.0%):</strong> Over 1 in 3 hotel reservations is canceled prior to check-in, causing perishable room stock losses and staffing overhead.</div>
        </li>
        <li>
          <div class="check-icon" style="background: rgba(244, 63, 94, 0.15); border-color: rgba(244, 63, 94, 0.3); color: #fb7185;">!</div>
          <div><strong>Inefficient Static Room Rates:</strong> Static rules miss demand spikes, room tier differentials, and lead-time willingness-to-pay, leaving RevPAR unrealized.</div>
        </li>
        <li>
          <div class="check-icon" style="background: rgba(244, 63, 94, 0.15); border-color: rgba(244, 63, 94, 0.3); color: #fb7185;">!</div>
          <div><strong>No Real-Time Booking Assessment:</strong> Traditional Property Management Systems (PMS) lack instant scoring at the time of reservation intake.</div>
        </li>
      </ul>

      <div style="padding: 16px; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px;">
        <div style="font-size: 13px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 6px;">Business Reality</div>
        <div style="font-size: 14.5px; color: #cbd5e1; line-height: 1.45;">
          A late cancellation leaves an empty room with zero recovery value. Accurately scoring risk allows targeted deposit policies and dynamic overbooking without customer friction.
        </div>
      </div>
    </div>

    <div class="card card-highlight" style="flex: 1.25;">
      <div class="card-title">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        The Dual Machine Learning Solution
      </div>

      <div class="grid-2">
        <div style="background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 8px;">
          <div class="pill pill-indigo">TASK 1: CLASSIFICATION</div>
          <h3 style="font-size: 18.5px; color: #ffffff;">Cancellation Risk Engine</h3>
          <p style="font-size: 14px; color: #cbd5e1; line-height: 1.5;">
            Predicts exact cancellation probability [0&ndash;1] and assigns <strong>Low, Medium, or High Risk</strong> tiers using tuned decision boundaries.
          </p>
          <div style="margin-top: 6px; padding: 10px 12px; background: rgba(99, 102, 241, 0.15); border-radius: 8px; font-size: 12.5px; color: #c7d2fe;">
            <strong>Action:</strong> Automated non-refundable deposit workflows for reservations in the high-risk band.
          </div>
        </div>

        <div style="background: rgba(6, 182, 212, 0.1); border: 1px solid rgba(6, 182, 212, 0.25); border-radius: 12px; padding: 20px; display: flex; flex-direction: column; gap: 8px;">
          <div class="pill pill-cyan">TASK 2: REGRESSION</div>
          <h3 style="font-size: 18.5px; color: #ffffff;">ADR &amp; Revenue Estimation</h3>
          <p style="font-size: 14px; color: #cbd5e1; line-height: 1.5;">
            Estimates fair <strong>Average Daily Rate (ADR)</strong> in USD based on room specs and seasonality, computing total expected stay yield.
          </p>
          <div style="margin-top: 6px; padding: 10px 12px; background: rgba(6, 182, 212, 0.15); border-radius: 8px; font-size: 12.5px; color: #a5f3fc;">
            <strong>Formula:</strong> Projected Revenue = Predicted ADR &times; Total Stay Nights
          </div>
        </div>
      </div>

      <div style="padding: 14px 18px; background: rgba(255, 255, 255, 0.03); border-radius: 10px; border-left: 3px solid #10b981; font-size: 14px; color: #94a3b8;">
        <strong style="color: #34d399;">Unified Value Proposition:</strong> Integrates risk mitigation and dynamic yield estimation into a single real-time decision dashboard.
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <div>Hospitality Analytics: Combining Risk Assessment &amp; Yield Estimation into One Decision Workflow</div>
    <div class="footer-tag"><div class="footer-dot"></div> Slide 2 of 9</div>
  </div>
</div>

<!-- ==========================================
     SLIDE 3: DATA HARMONIZATION & PIPELINE
     ========================================== -->
<div class="slide">
  <div class="slide-header">
    <div class="slide-header-left">
      <div class="category-badge">Data Engineering</div>
      <h2 class="slide-title">Multi-Source Data Harmonization</h2>
      <p class="slide-subtitle">Merging and standardizing 3 heterogeneous booking datasets spanning 2015 to 2018</p>
    </div>
    <div class="slide-counter">03 / 09</div>
  </div>

  <div class="slide-body">
    <div class="card" style="flex: 1.15;">
      <div class="card-title">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
        Dataset Source Breakdown
      </div>

      <table class="styled-table">
        <thead>
          <tr>
            <th>Dataset Source</th>
            <th>Arrival Years</th>
            <th>Raw Rows</th>
            <th>Usable Rows</th>
            <th>Cancel Rate</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Hotel Reservations.csv</strong></td>
            <td>2017 &ndash; 2018</td>
            <td>36,275</td>
            <td>36,275</td>
            <td>32.76%</td>
          </tr>
          <tr>
            <td><strong>hotel_bookings.csv (Sample)</strong></td>
            <td>2015 &ndash; 2017</td>
            <td>5,000</td>
            <td>4,998</td>
            <td>34.09%</td>
          </tr>
          <tr>
            <td><strong>hotel_bookings1.csv (Full)</strong></td>
            <td>2015 &ndash; 2017</td>
            <td>119,390</td>
            <td>119,209</td>
            <td>37.08%</td>
          </tr>
          <tr class="winner-row">
            <td><strong>Unified Training Corpus</strong></td>
            <td><strong>2015 &ndash; 2018</strong></td>
            <td><strong>160,665</strong></td>
            <td><strong>160,482</strong></td>
            <td><strong>36.01%</strong></td>
          </tr>
        </tbody>
      </table>

      <div style="padding: 12px 16px; background: rgba(56, 189, 248, 0.08); border-radius: 10px; font-size: 13.5px; color: #7dd3fc; line-height: 1.45;">
        <strong>Cryptographic Verification:</strong> SHA-256 fingerprinting confirmed the root-level sample is an exact byte-for-byte subset of the full legacy file, preventing double-counting.
      </div>

      <div style="padding: 12px 16px; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px; font-size: 13.5px; color: #94a3b8;">
        Generated output: <code style="color: #34d399;">data/merged_hotel_reservations.csv</code> (160,482 rows &times; 42 features) with source provenance tags.
      </div>
    </div>

    <div class="card" style="flex: 1.25;">
      <div class="card-title">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        Data Cleansing &amp; Leakage Prevention
      </div>

      <div class="grid-2">
        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px; padding: 14px;">
          <div style="font-size: 14px; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">Outlier &amp; Quality Filtering</div>
          <p style="font-size: 13.5px; color: #94a3b8; line-height: 1.45;">
            Excluded <strong>183 records</strong> with 0 guests or negative ADR. Retained <strong>31,994 legitimate duplicate rows</strong> representing real identical booking patterns.
          </p>
        </div>

        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px; padding: 14px;">
          <div style="font-size: 14px; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">Zero Post-Booking Leakage</div>
          <p style="font-size: 13.5px; color: #94a3b8; line-height: 1.45;">
            Strictly eliminated outcome leakages (<code style="color: #fb7185;">reservation_status</code>, checkout date). Only fields known at booking timestamp are accepted.
          </p>
        </div>
      </div>

      <div style="background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 10px; padding: 16px;">
        <div style="font-size: 14px; font-weight: 700; color: #a5b4fc; margin-bottom: 8px;">Canonical Schema Alignment Mapping:</div>
        <ul class="feature-list" style="gap: 8px;">
          <li style="font-size: 13.5px;">
            <div class="check-icon">&check;</div>
            <div><strong>Guest Demographics:</strong> Unified separate babies and children into single canonical <code style="color: #38bdf8;">no_of_children</code>.</div>
          </li>
          <li style="font-size: 13.5px;">
            <div class="check-icon">&check;</div>
            <div><strong>Distribution Harmonization:</strong> Synced market segments (Online TA, Offline, Corporate, Aviation) and meal plans (BB, HB, FB, Room-Only).</div>
          </li>
          <li style="font-size: 13.5px;">
            <div class="check-icon">&check;</div>
            <div><strong>Sample Weighting:</strong> Applied source-family weighting so the smaller modern source is not drowned out by legacy data.</div>
          </li>
        </ul>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <div>Unified Pipeline: 160,482 Clean Bookings Processed with Zero Future-Lookahead Leakage</div>
    <div class="footer-tag"><div class="footer-dot"></div> Slide 3 of 9</div>
  </div>
</div>

<!-- ==========================================
     SLIDE 4: FEATURE ENGINEERING & PREPROCESSING
     ========================================== -->
<div class="slide">
  <div class="slide-header">
    <div class="slide-header-left">
      <div class="category-badge">Feature Engineering</div>
      <h2 class="slide-title">Domain Features &amp; Preprocessing Architecture</h2>
      <p class="slide-subtitle">Transforming raw hotel variables into high-signal cyclical, behavioral, and interaction predictors</p>
    </div>
    <div class="slide-counter">04 / 09</div>
  </div>

  <div class="slide-body">
    <div class="grid-3" style="width: 100%;">
      <!-- Card 1 -->
      <div class="card">
        <div class="card-title">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          Cyclical Seasonality
        </div>
        <p style="font-size: 14px; color: #94a3b8; line-height: 1.45;">
          Calendar dates are circular (Dec 31 is adjacent to Jan 1). Integer encodings create false numerical discontinuities.
        </p>
        <div style="display: flex; flex-direction: column; gap: 10px;">
          <div style="background: rgba(255, 255, 255, 0.03); padding: 12px; border-radius: 10px; border-left: 3px solid #38bdf8;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; color: #38bdf8;">arrival_month_sin / cos</div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Trigonometric mapping of annual high/low hospitality seasons</div>
          </div>
          <div style="background: rgba(255, 255, 255, 0.03); padding: 12px; border-radius: 10px; border-left: 3px solid #818cf8;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; color: #818cf8;">arrival_weekday_sin / cos</div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Captures weekday business trips vs weekend vacation travelers</div>
          </div>
          <div style="background: rgba(255, 255, 255, 0.03); padding: 12px; border-radius: 10px; border-left: 3px solid #34d399;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; color: #34d399;">arrival_date_sin / cos</div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Intra-month payday cycles and month-end holiday behavior</div>
          </div>
        </div>
      </div>

      <!-- Card 2 -->
      <div class="card">
        <div class="card-title">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          Behavioral &amp; Interaction Ratios
        </div>
        <p style="font-size: 14px; color: #94a3b8; line-height: 1.45;">
          Engineered interaction terms that capture customer psychological commitment and likelihood to cancel.
        </p>
        <div style="display: flex; flex-direction: column; gap: 10px;">
          <div style="background: rgba(255, 255, 255, 0.03); padding: 12px; border-radius: 10px; border-left: 3px solid #fbbf24;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; color: #fbbf24;">log_lead_time</div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">log1p transformation of heavily right-skewed booking lead days</div>
          </div>
          <div style="background: rgba(255, 255, 255, 0.03); padding: 12px; border-radius: 10px; border-left: 3px solid #fb7185;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; color: #fb7185;">previous_cancel_rate</div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Cancellations &divide; Total Prior Bookings per individual customer</div>
          </div>
          <div style="background: rgba(255, 255, 255, 0.03); padding: 12px; border-radius: 10px; border-left: 3px solid #22d3ee;">
            <div style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600; color: #22d3ee;">weekend_night_share</div>
            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Ratio of weekend nights to total length of stay</div>
          </div>
        </div>
      </div>

      <!-- Card 3 -->
      <div class="card card-highlight">
        <div class="card-title">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
          Scikit-Learn ColumnTransformer
        </div>
        <p style="font-size: 14px; color: #94a3b8; line-height: 1.45;">
          Unified transformation pipeline guaranteeing identical feature structures in training and live Streamlit serving.
        </p>
        <div style="display: flex; flex-direction: column; gap: 10px;">
          <div style="padding: 12px; background: rgba(99, 102, 241, 0.12); border-radius: 10px;">
            <strong style="color: #ffffff; font-size: 13.5px;">Numeric Pipeline:</strong>
            <div style="font-size: 12.5px; color: #cbd5e1; margin-top: 4px;">SimpleImputer(median) &rarr; StandardScaler (zero mean, unit variance)</div>
          </div>
          <div style="padding: 12px; background: rgba(6, 182, 212, 0.12); border-radius: 10px;">
            <strong style="color: #ffffff; font-size: 13.5px;">Categorical Pipeline:</strong>
            <div style="font-size: 12.5px; color: #cbd5e1; margin-top: 4px;">OneHotEncoder(handle_unknown='ignore') for meal, room, and market types</div>
          </div>
          <div style="padding: 10px 12px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; font-size: 12px; color: #34d399;">
            &check; Arrival Year excluded as direct numeric feature to prevent future year out-of-range failures.
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <div>Feature Matrix: 42 Engineered &amp; Derived Predictors Feeding Scikit-Learn Ensemble Estimators</div>
    <div class="footer-tag"><div class="footer-dot"></div> Slide 4 of 9</div>
  </div>
</div>

<!-- ==========================================
     SLIDE 5: TIME-AWARE VALIDATION STRATEGY
     ========================================== -->
<div class="slide">
  <div class="slide-header">
    <div class="slide-header-left">
      <div class="category-badge">Evaluation Rigor</div>
      <h2 class="slide-title">Time-Aware Chronological Validation</h2>
      <p class="slide-subtitle">Why random K-Fold splits fail in hospitality, and how chronological splits guarantee realistic generalization</p>
    </div>
    <div class="slide-counter">05 / 09</div>
  </div>

  <div class="slide-body">
    <div class="card" style="flex: 1.15;">
      <div class="card-title">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        The 3-Phase Chronological Split Setup
      </div>
      <p style="font-size: 14.5px; color: #94a3b8; line-height: 1.5;">
        Random K-Fold shuffling leaks future market conditions into past models (+12% artificial score inflation). We enforced strict chronological testing:
      </p>

      <div style="display: flex; flex-direction: column; gap: 10px;">
        <div class="flow-step" style="border-left: 4px solid #3b82f6;">
          <div class="flow-step-num">PHASE 1: TRAINING SET (2015 &ndash; 2016)</div>
          <div class="flow-step-title">81,918 Historical Bookings</div>
          <div class="flow-step-desc">All candidate algorithms fit exclusively on historical patterns across the source datasets with sample weighting.</div>
        </div>

        <div class="flow-step" style="border-left: 4px solid #8b5cf6;">
          <div class="flow-step-num">PHASE 2: MODEL SELECTION &amp; TUNING (2017)</div>
          <div class="flow-step-title">6,514 Target Source Bookings (Hotel Reservations)</div>
          <div class="flow-step-desc">Used to select winning candidate and tune decision threshold specifically on the target hotel distribution.</div>
        </div>

        <div class="flow-step" style="border-left: 4px solid #10b981;">
          <div class="flow-step-num">PHASE 3: DIAGNOSTIC HOLDOUT TEST (2018)</div>
          <div class="flow-step-title">29,761 Unseen Future Bookings</div>
          <div class="flow-step-desc">Final evaluation of accuracy, precision, recall, F1, and subgroup slice stability on an entirely unseen year.</div>
        </div>
      </div>
    </div>

    <div class="card" style="flex: 1.25;">
      <div class="card-title">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 14 14"/></svg>
        Decision Threshold Tuning vs. Default 0.50
      </div>
      <p style="font-size: 14.5px; color: #cbd5e1; line-height: 1.5;">
        Standard scikit-learn models assume a naive 0.50 probability cutoff. Because cancellation cost is asymmetrical, 0.50 misses valuable cancellations:
      </p>

      <div class="metric-box" style="background: rgba(99, 102, 241, 0.08); border-color: rgba(99, 102, 241, 0.35);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div class="metric-value" style="color: #818cf8; font-size: 36px;">0.4482</div>
            <div class="metric-label">Optimal Threshold Selected on 2017 Validation</div>
          </div>
          <div class="pill pill-indigo" style="font-size: 13px; padding: 6px 14px;">F1-Maximizing</div>
        </div>
      </div>

      <table class="styled-table">
        <thead>
          <tr>
            <th>Strategy</th>
            <th>Precision</th>
            <th>Recall</th>
            <th>F1-Score</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Default 0.50 Cutoff</td>
            <td>86.10%</td>
            <td>71.80%</td>
            <td>78.29%</td>
          </tr>
          <tr class="winner-row">
            <td><strong>Tuned 0.4482 Cutoff</strong></td>
            <td><strong>84.25%</strong></td>
            <td><strong>76.46%</strong></td>
            <td><strong>80.17%</strong></td>
          </tr>
        </tbody>
      </table>

      <div style="padding: 12px 16px; background: rgba(16, 185, 129, 0.08); border-radius: 8px; font-size: 13.5px; color: #34d399;">
        &check; <strong>+4.66% Gain in Recall:</strong> Identifies significantly more cancellations while preserving high precision (84.25%).
      </div>

      <div style="font-size: 12.5px; color: #94a3b8; line-height: 1.4;">
        *Note: Final production model was refit on all 160K merged rows after holdout evaluation to leverage complete historical experience.
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <div>Temporal Validation Strategy: Eliminates Look-Ahead Bias &amp; Reflects Genuine Operational Performance</div>
    <div class="footer-tag"><div class="footer-dot"></div> Slide 5 of 9</div>
  </div>
</div>

<!-- ==========================================
     SLIDE 6: CANCELLATION CLASSIFIER RESULTS
     ========================================== -->
<div class="slide">
  <div class="slide-header">
    <div class="slide-header-left">
      <div class="category-badge">Model Performance</div>
      <h2 class="slide-title">Cancellation Classification Model Results</h2>
      <p class="slide-subtitle">Benchmarking ensemble candidates on 2018 diagnostic holdout (29,761 real-world bookings)</p>
    </div>
    <div class="slide-counter">06 / 09</div>
  </div>

  <div class="slide-body">
    <div class="card" style="flex: 1.3;">
      <div class="card-title">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
        Model Tournament &amp; Evaluation Benchmarks
      </div>

      <table class="styled-table">
        <thead>
          <tr>
            <th>Model Candidate</th>
            <th>Accuracy</th>
            <th>Precision</th>
            <th>Recall</th>
            <th>F1-Score</th>
            <th>ROC-AUC</th>
          </tr>
        </thead>
        <tbody>
          <tr class="winner-row">
            <td><strong>Deep Extra Trees (Winner)</strong></td>
            <td><strong>86.12%</strong></td>
            <td><strong>84.25%</strong></td>
            <td><strong>76.46%</strong></td>
            <td><strong>80.17%</strong></td>
            <td><strong>0.9043</strong></td>
          </tr>
          <tr>
            <td>Extra Trees Classifier</td>
            <td>84.88%</td>
            <td>79.31%</td>
            <td>79.58%</td>
            <td>79.44%</td>
            <td>0.8892</td>
          </tr>
          <tr>
            <td>Random Forest Classifier</td>
            <td>81.69%</td>
            <td>77.09%</td>
            <td>71.33%</td>
            <td>74.10%</td>
            <td>0.8662</td>
          </tr>
          <tr>
            <td>Hist Gradient Boosting</td>
            <td>78.86%</td>
            <td>71.35%</td>
            <td>70.87%</td>
            <td>71.11%</td>
            <td>0.8462</td>
          </tr>
          <tr>
            <td>Majority Class Baseline</td>
            <td>63.29%</td>
            <td>0.00%</td>
            <td>0.00%</td>
            <td>0.00%</td>
            <td>0.5000</td>
          </tr>
        </tbody>
      </table>

      <div style="padding: 14px 18px; background: rgba(99, 102, 241, 0.08); border-radius: 10px; font-size: 14px; color: #a5b4fc; line-height: 1.45;">
        <strong>Winning Rationale:</strong> Deep Extra Trees achieved the highest Precision (84.25%) with exceptional ROC-AUC (0.9043), minimizing expensive false alarms where reliable guests are mistakenly penalized.
      </div>
    </div>

    <div class="card" style="flex: 1.15;">
      <div class="card-title">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg>
        Confusion Matrix &amp; Confidence Intervals
      </div>

      <div class="grid-2">
        <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: 10px; padding: 12px; text-align: center;">
          <div style="font-size: 26px; font-weight: 800; color: #34d399;">17,276</div>
          <div style="font-size: 13px; color: #94a3b8; margin-top: 2px;">True Negatives (Kept)</div>
          <div style="font-size: 11px; color: #64748b; margin-top: 2px;">58.0% of total cohort</div>
        </div>
        <div style="background: rgba(244, 63, 94, 0.08); border: 1px solid rgba(244, 63, 94, 0.25); border-radius: 10px; padding: 12px; text-align: center;">
          <div style="font-size: 26px; font-weight: 800; color: #fb7185;">1,561</div>
          <div style="font-size: 13px; color: #94a3b8; margin-top: 2px;">False Positives (False Alarm)</div>
          <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Only 5.2% false alarm rate</div>
        </div>
        <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 10px; padding: 12px; text-align: center;">
          <div style="font-size: 26px; font-weight: 800; color: #fbbf24;">2,571</div>
          <div style="font-size: 13px; color: #94a3b8; margin-top: 2px;">False Negatives (Missed)</div>
          <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Uncaught cancellations</div>
        </div>
        <div style="background: rgba(99, 102, 241, 0.08); border: 1px solid rgba(99, 102, 241, 0.25); border-radius: 10px; padding: 12px; text-align: center;">
          <div style="font-size: 26px; font-weight: 800; color: #818cf8;">8,353</div>
          <div style="font-size: 13px; color: #94a3b8; margin-top: 2px;">True Positives (Canceled)</div>
          <div style="font-size: 11px; color: #64748b; margin-top: 2px;">28.1% correctly flagged</div>
        </div>
      </div>

      <div class="grid-2">
        <div class="metric-box">
          <div class="metric-value" style="color: #38bdf8;">0.9043</div>
          <div class="metric-label">ROC-AUC Score</div>
          <div class="metric-tag">95% CI: [0.901 &ndash; 0.908]</div>
        </div>
        <div class="metric-box">
          <div class="metric-value" style="color: #34d399;">0.8614</div>
          <div class="metric-label">Average Precision (PR-AUC)</div>
          <div class="metric-tag">95% CI: [0.855 &ndash; 0.868]</div>
        </div>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <div>Diagnostic Split Results: Outperforms Naive Baseline by 22.8% Absolute Accuracy &amp; 80.2% F1</div>
    <div class="footer-tag"><div class="footer-dot"></div> Slide 6 of 9</div>
  </div>
</div>

<!-- ==========================================
     SLIDE 7: ADR PRICING REGRESSOR RESULTS
     ========================================== -->
<div class="slide">
  <div class="slide-header">
    <div class="slide-header-left">
      <div class="category-badge">Model Performance</div>
      <h2 class="slide-title">Room Rate (ADR) Pricing Regression</h2>
      <p class="slide-subtitle">Predicting fair average daily room rates and computing projected total stay revenue</p>
    </div>
    <div class="slide-counter">07 / 09</div>
  </div>

  <div class="slide-body">
    <div class="card" style="flex: 1.3;">
      <div class="card-title">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
        Pricing Regressor Benchmark (Completed Bookings)
      </div>

      <table class="styled-table">
        <thead>
          <tr>
            <th>Regressor Candidate</th>
            <th>Validation R&sup2; (2017)</th>
            <th>Holdout MAE ($)</th>
            <th>Holdout RMSE ($)</th>
            <th>Holdout R&sup2;</th>
          </tr>
        </thead>
        <tbody>
          <tr class="winner-row">
            <td><strong>Random Forest (Tuned Winner)</strong></td>
            <td><strong>0.5675</strong></td>
            <td><strong>$13.62</strong></td>
            <td><strong>$19.65</strong></td>
            <td><strong>0.7035</strong></td>
          </tr>
          <tr>
            <td>Deep Extra Trees Regressor</td>
            <td>0.5402</td>
            <td>$12.31</td>
            <td>$18.26</td>
            <td>0.7440</td>
          </tr>
          <tr>
            <td>Extra Trees Regressor</td>
            <td>0.5110</td>
            <td>$14.26</td>
            <td>$20.36</td>
            <td>0.6816</td>
          </tr>
          <tr>
            <td>Hist Gradient Boosting</td>
            <td>0.2156</td>
            <td>$16.12</td>
            <td>$22.22</td>
            <td>0.6208</td>
          </tr>
          <tr>
            <td>Ridge Regression Baseline</td>
            <td>0.2333</td>
            <td>$18.57</td>
            <td>$25.18</td>
            <td>0.5134</td>
          </tr>
        </tbody>
      </table>

      <div style="padding: 14px 18px; background: rgba(6, 182, 212, 0.08); border-radius: 10px; font-size: 14px; color: #38bdf8; line-height: 1.45;">
        <strong>Selection Criterion:</strong> Tuned Random Forest selected based on highest 2017 validation R&sup2; (0.5675), ensuring robust out-of-sample stability rather than overfitting to holdout.
      </div>
    </div>

    <div class="card" style="flex: 1.15;">
      <div class="card-title">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
        Pricing Insights &amp; Revenue Formula
      </div>

      <div class="grid-2">
        <div class="metric-box">
          <div class="metric-value" style="color: #fbbf24;">$13.62</div>
          <div class="metric-label">Mean Absolute Error (MAE)</div>
          <div class="metric-tag">95% CI: [$13.42 &ndash; $13.83]</div>
        </div>
        <div class="metric-box">
          <div class="metric-value" style="color: #34d399;">0.7035</div>
          <div class="metric-label">Variance Explained (R&sup2;)</div>
          <div class="metric-tag">70.4% Price Variance Captured</div>
        </div>
      </div>

      <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 16px;">
        <div style="font-size: 14px; font-weight: 700; color: #f8fafc; margin-bottom: 8px;">Revenue Management Workflow:</div>
        <ul class="feature-list" style="gap: 8px;">
          <li style="font-size: 13.5px;">
            <div class="check-icon">&check;</div>
            <div><strong>Trained on Completed Stays:</strong> Pricing candidates trained strictly on non-canceled reservations to reflect authentic realized market rates.</div>
          </li>
          <li style="font-size: 13.5px;">
            <div class="check-icon">&check;</div>
            <div><strong>Gross Projected Revenue:</strong> Multiplies estimated ADR by (week nights + weekend nights) for total expected booking value.</div>
          </li>
        </ul>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <div>Pricing Architecture: Enables Revenue Forecasting &amp; Dynamic Quotation Comparison</div>
    <div class="footer-tag"><div class="footer-dot"></div> Slide 7 of 9</div>
  </div>
</div>

<!-- ==========================================
     SLIDE 8: STREAMLIT APP & USER INTERFACE
     ========================================== -->
<div class="slide">
  <div class="slide-header">
    <div class="slide-header-left">
      <div class="category-badge">Deployment &amp; Software Architecture</div>
      <h2 class="slide-title">Interactive Streamlit Web Application</h2>
      <p class="slide-subtitle">Bilingual (English/Arabic) decision support system featuring single and high-speed batch inference</p>
    </div>
    <div class="slide-counter">08 / 09</div>
  </div>

  <div class="slide-body">
    <div class="grid-3" style="width: 100%;">
      <!-- Card 1 -->
      <div class="card">
        <div class="card-title">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          1. Single-Booking Scoring
        </div>
        <p style="font-size: 14px; color: #94a3b8; line-height: 1.45;">
          Interactive front-desk form for real-time quotation and reservation risk evaluation.
        </p>

        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px; padding: 12px;">
          <div style="display: flex; gap: 6px; margin-bottom: 6px;">
            <span class="pill pill-emerald" style="font-size: 11px;">Low &lt;35%</span>
            <span class="pill pill-amber" style="font-size: 11px;">Med 35&ndash;70%</span>
            <span class="pill pill-rose" style="font-size: 11px;">High &gt;70%</span>
          </div>
          <div style="font-size: 12.5px; color: #cbd5e1;">Real-time risk scoring, probability display, and recommended room rate.</div>
        </div>

        <ul class="feature-list" style="gap: 8px;">
          <li style="font-size: 13.5px;">
            <div class="check-icon">&check;</div>
            <div><strong>Instant Risk Meter:</strong> Calibrated probability score with color-coded risk bands.</div>
          </li>
          <li style="font-size: 13.5px;">
            <div class="check-icon">&check;</div>
            <div><strong>Bilingual Switch:</strong> Arabic (RTL) &amp; English localization switch.</div>
          </li>
          <li style="font-size: 13.5px;">
            <div class="check-icon">&check;</div>
            <div><strong>Projected Revenue:</strong> ADR &times; stay nights calculated instantly.</div>
          </li>
        </ul>
      </div>

      <!-- Card 2 -->
      <div class="card card-highlight">
        <div class="card-title">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
          2. High-Speed Batch CSV
        </div>
        <p style="font-size: 14px; color: #94a3b8; line-height: 1.45;">
          Enterprise batch scoring engine capable of scoring seasonal manifests in seconds.
        </p>

        <div style="background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.35); padding: 14px; border-radius: 12px; text-align: center;">
          <div style="font-family: 'Outfit', sans-serif; font-size: 30px; font-weight: 800; color: #a5b4fc;">5,870 rows/sec</div>
          <div style="font-size: 12px; color: #cbd5e1; margin-top: 2px;">Inference Engine Throughput</div>
        </div>

        <ul class="feature-list" style="gap: 8px;">
          <li style="font-size: 13.5px;">
            <div class="check-icon">&check;</div>
            <div>Up to <strong>10,000 bookings per upload</strong> with strict schema validation.</div>
          </li>
          <li style="font-size: 13.5px;">
            <div class="check-icon">&check;</div>
            <div>Downloadable input CSV template for standard hotel exports.</div>
          </li>
          <li style="font-size: 13.5px;">
            <div class="check-icon">&check;</div>
            <div>Formula-injection safe CSV export with all risk scores appended.</div>
          </li>
        </ul>
      </div>

      <!-- Card 3 -->
      <div class="card">
        <div class="card-title">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>
          3. Exploratory Data Insights
        </div>
        <p style="font-size: 14px; color: #94a3b8; line-height: 1.45;">
          Interactive Plotly dashboards delivering immediate business intelligence.
        </p>

        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 10px; padding: 12px;">
          <div style="font-size: 13px; font-weight: 600; color: #38bdf8; margin-bottom: 2px;">Interactive Plotly Visuals</div>
          <div style="font-size: 12.5px; color: #94a3b8;">Filterable by arrival year and market segment with zero page reload lag.</div>
        </div>

        <ul class="feature-list" style="gap: 8px;">
          <li style="font-size: 13.5px;">
            <div class="check-icon">&check;</div>
            <div><strong>Channel Analytics:</strong> Cancellation rates across Online, Offline, and Corporate.</div>
          </li>
          <li style="font-size: 13.5px;">
            <div class="check-icon">&check;</div>
            <div><strong>Lead-Time Distribution:</strong> Correlation between booking window and churn.</div>
          </li>
          <li style="font-size: 13.5px;">
            <div class="check-icon">&check;</div>
            <div><strong>ADR Histograms:</strong> Price distributions by month and room type.</div>
          </li>
        </ul>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <div>Deployment Architecture: python -m streamlit run app.py | Fully Self-Contained &amp; Production-Ready</div>
    <div class="footer-tag"><div class="footer-dot"></div> Slide 8 of 9</div>
  </div>
</div>

<!-- ==========================================
     SLIDE 9: SUMMARY, IMPACT & ROADMAP
     ========================================== -->
<div class="slide">
  <div class="slide-header">
    <div class="slide-header-left">
      <div class="category-badge">Conclusions &amp; Future Work</div>
      <h2 class="slide-title">Key Insights, Guardrails &amp; Next Steps</h2>
      <p class="slide-subtitle">Translating machine learning results into sustainable operational hospitality advantage</p>
    </div>
    <div class="slide-counter">09 / 09</div>
  </div>

  <div class="slide-body">
    <div class="card" style="flex: 1.1;">
      <div class="card-title">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
        Core Project Accomplishments
      </div>
      <ul class="feature-list" style="gap: 14px;">
        <li>
          <div class="check-icon">&check;</div>
          <div><strong>Dual ML Pipeline Delivered:</strong> Successfully solved classification (86.1% acc, 80.2% F1) and pricing regression ($13.62 MAE) simultaneously.</div>
        </li>
        <li>
          <div class="check-icon">&check;</div>
          <div><strong>Methodological Rigor:</strong> Zero data leakage, strict chronological time-aware split, and threshold tuning on holdout validation.</div>
        </li>
        <li>
          <div class="check-icon">&check;</div>
          <div><strong>Production Deployment:</strong> Fully functional bilingual web app with unit tests, input validation, and high throughput (&gt;5,800 rows/sec).</div>
        </li>
      </ul>

      <div style="padding: 14px 18px; background: rgba(99, 102, 241, 0.1); border-radius: 10px; border-left: 3px solid #818cf8;">
        <div style="font-size: 13.5px; font-weight: 700; color: #ffffff; margin-bottom: 4px;">Key Takeaway for Evaluation:</div>
        <p style="font-size: 13px; color: #cbd5e1; line-height: 1.5;">
          This capstone proves that high-performing ML in business requires domain-aware feature engineering and chronological validation, not just standard default hyperparameters.
        </p>
      </div>
    </div>

    <div class="card" style="flex: 1.25;">
      <div class="card-title">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
        Operational Guardrails &amp; Future Roadmap
      </div>

      <div class="grid-2">
        <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.25); border-radius: 10px; padding: 14px;">
          <h4 style="font-size: 14px; color: #fbbf24; margin-bottom: 6px;">Distribution Shift Guardrail</h4>
          <p style="font-size: 13px; color: #cbd5e1; line-height: 1.45;">
            Historical slice analysis revealed seasonal shifts (e.g., Jan 2018 low-cancellation drift). Models must be recalibrated when onboarding new hotel properties.
          </p>
        </div>

        <div style="background: rgba(6, 182, 212, 0.08); border: 1px solid rgba(6, 182, 212, 0.25); border-radius: 10px; padding: 14px;">
          <h4 style="font-size: 14px; color: #38bdf8; margin-bottom: 6px;">Live Market Data Integration</h4>
          <p style="font-size: 13px; color: #cbd5e1; line-height: 1.45;">
            Future iterations will integrate live competitor rate APIs and local events data to further improve ADR elasticity and dynamic revenue optimization.
          </p>
        </div>
      </div>

      <div style="padding: 14px 18px; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px;">
        <div style="font-size: 13.5px; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">Recommended Operational Rollout:</div>
        <div style="font-size: 13px; color: #94a3b8; line-height: 1.5;">
          1. Run parallel with existing PMS for 30 days &bull; 2. Validate calibration on current-year arrivals &bull; 3. Automate non-refundable deposit workflows for top 15% risk tier.
        </div>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <div>Hotel Reservation ML Project &bull; Full End-to-End Capstone &bull; Thank You!</div>
    <div class="footer-tag"><div class="footer-dot"></div> Slide 9 of 9</div>
  </div>
</div>

</body>
</html>
"""

def generate_pdf():
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(HTML_CONTENT)
    print(f"HTML presentation written to: {OUTPUT_HTML}")

    chrome_bin = None
    for path in CHROME_PATHS:
        if path.exists():
            chrome_bin = str(path)
            break

    if not chrome_bin:
        print("Error: Neither Google Chrome nor Microsoft Edge was found.")
        sys.exit(1)

    print(f"Using browser: {chrome_bin}")
    cmd = [
        chrome_bin,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={OUTPUT_PDF}",
        str(OUTPUT_HTML),
    ]

    subprocess.run(cmd, check=True)
    print(f"Successfully generated PDF: {OUTPUT_PDF}")

    # Check page count
    try:
        import pypdf
        reader = pypdf.PdfReader(str(OUTPUT_PDF))
        print(f"Total Pages in PDF: {len(reader.pages)}")
    except Exception as e:
        print(f"Page count check skipped: {e}")

if __name__ == "__main__":
    generate_pdf()
