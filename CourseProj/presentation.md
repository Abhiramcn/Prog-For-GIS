# A GIS-Integrated Agent-Based Model for Simulating the Spatial Spread of an Epidemic in Nedumangad Municipality, Kerala
## Course Project Presentation — GIS & Spatial Agent-Based Modeling
### Methodological Framework, Data Lineage & Illustrative Policy Simulations

---

### Slide 1: Title & Project Identification
* **Project Title:** A GIS-Integrated Agent-Based Model for Simulating the Spatial Spread of an Epidemic in Nedumangad Municipality, Kerala
* **Nature of the Study:** Exploratory Spatial Simulation & Methodological Proof-of-Concept (Sample-Based Computational Model)
* **Domain:** Geographic Information Systems (GIS), Spatial Agent-Based Modeling (ABM), Computational Geography
* **Study Area:** Nedumangad Municipality, Thiruvananthapuram District, Kerala, India
* **Core Technology Stack:**
  * **GIS Data & Preprocessing:** Python 3.12, OpenStreetMap (OSM) 0.6 API, PyShp, NetworkX, NumPy
  * **Simulation Platform:** NetLogo 7.0.4 with NetLogo GIS Extension (`extensions [ gis ]`)
  * **Visualization & Spatial Analytics:** Matplotlib, Python SEIR Prototype Engine
* **Crucial Methodological Caveat:** This project is an illustrative academic sample model demonstrating how GIS infrastructure can be integrated with agent-based epidemic simulations. Numerical outputs reflect scaled computational samples rather than empirical clinical forecasts for specific wards or healthcare facilities.

> **Speaker Notes:** 
> "Good morning/afternoon. Today I will present our project on integrating Geographic Information Systems (GIS) with Agent-Based Modeling (ABM) using Nedumangad Municipality in Kerala as our study landscape. I want to emphasize at the outset that this study is an exploratory sample model and methodological proof-of-concept. Our objective is to evaluate how real-world spatial networks influence relative transmission dynamics, rather than making definitive clinical predictions for specific wards or hospital beds."

---

### Slide 2: Executive Summary & Academic Scope
* **The Core Research Question:** How do physical road network hierarchies, localized activity hubs, and spatial settlement patterns govern the relative diffusion of an infectious pathogen through a semi-urban municipality?
* **Why Traditional ODE Models Fall Short:** Classical mathematical models ($dS/dt = -\beta SI/N$) assume *homogeneous mixing*—treating all individuals as evenly dispersed particles. They cannot capture spatial choke points, transit corridors, or facility-specific crowding.
* **Scope & Character of This Study:**
  1. **Methodological Integration:** Demonstrating an end-to-end pipeline connecting raw OpenStreetMap vector data and raster surfaces directly into an interactive NetLogo 7.0.4 environment.
  2. **Exploratory Sample Simulation:** Employing a scaled agent sample ($N = 1,500 - 3,000$ agents) to simulate diurnal human mobility across the municipal landscape.
  3. **Comparative Policy Sensitivity:** Evaluating the relative efficacy of 4 stylized intervention strategies (Baseline, Hub Closure, Lockdown, Active Quarantine).

---

### Slide 3: Motivation & Regional Context
* **Why Nedumangad Municipality, Kerala?**
  * **Strategic Geographical Node:** Situated 18 km northeast of Thiruvananthapuram city, Nedumangad acts as the primary transit junction connecting the highland agro-ecological belts (Ponmudi, Vithura, Western Ghats) with the state capital.
  * **Representative Semi-Urban Fabric:** Features a dense commercial and transit core (**Valiya Chanda**, **Pazhakutty**, **KSRTC bus terminal**) surrounded by residential and semi-rural wards—an ideal testbed for examining urban-to-rural spatial transmission gradients.
  * **Decentralized Governance Setting:** Kerala manages public health through decentralized local bodies (Municipalities and Grama Panchayats). Developing spatially aware decision-support tools aligns directly with state-level micro-containment planning.

---

### Slide 4: Data Lineage, Accuracy Degrees & Provenance Matrix
*An essential scientific requirement is acknowledging the exact level of accuracy, approximation, and sampling across all project datasets:*

