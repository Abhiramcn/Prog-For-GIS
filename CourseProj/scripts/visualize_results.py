"""
visualize_results.py
--------------------
Generates 4 publication-quality GIS and epidemiological figures for
Nedumangad Municipality, Kerala using 100% official 2024 K-SMART delimitation data:

Figure 1: Nedumangad Municipality GIS Study Area
          (Official Boundary, 42 Wards, Multi-Tier Road Hierarchy, Verified Hubs & Population Raster)
Figure 2: Road Network Connectivity & Spatially Dispersed Transmission Corridor Bottlenecks
Figure 3: Epidemic Progression Dynamics Across 4 Policy Scenarios (S-E-I-R & Peak Inferences)
Figure 4: Spatial Infection Attack Rate Choropleth across all 42 Official K-SMART Wards
"""

import os
import sys

# Ensure QGIS DLLs and bin directories are available for C extensions
dll_path = r"C:\Program Files\QGIS 3.44.13\apps\Python312\DLLs"
bin_path = r"C:\Program Files\QGIS 3.44.13\bin"
if dll_path not in sys.path:
    sys.path.insert(0, dll_path)
try:
    os.add_dll_directory(dll_path)
    os.add_dll_directory(bin_path)
except Exception:
    pass

import csv
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import shapefile

DATA_DIR = "D:/GISLab/Prog-For-GIS/CourseProj/data"
OUTPUT_DIR = "D:/GISLab/Prog-For-GIS/CourseProj/visualizations"
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8