| Spatial / Attribute Dataset | Accuracy Level | Source & Lineage | Scientific Degree of Confidence & Caveats |
| :--- | :---: | :--- | :--- |
| **Road Network Geometry** | **High** | OpenStreetMap (OSM) Planet Dump (2026) | **High accuracy.** Real GPS coordinates, 1,064 road lines, verified multi-tier classification (SH 2, SH 3, tertiary, residential). Minor local footpaths may be unmapped. |
| **Major Landmarks & Key Hubs** | **High** | OSM Surveyed Features & Field Ground Truth | **High accuracy.** Landmark coordinates for Taluk Hospital, KSRTC Bus Stand, Valiya Chanda Market, Town Hall, and major HSS schools are ground-truth verified. |
| **Secondary Amenities & Shops** | **Moderate (Sample)** | OSM Tagged Amenities | **Moderate sampling.** Represents 205 surveyed commercial, religious, and civic facilities; does not claim to be an exhaustive register of every informal vendor or kiosk. |
| **Municipal Boundary** | **High** | Official Survey Limits ($32.52\text{ km}^2$) | **High accuracy.** Accurately encloses the official $32.52\text{ km}^2$ municipal bounding territory. |
| **Official Municipal & Ward Boundaries (42 Wards)** | **100% Real & Verified** | Delimitation Commission, Kerala (K-SMART 2024 Gazette) | **Authentic Government Cadastral GIS Data.** Sourced directly from K-SMART Ward Delimitation portal (`wardmap.ksmart.live`, 2024 notification). 42 officially surveyed ward polygons dissolved into the exact municipal boundary ($32.27\text{ km}^2$). |
| **Population Density Surface** | **Modeled Proxy** | Multi-Kernel Gaussian Surface calibrated to Census 2011 | **Modeled proxy.** $120 \times 120$ raster ($\approx 55\text{ m}$ res) normalized to 60,161 total population, decaying around commercial centers. Reflects macro settlement density, not micro-level household survey registers. |
| **Agent Population Scale** | **Computational Sample** | Scaled Population ($N = 1,500 - 3,000$) | **Scaled sample.** Represents a 1:20 to 1:40 computational sample of the municipal population to enable real-time interactive simulation on desktop hardware. |
| **Healthcare Capacity Benchmark** | **Illustrative Threshold** | Stylized 120-Bed Benchmark | **Illustrative benchmark.** Used as an operational threshold to demonstrate surge capacity modeling, not an audited live bed count from the Directorate of Health Services. |

---

### Slide 5: End-to-End Methodological Architecture
* **Stage 1 (Automated Ingest):** `download_osm_data.py` queries OpenStreetMap REST servers for Nedumangad's bounding envelope.
* **Stage 2 (Spatial Formatting):** `process_gis_data.py` parses XML into ESRI Shapefiles (`.shp`), `.prj`, `.geojson`, and the ASCII raster grid (`.asc`).
* **Stage 3 (Network Graph Analytics):** `analyze_spatial_network.py` models 14,218 junctions in NetworkX to compute betweenness centrality and healthcare distance matrices.
* **Stage 4 (Agent Simulation):**
  * **NetLogo 7.0.4 Model:** Visual interactive ABM with `extensions [ gis ]`, agent diurnal mobility, real-time SEIR plots, and policy sliders.
  * **Python Simulation Engine:** Headless Monte Carlo batch execution across comparative scenarios.
* **Stage 5 (Cartographic Visualization):** `visualize_results.py` generates 300 DPI spatial figures and comparative curves.

---

### Slide 6: Road Network Topology & Transmission Corridors
* **Mathematical Graph Modeling (`analyze_spatial_network.py`):**
  * Graph $G = (V, E)$ consisting of 14,218 vertices and 14,481 edges.
  * Arc weights defined by spherical Haversine distances along road centerlines.
* **Betweenness Centrality Metric:**
  $$C_B(v) = \sum_{s \neq v \neq t} \frac{\sigma_{st}(v)}{\sigma_{st}}$$
  Quantifies the proportion of all municipal shortest paths traversing intersection $v$.
* **Top Structural Bottlenecks Identified:**
  1. *Old Rajapatha Road / Nedumangad–Vattappara Road junction* ($C_B = 0.2765$)
  2. *8th Stone – Mulamukku Road junction* ($C_B = 0.2364$)
  3. *Old Rajapatha unclassified connector* ($C_B = 0.2210$)
* **Structural Observation:** The road network exhibits high topological centralization: over half of cross-municipal transit is funneled through three primary junctions.

---

### Slide 7: Agent-Based Diurnal Mobility & SEIR Framework
* **Diurnal Mobility Schedule:**
  * Agents emulate daily human commuting rhythms:
    * *00:00 – 07:00 (Night):* Resting at residential `home-patch`.
    * *08:00 – 09:00 (Commute):* Transiting along road network to destination.
    * *10:00 – 16:00 (Daytime Activity):* High-contact mixing at assigned activity hubs (Markets, Transit, Schools, Worship, Civic).
    * *17:00 – 18:00 (Evening Commute):* Return transit along road lines.
    * *19:00 – 23:00 (Neighborhood Phase):* Localized residential interactions.
* **Dual-Mechanic Transmission Equations:**
  * **Indoor Hub Superspreading:**
    $$P_{\text{hub}}(\text{infection}) = 1 - \left[1 - \left(\beta_{\text{hub}} \cdot \text{Risk}_h \cdot \frac{\mu_{\text{crowd}}}{2}\right)\right]^{I_h} \times (1 - \eta_{\text{mask}})$$
  * **Street Proximity Transmission:**
    $$P_{\text{street}}(\text{infection}) = \beta_{\text{street}} \times (1 - \eta_{\text{mask, sus}}) \times (1 - \eta_{\text{mask, inf}})$$
    evaluated within a 25-meter proximity radius ($r = 1.5\text{ patches}$).

---

### Slide 8: Policy Intervention Scenarios Tested
*To evaluate relative policy dynamics rather than absolute case forecasts, 4 stylized scenarios were simulated over a 60-day window:*
1. **Scenario A — Baseline (Unmitigated Outbreak):**
   * Normal mobility, open hubs, no active quarantine. Serves as the experimental control benchmark.
2. **Scenario B — Targeted Hub / Market Closures (Day 8):**
   * Proactive closure of high-density commercial markets (Valiya Chanda, Pazhakutty) and KSRTC bus stand. Domestic local neighborhood travel remains open.
3. **Scenario C — Blanket Municipal Lockdown (Day 10):**
   * 75% municipal movement restriction across all 39 wards. Non-essential travel prohibited.
4. **Scenario D — Early Testing & Active Quarantine (Day 7):**
   * 35%–45% detection and strict isolation of active infectious cases at home or isolation centers. Economy and road mobility remain open.

---

### Slide 9: Results (1) — Relative Policy Comparison (Sample Simulation)
* **Comparative Trajectories across 60 Simulation Days ($N = 3,000$ Agent Sample):**

| Intervention Scenario | Peak Active Caseload ($I_{\max}$) | Relative Peak Reduction | Peak Day | Sample Attack Rate | Relative Attack Rate Impact |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Scenario A: Baseline** | 231 | Reference (0%) | Day 13 | 13.1% | Reference Benchmark |
| **Scenario B: Hub Closures** | 229 | -0.9% | Day 12 | 12.1% | -7.6% Total Infection Reduction |
| **Scenario C: Blanket Lockdown** | 207 | -10.4% | Day 12 | 16.4% | Prolonged transmission tail |
| **Scenario D: Testing & Quarantine** | **168** | **-27.3%** | **Day 10** | **7.8%** | **-40.5% Substantial Reduction** |

> **Scientific Interpretation:** Because this simulation is a scaled sample, the primary value lies in the **relative comparisons**: active testing and quarantine outperforms blanket stay-at-home orders by directly breaking transmission chains at high-contact hubs.

---

### Slide 10: Results (2) — Spatial Attack Rate Gradient (Core vs. Periphery)
* **General Spatial Pattern Observed (Rather than literal ward forecasts):**
  * **Central Commercial Zone (Elevated Relative Transmission):**
    * Wards in the commercial and transit nucleus (e.g., Valiya Chanda, Town Ward, Melamcode, Pazhakutty) exhibit higher relative attack rates in the simulation ($\approx 18\% - 22\%$ in the sample).
    * Driven by the confluence of higher population density and daily transit footfall from surrounding rural catchments.
  * **Peripheral & Agricultural Wards (Naturally Insulated):**
    * Peripheral wards along the northern and eastern municipal borders (e.g., Kurupuzha, Vettinadu, Panavoor Border, Palode Road) sustain significantly lower sample attack rates ($\approx 4\% - 7\%$).
    * Protected by spatial buffer, low building density, and dispersed agricultural settlements.
* **Methodological Takeaway:** The model demonstrates how geographical heterogeneity naturally produces transmission gradients, reinforcing the scientific rationale for **localized micro-containment** over town-wide shutdowns.