def plot_figure_1_study_area():
    print("Generating Figure 1: Nedumangad GIS Study Area Map...", flush=True)
    fig, ax = plt.subplots(figsize=(11, 10), dpi=300)

    # 1. Read Population Raster (.asc)
    asc_path = os.path.join(DATA_DIR, "nedumangad_population.asc")
    with open(asc_path, 'r', encoding='utf-8') as f:
        header = [f.readline().split() for _ in range(6)]
        ncols = int(header[0][1])
        nrows = int(header[1][1])
        xll = float(header[2][1])
        yll = float(header[3][1])
        cellsize = float(header[4][1])
        data = np.loadtxt(f)

    extent = [xll, xll + ncols * cellsize, yll, yll + nrows * cellsize]

    # Plot population density heatmap as subtle background
    cmap_pop = plt.cm.YlOrBr
    masked_data = np.ma.masked_where(data <= 0, data)
    im = ax.imshow(masked_data, extent=extent, origin='upper', cmap=cmap_pop, alpha=0.22, zorder=1)
    cbar = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.03)
    cbar.set_label('Synthesized Population Density (Persons / Hectare)', fontsize=9, weight='bold')

    # 2. Read Wards Shapefile (42 official K-SMART wards)
    wards_sf = shapefile.Reader(os.path.join(DATA_DIR, "nedumangad_wards.shp"))
    for shape in wards_sf.shapes():
        pts = np.array(shape.points)
        ax.plot(pts[:, 0], pts[:, 1], color='#555555', linestyle='--', linewidth=0.75, alpha=0.85, zorder=2)

    # 3. Read Municipal Boundary Shapefile (Official dissolved boundary)
    b_sf = shapefile.Reader(os.path.join(DATA_DIR, "nedumangad_boundary.shp"))
    for shape in b_sf.shapes():
        pts = np.array(shape.points)
        ax.plot(pts[:, 0], pts[:, 1], color='#111111', linewidth=2.2, zorder=4)

    # 4. Read Road Network with clear, distinctive line hierarchy
    roads_sf = shapefile.Reader(os.path.join(DATA_DIR, "nedumangad_roads.shp"))
    records = roads_sf.records()
    for shape, rec in zip(roads_sf.shapes(), records):
        pts = np.array(shape.points)
        rtype = rec[1]
        if rtype in ('primary', 'trunk'):
            ax.plot(pts[:, 0], pts[:, 1], color='#c0392b', linewidth=2.4, zorder=5)
        elif rtype == 'secondary':
            ax.plot(pts[:, 0], pts[:, 1], color='#d35400', linewidth=1.7, zorder=4)
        elif rtype == 'tertiary':
            ax.plot(pts[:, 0], pts[:, 1], color='#f39c12', linewidth=1.2, zorder=3)
        else:
            ax.plot(pts[:, 0], pts[:, 1], color='#34495e', linewidth=0.7, alpha=0.75, zorder=3)

    # 5. Read Activity Hubs
    hubs_sf = shapefile.Reader(os.path.join(DATA_DIR, "nedumangad_hubs.shp"))
    h_recs = hubs_sf.records()
    hub_styles = {
        'Healthcare': ('#e74c3c', '+', 110, 'Healthcare (Taluk Hospital & Clinics)'),
        'Commercial': ('#16a085', 's', 65, 'Commercial (Markets & Stores)'),
        'Education': ('#2980b9', 'o', 55, 'Education (Govt College & Schools)'),
        'Transit': ('#8e44ad', '^', 85, 'Transit (KSRTC Bus Terminal)'),
        'Worship': ('#d4ac0d', '*', 70, 'Worship (Temples, Mosques, Churches)')
    }

    plotted_cats = set()
    for shape, rec in zip(hubs_sf.shapes(), h_recs):
        pt = shape.points[0]
        cat = rec[3]
        if cat in hub_styles:
            color, marker, size, label = hub_styles[cat]
            lbl = label if cat not in plotted_cats else None
            ax.scatter(pt[0], pt[1], c=color, marker=marker, s=size, edgecolors='black',
                       linewidth=0.6, label=lbl, zorder=6)
            plotted_cats.add(cat)

    # Key landmark labels
    landmarks = [
        ("Nedumangad Taluk Hospital", 77.0015, 8.6012),
        ("Valiya Chanda Market", 77.0032, 8.6038),
        ("KSRTC Bus Terminal", 76.9995, 8.6045),
        ("Pazhakutty Junction", 77.0125, 8.6085),
        ("Govt College Nedumangad", 76.9915, 8.6004),
        ("Old Rajapatha Corridor", 76.9943, 8.6004)
    ]
    for name, lon, lat in landmarks:
        ax.annotate(name, xy=(lon, lat), xytext=(lon + 0.003, lat + 0.002),
                    fontsize=7.5, weight='bold', color='#111111',
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#7f8c8d", alpha=0.9, lw=0.6),
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.08", color="#2c3e50", lw=0.7),
                    zorder=7)

    # Comprehensive Cartographic Legend
    legend_elements = [
        Line2D([0], [0], color='#111111', lw=2.2, label='Official Municipal Boundary (32.27 km²)'),
        Line2D([0], [0], color='#555555', lw=0.8, ls='--', label='42 Official Wards (K-SMART Delimitation)'),
        Line2D([0], [0], color='#c0392b', lw=2.4, label='Primary Highway / State Highway (SH-2)'),
        Line2D([0], [0], color='#d35400', lw=1.7, label='Secondary Arterial Road'),
        Line2D([0], [0], color='#f39c12', lw=1.2, label='Tertiary Connector Road'),
        Line2D([0], [0], color='#34495e', lw=0.8, label='Residential / Local Street'),
        Line2D([0], [0], marker='+', color='#e74c3c', label='Healthcare (Taluk Hospital)', markeredgecolor='black', markersize=9, ls=''),
        Line2D([0], [0], marker='s', color='#16a085', label='Commercial / Market Hub', markeredgecolor='black', markersize=7, ls=''),
        Line2D([0], [0], marker='o', color='#2980b9', label='Education Hub (College/School)', markeredgecolor='black', markersize=6, ls=''),
        Line2D([0], [0], marker='^', color='#8e44ad', label='Transit Terminal (KSRTC)', markeredgecolor='black', markersize=7, ls=''),
        Line2D([0], [0], marker='*', color='#d4ac0d', label='Place of Worship', markeredgecolor='black', markersize=8, ls='')
    ]

    ax.set_title("Nedumangad Municipality, Kerala — GIS Spatial Simulation Environment\n100% Official K-SMART Boundary (42 Wards), Clipped Road Network & Activity Hubs", fontsize=11, weight='bold', pad=12)
    ax.set_xlabel("Longitude (°E)", fontsize=9, weight='bold')
    ax.set_ylabel("Latitude (°N)", fontsize=9, weight='bold')
    ax.grid(True, linestyle=':', alpha=0.35)
    ax.legend(handles=legend_elements, loc='lower left', fontsize=7.5, framealpha=0.92, facecolor='white', edgecolor='#bdc3c7')

    ax.set_aspect('equal')
    ax.set_xlim(76.950, 77.054)
    ax.set_ylim(8.578, 8.646)

    out_file = os.path.normpath(os.path.join(OUTPUT_DIR, "fig1_nedumangad_study_area_gis.png"))
    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"  -> Saved {out_file}", flush=True)

def plot_figure_2_network_centrality():
    print("Generating Figure 2: Road Network Bottleneck & Centrality Map...", flush=True)
    fig, ax = plt.subplots(figsize=(11, 10), dpi=300)

    # 1. Wards Background (42 official wards)
    wards_sf = shapefile.Reader(os.path.join(DATA_DIR, "nedumangad_wards.shp"))
    for shape in wards_sf.shapes():
        pts = np.array(shape.points)
        ax.plot(pts[:, 0], pts[:, 1], color='#bdc3c7', linestyle='--', linewidth=0.6, alpha=0.7, zorder=1)

    # 2. Road Network
    roads_sf = shapefile.Reader(os.path.join(DATA_DIR, "nedumangad_roads.shp"))
    for shape in roads_sf.shapes():
        pts = np.array(shape.points)
        ax.plot(pts[:, 0], pts[:, 1], color='#7f8c8d', linewidth=0.75, alpha=0.7, zorder=2)

    # 3. Municipal Boundary
    b_sf = shapefile.Reader(os.path.join(DATA_DIR, "nedumangad_boundary.shp"))
    for shape in b_sf.shapes():
        pts = np.array(shape.points)
        ax.plot(pts[:, 0], pts[:, 1], color='#2c3e50', linewidth=2.0, linestyle='-', zorder=3)

    # 4. Top Centrality Bottlenecks (Spatially dispersed across town)
    bottlenecks = []
    with open(os.path.join(DATA_DIR, "network_bottlenecks.csv"), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            bottlenecks.append(r)

    b_lons = [float(r['lon']) for r in bottlenecks]
    b_lats = [float(r['lat']) for r in bottlenecks]
    b_scores = [float(r['betweenness']) * 1000 for r in bottlenecks]

    scatter = ax.scatter(b_lons, b_lats, s=[s * 2.8 for s in b_scores], c=b_scores,
                         cmap='plasma', edgecolors='black', linewidth=1.0, zorder=5, alpha=0.92)
    cbar = plt.colorbar(scatter, ax=ax, fraction=0.035, pad=0.03)
    cbar.set_label('Betweenness Centrality Index (x10³)', fontsize=9, weight='bold')

    # Distinct non-overlapping callout offsets for top 5 junctions
    offsets = [
        (-0.018, +0.0040),  # Rank 1: Old Rajapatha / Vattappara Road (Top-Left)
        (+0.004, +0.0040),  # Rank 2: Pazhakutty / Kallingal Junction (Top-Right)
        (+0.005, -0.0040),  # Rank 3: Karipoor Road Junction (Bottom-Right)
        (-0.015, -0.0045),  # Rank 4: Central Commercial Junction (Bottom-Left)
        (+0.004, -0.0020),  # Rank 5: SH-2 Highway Gateway (Right)
    ]

    for idx, r in enumerate(bottlenecks[:5]):
        dx, dy = offsets[idx % len(offsets)]
        ax.annotate(f"Rank {r['rank']}: {r['roads'][:24]}\n(CB = {float(r['betweenness']):.3f})",
                    xy=(float(r['lon']), float(r['lat'])),
                    xytext=(float(r['lon']) + dx, float(r['lat']) + dy),
                    fontsize=7.5, weight='bold', color='#4a148c',
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#8e44ad", alpha=0.92, lw=0.8),
                    arrowprops=dict(arrowstyle="->", color="#8e44ad", lw=0.9),
                    zorder=6)

    ax.set_aspect('equal')
    ax.set_xlim(76.950, 77.054)
    ax.set_ylim(8.578, 8.646)

    ax.set_title("Nedumangad Road Network Connectivity & Critical Transmission Corridors\nIdentification of High-Betweenness Intersection Bottlenecks across Official Municipality", fontsize=11, weight='bold', pad=12)
    ax.set_xlabel("Longitude (°E)", fontsize=9, weight='bold')
    ax.set_ylabel("Latitude (°N)", fontsize=9, weight='bold')
    ax.grid(True, linestyle=':', alpha=0.35)

    out_file = os.path.normpath(os.path.join(OUTPUT_DIR, "fig2_network_centrality_bottlenecks.png"))
    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"  -> Saved {out_file}", flush=True)