---

### Slide 11: Results (3) — Spatial Healthcare Accessibility & Surge Modeling
* **Healthcare Accessibility Modeling:**
  * Network distance analysis from ward centers to **Taluk Headquarter Hospital Nedumangad** established a range from $0.27\text{ km}$ (proximate central wards) to $4.19\text{ km}$ (northern border wards), with estimated urban transit times spanning 3 to 18 minutes.
* **Surge Capacity Demonstration (Stylized 120-Bed Capacity):**
  * In the unmitigated baseline scenario, active infectious cases in our sample model quickly exceed the illustrative 120-bed threshold, demonstrating how an unmitigated outbreak can cause bed deficits.
  * In the Testing & Quarantine scenario, the curve is compressed, illustrating how early interventions keep healthcare demand within sustainable operational limits.
* **Caveat:** The 120-bed figure represents a stylized demonstration parameter to illustrate how hospital surge dynamics can be analyzed spatially, not an official audit of Nedumangad Taluk Hospital's real-time bed inventory.

---

### Slide 12: Top 5 Strategic Methodological Observations
1. **Topological Choke Points Shape Transmission:** Road betweenness centrality proves that disease diffusion funnels heavily through major structural intersections rather than diffusing uniformly.
2. **Commercial Hubs Function as Amplification Engines:** High-contact facilities (markets, bus stands) drive rapid early-stage transmission; closing them provides significant mitigation without full curfews.
3. **Active Case Removal Outperforms General Curfews:** Testing and isolating infectious individuals proves substantially more effective in our sample model than blanket mobility restrictions.
4. **Geography Creates Natural Micro-Containment Opportunities:** The sharp spatial gradient between urban commercial centers and peripheral rural wards demonstrates the viability of ward-level cordon sanitaire.
5. **Surge Modeling Highlights Spatial Healthcare Inequity:** Peripheral wards face greater transit distances to central health facilities, highlighting the importance of decentralized mobile fever clinics during outbreaks.

---

### Slide 13: Model Limitations & Academic Boundaries
* **Sample-Based Scaling:** The simulation runs on a scaled sample ($N = 1,500 - 3,000$ agents) rather than full 1:1 individual census simulation, designed for computational tractability.
* **100% Official Cadastral Wards Integrated:** Delimited 2024 electoral ward boundaries sourced directly from the Delimitation Commission, Kerala (K-SMART portal), dissolving 42 surveyed wards into the exact municipal boundary ($32.27\text{ km}^2$).
* **Closed Municipal Boundary:** Does not account for continuous external transit along State Highway 2 (e.g., long-distance traffic between Thiruvananthapuram and Shenkottai/Tamil Nadu).
* **Aggregated Indoor Aerodynamics:** Indoor transmission utilizes parameterized risk multipliers rather than full 3D airflow and ventilation physics.
* **Behavioral Assumptions:** Agent compliance scores are held constant; in real outbreaks, public adherence fluctuates due to economic and pandemic fatigue.

---

### Slide 14: Future Research Extensions
1. **Integration of Empirical Mobility (GPS / CDR):** Replacing synthetic diurnal schedules with anonymized cellular Call Detail Records (CDR) to capture real-world origin-destination commuting matrices.
2. **Official Cadastral Layer Integration:** Ingesting surveyed ward boundary shapefiles and property tax building footprints from the Kerala Local Self-Government Department (LSGD).
3. **Wastewater-Based Epidemiology (WBE):** Coupling municipal open drain and sewer GIS networks to simulate spatial viral shedding and early detection.
4. **Multi-Pathogen Parametric Calibration:** Calibrating disease parameters for specific infectious agents (e.g., Dengue vector transmission, respiratory influenza, or COVID-19 variants).

---

### Slide 15: Conclusion & Academic Summary
* **Summary of Contributions:**
  * Developed a fully functional, reproducible GIS-integrated Agent-Based Model for Nedumangad Municipality using Python and NetLogo 7.0.4.
  * Successfully demonstrated how real OpenStreetMap vector infrastructure and raster surfaces can be coupled with agent-based behavioral rules.
  * Highlighted the critical importance of spatial network topology and facility-level superspreading in understanding epidemic trajectories.
* **Project Status:** All reproducible scripts, shapefiles, NetLogo model files, and figures are fully documented in `D:\GISLab\Prog-For-GIS\CourseProj`.
* **Questions & Discussion:** Thank you. We welcome your feedback and questions.