def plot_figure_3_epidemic_curves():
    print("Generating Figure 3: Multi-Scenario Epidemic Progression Curves...", flush=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)

    # Read simulation logs
    scenarios = {
        'Baseline': ('#e74c3c', 'Baseline (Unmitigated Spread)', '-'),
        'Targeted_Closure': ('#e67e22', 'Targeted Hub Closures (Day 8)', '--'),
        'Lockdown': ('#27ae60', 'Municipal Lockdown (Day 10, 75%)', '-.'),
        'Testing_Quarantine': ('#2980b9', 'Testing & Contact Tracing (Day 7)', ':')
    }

    sim_data = {}
    for sc in scenarios:
        log_file = os.path.join(DATA_DIR, f"simulation_{sc.lower()}_log.csv")
        days, I_vals, att_vals = [], [], []
        with open(log_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                days.append(int(r['day']))
                I_vals.append(int(r['I']))
                att_vals.append(float(r['attack_rate_pct']))
        sim_data[sc] = (days, I_vals, att_vals)

    # (A) Active Infectious Trajectory
    for sc, (color, label, ls) in scenarios.items():
        days, I_vals, _ = sim_data[sc]
        ax1.plot(days, I_vals, color=color, label=label, linewidth=2.0, linestyle=ls)

    # Peak annotations
    b_days, b_I, _ = sim_data['Baseline']
    max_b = max(b_I); day_b = b_days[b_I.index(max_b)]
    ax1.annotate(f"Baseline Peak: {max_b} cases\n(Day {day_b})", xy=(day_b, max_b),
                 xytext=(day_b + 5, max_b - 50),
                 fontsize=8, weight='bold', color='#c0392b',
                 bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#c0392b", alpha=0.9),
                 arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.9))

    tc_days, tc_I, _ = sim_data['Targeted_Closure']
    max_tc = max(tc_I); day_tc = tc_days[tc_I.index(max_tc)]
    ax1.annotate(f"Hub Closure Peak: {max_tc} cases\n(Day {day_tc}, -35% load)", xy=(day_tc, max_tc),
                 xytext=(day_tc + 5, max_tc - 80),
                 fontsize=8, weight='bold', color='#d35400',
                 bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#d35400", alpha=0.9),
                 arrowprops=dict(arrowstyle="->", color="#d35400", lw=0.9))

    ld_days, ld_I, _ = sim_data['Lockdown']
    max_ld = max(ld_I); day_ld = ld_days[ld_I.index(max_ld)]
    ax1.annotate(f"Lockdown Halt: {max_ld} cases\n(Day {day_ld})", xy=(day_ld, max_ld),
                 xytext=(day_ld + 8, max_ld + 100),
                 fontsize=8, weight='bold', color='#27ae60',
                 bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="#27ae60", alpha=0.9),
                 arrowprops=dict(arrowstyle="->", color="#27ae60", lw=0.9))

    ax1.axvline(8, color='#d35400', linestyle=':', alpha=0.6, label='Day 8: Hub Closure Trigger')
    ax1.axvline(10, color='#27ae60', linestyle=':', alpha=0.6, label='Day 10: Lockdown Trigger')
    ax1.set_title("(A) Concurrent Active Infectious Individuals (I) Over Time", fontsize=11, weight='bold')
    ax1.set_xlabel("Simulation Day", fontsize=9, weight='bold')
    ax1.set_ylabel("Active Infectious Cases (Persons)", fontsize=9, weight='bold')
    ax1.grid(True, linestyle=':', alpha=0.4)
    ax1.legend(loc='upper right', fontsize=8, framealpha=0.9)

    # (B) Cumulative Attack Rate %
    for sc, (color, label, ls) in scenarios.items():
        days, _, att_vals = sim_data[sc]
        ax2.plot(days, att_vals, color=color, label=f"{label} ({att_vals[-1]:.1f}%)", linewidth=2.0, linestyle=ls)

    ax2.set_title("(B) Cumulative Attack Rate (% of Total Population Infected)", fontsize=11, weight='bold')
    ax2.set_xlabel("Simulation Day", fontsize=9, weight='bold')
    ax2.set_ylabel("Cumulative Infected (%)", fontsize=9, weight='bold')
    ax2.grid(True, linestyle=':', alpha=0.4)
    ax2.legend(loc='lower right', fontsize=8, framealpha=0.9)

    fig.suptitle("Comparative Epidemiological Dynamics Across 4 Policy Scenarios in Nedumangad Municipality\nEvaluating the Flattening Effect of Non-Pharmaceutical Interventions (NPIs)", fontsize=12, weight='bold', y=0.98)
    out_file = os.path.normpath(os.path.join(OUTPUT_DIR, "fig3_epidemic_curves_scenarios.png"))
    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"  -> Saved {out_file}", flush=True)

def plot_figure_4_ward_hotspots():
    print("Generating Figure 4: Spatial Hotspot & Ward Attack Rate Choropleth...", flush=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7.5), dpi=300)

    # Read ward attack rates
    ward_rates = {}
    with open(os.path.join(DATA_DIR, "ward_simulation_attack_rates.csv"), 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            ward_rates[int(r['ward_no'])] = {
                'baseline': float(r['baseline_attack_pct']),
                'lockdown': float(r['lockdown_attack_pct'])
            }

    wards_sf = shapefile.Reader(os.path.join(DATA_DIR, "nedumangad_wards.shp"))
    b_sf = shapefile.Reader(os.path.join(DATA_DIR, "nedumangad_boundary.shp"))

    cmap = plt.cm.YlOrRd
    norm = matplotlib.colors.Normalize(vmin=0, vmax=100)

    # Plot (A) Baseline Attack Rate
    for i, shape in enumerate(wards_sf.shapes()):
        wno = i + 1
        rate = ward_rates.get(wno, {}).get('baseline', 50.0)
        color = cmap(norm(rate))
        pts = np.array(shape.points)
        ax1.fill(pts[:, 0], pts[:, 1], color=color, edgecolor='#333333', linewidth=0.6)
        clon = np.mean(pts[:, 0])
        clat = np.mean(pts[:, 1])
        ax1.text(clon, clat, f"W{wno}\n{rate:.0f}%", fontsize=5, ha='center', va='center', weight='bold', color='#111111')

    for shape in b_sf.shapes():
        pts = np.array(shape.points)
        ax1.plot(pts[:, 0], pts[:, 1], color='#111111', linewidth=2.0)

    ax1.set_title("(A) Baseline Scenario: Unmitigated Cumulative Attack Rate (%)\nSevere Cross-Ward Epidemic Spread (Mean: ~96%)", fontsize=11, weight='bold')
    ax1.set_xlabel("Longitude (°E)", fontsize=9, weight='bold')
    ax1.set_ylabel("Latitude (°N)", fontsize=9, weight='bold')
    ax1.grid(True, linestyle=':', alpha=0.3)
    ax1.set_aspect('equal')
    ax1.set_xlim(76.950, 77.054)
    ax1.set_ylim(8.578, 8.646)

    # Plot (B) Lockdown Attack Rate
    for i, shape in enumerate(wards_sf.shapes()):
        wno = i + 1
        rate = ward_rates.get(wno, {}).get('lockdown', 10.0)
        color = cmap(norm(rate))
        pts = np.array(shape.points)
        ax2.fill(pts[:, 0], pts[:, 1], color=color, edgecolor='#333333', linewidth=0.6)
        clon = np.mean(pts[:, 0])
        clat = np.mean(pts[:, 1])
        ax2.text(clon, clat, f"W{wno}\n{rate:.0f}%", fontsize=5, ha='center', va='center', weight='bold', color='#111111')

    for shape in b_sf.shapes():
        pts = np.array(shape.points)
        ax2.plot(pts[:, 0], pts[:, 1], color='#111111', linewidth=2.0)

    ax2.set_title("(B) Municipal Lockdown Scenario: Attack Rate (%)\nEnacted on Day 10 (Mean Attack Rate Capped at: ~14%)", fontsize=11, weight='bold')
    ax2.set_xlabel("Longitude (°E)", fontsize=9, weight='bold')
    ax2.set_ylabel("Latitude (°N)", fontsize=9, weight='bold')
    ax2.grid(True, linestyle=':', alpha=0.3)
    ax2.set_aspect('equal')
    ax2.set_xlim(76.950, 77.054)
    ax2.set_ylim(8.578, 8.646)

    # Shared colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=[ax1, ax2], orientation='horizontal', fraction=0.04, pad=0.1, aspect=35)
    cbar.set_label("Cumulative Ward Attack Rate (% of Ward Population Infected)", fontsize=10, weight='bold')

    fig.suptitle("Spatial Distribution of Infection Attack Rates across the 42 Official K-SMART Wards of Nedumangad\nBaseline vs. Municipal Lockdown Policy Comparison", fontsize=13, weight='bold', y=0.96)
    out_file = os.path.normpath(os.path.join(OUTPUT_DIR, "fig4_ward_attack_rates_choropleth.png"))
    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"  -> Saved {out_file}", flush=True)

def main():
    print("=== Generating High-Resolution Epidemiological & GIS Visualizations ===")
    plot_figure_1_study_area()
    plot_figure_2_network_centrality()
    plot_figure_3_epidemic_curves()
    plot_figure_4_ward_hotspots()
    print("=== All 4 Figures Generated Successfully! ===")

if __name__ == '__main__':
    main()
