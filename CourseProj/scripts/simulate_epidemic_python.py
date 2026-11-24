"""
simulate_epidemic_python.py
---------------------------
Spatially-explicit Agent-Based Simulation (ABM) of infectious disease spread
in Nedumangad Municipality, Kerala across all 42 official K-SMART wards.

Implements SEIR dynamics:
  S (Susceptible) -> E (Exposed) -> I (Infected) -> R (Recovered)
Integrated with real OSM road networks, 54 activity hubs, and 42 official ward populations.
Evaluates 4 intervention scenarios and logs temporal and spatial disease metrics.
"""

import json
import csv
import math
import random
import os
from collections import defaultdict

DATA_DIR = r"D:\GISLab\Prog-For-GIS\CourseProj\data"

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    a = min(1.0, max(0.0, a))
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

class Agent:
    def __init__(self, agent_id, home_lon, home_lat, ward_id, assigned_hub):
        self.id = agent_id
        self.home_lon = home_lon
        self.home_lat = home_lat
        self.cur_lon = home_lon
        self.cur_lat = home_lat
        self.ward_id = ward_id
        self.assigned_hub = assigned_hub

        self.state = 'S'
        self.days_exposed = 0
        self.days_infected = 0
        self.latent_period = max(2, int(random.gauss(3.5, 1.0)))
        self.infectious_period = max(4, int(random.gauss(6.5, 1.5)))

        self.is_isolated = False
        self.compliance = random.uniform(0.70, 0.95)

class NedumangadABM:
    def __init__(self, num_agents=2500, initial_infected=12, scenario='Baseline', seed=42):
        random.seed(seed)
        self.scenario = scenario
        self.num_agents = num_agents
        self.initial_infected = initial_infected

        self.p_hub_trans = 0.055
        self.p_loc_coef = 0.22

        self.load_gis()
        self.init_agents()

    def load_gis(self):
        with open(os.path.join(DATA_DIR, "nedumangad_hubs.geojson"), 'r', encoding='utf-8') as f:
            geo = json.load(f)
            self.hubs = [feat['properties'] for feat in geo['features']]
            for i, feat in enumerate(geo['features']):
                self.hubs[i]['lon'] = feat['geometry']['coordinates'][0]
                self.hubs[i]['lat'] = feat['geometry']['coordinates'][1]

        self.wards = []
        with open(os.path.join(DATA_DIR, "ward_healthcare_accessibility.csv"), 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.wards.append({
                    'ward_no': int(row['ward_no']),
                    'ward_name': row['ward_name'],
                    'population': int(row['population'])
                })

        self.road_nodes = []
        with open(os.path.join(DATA_DIR, "road_network_nodes.csv"), 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                self.road_nodes.append((float(r['lon']), float(r['lat'])))

        print(f"[{self.scenario}] Loaded {len(self.hubs)} Hubs, {len(self.wards)} Wards, {len(self.road_nodes)} Road Nodes.", flush=True)

    def init_agents(self):
        self.agents = []
        total_ward_pop = sum(w['population'] for w in self.wards)
        exact_allocations = [
            w['population'] / total_ward_pop * self.num_agents
            for w in self.wards
        ]
        ward_agent_counts = [int(count) for count in exact_allocations]
        remaining_agents = self.num_agents - sum(ward_agent_counts)
        remainder_order = sorted(
            range(len(self.wards)),
            key=lambda i: exact_allocations[i] - ward_agent_counts[i],
            reverse=True
        )
        for i in remainder_order[:remaining_agents]:
            ward_agent_counts[i] += 1

        agent_id = 1
        for w, w_agent_count in zip(self.wards, ward_agent_counts):
            for _ in range(w_agent_count):
                node = random.choice(self.road_nodes)
                home_lon = node[0] + random.uniform(-0.001, 0.001)
                home_lat = node[1] + random.uniform(-0.001, 0.001)
                assigned_hub = random.choice(self.hubs)
                ag = Agent(agent_id, home_lon, home_lat, w['ward_no'], assigned_hub)
                self.agents.append(ag)
                agent_id += 1

        # Seed initial infections near town center
        infected_indices = random.sample(range(len(self.agents)), self.initial_infected)
        for idx in infected_indices:
            self.agents[idx].state = 'I'
            self.agents[idx].days_infected = random.randint(1, 2)

        print(f"[{self.scenario}] Initialized {len(self.agents)} agents ({self.initial_infected} initially infected).", flush=True)

    def step(self, day):
        lockdown_active = (self.scenario == 'Lockdown' and day >= 10)
        market_closure_active = (self.scenario == 'Targeted_Closure' and day >= 8)
        quarantine_active = (self.scenario == 'Testing_Quarantine' and day >= 7)

        # 1. Testing and contact tracing isolation
        if quarantine_active:
            for ag in self.agents:
                if ag.state == 'I' and not ag.is_isolated and random.random() < 0.30:
                    ag.is_isolated = True

        # 2. Mobility to hubs
        hub_occupants = defaultdict(list)
        for ag in self.agents:
            if ag.is_isolated:
                ag.cur_lon = ag.home_lon; ag.cur_lat = ag.home_lat
                continue

            if lockdown_active and random.random() < (0.75 * ag.compliance):
                ag.cur_lon = ag.home_lon; ag.cur_lat = ag.home_lat
                continue

            hub = ag.assigned_hub
            if market_closure_active and hub.get('category') in ('Commercial', 'Transit'):
                ag.cur_lon = ag.home_lon + random.uniform(-0.0005, 0.0005)
                ag.cur_lat = ag.home_lat + random.uniform(-0.0005, 0.0005)
                continue

            if random.random() < 0.40:  # 40% daily commute probability
                ag.cur_lon = hub['lon'] + random.uniform(-0.0002, 0.0002)
                ag.cur_lat = hub['lat'] + random.uniform(-0.0002, 0.0002)
                hub_occupants[hub['id']].append(ag)
            else:
                ag.cur_lon = ag.home_lon
                ag.cur_lat = ag.home_lat

        # 3. Transmission at Activity Hubs
        for hub_id, occupants in hub_occupants.items():
            inf = [a for a in occupants if a.state == 'I']
            sus = [a for a in occupants if a.state == 'S']
            if inf and sus:
                p_trans = 1.0 - math.pow(1.0 - self.p_hub_trans, len(inf))
                for s_ag in sus:
                    if random.random() < p_trans:
                        s_ag.state = 'E'
                        s_ag.days_exposed = 0

        # 4. Street / Residential neighborhood mixing
        inf_active = [a for a in self.agents if a.state == 'I' and not a.is_isolated]
        sus_all = [a for a in self.agents if a.state == 'S']
        if inf_active and sus_all:
            mult = 0.25 if lockdown_active else 1.0
            p_loc = (len(inf_active) / self.num_agents) * self.p_loc_coef * mult
            for s_ag in sus_all:
                if s_ag.state == 'S' and random.random() < p_loc:
                    s_ag.state = 'E'
                    s_ag.days_exposed = 0

        # 5. Disease Progression (E -> I -> R)
        for ag in self.agents:
            if ag.state == 'E':
                ag.days_exposed += 1
                if ag.days_exposed >= ag.latent_period:
                    ag.state = 'I'
                    ag.days_infected = 0
            elif ag.state == 'I':
                ag.days_infected += 1
                if ag.days_infected >= ag.infectious_period:
                    ag.state = 'R'

    def run(self, days=60):
        print(f"Running simulation [{self.scenario}] for {days} days...", flush=True)
        history = []
        for d in range(1, days + 1):
            self.step(d)
            s_cnt = sum(1 for a in self.agents if a.state == 'S')
            e_cnt = sum(1 for a in self.agents if a.state == 'E')
            i_cnt = sum(1 for a in self.agents if a.state == 'I')
            r_cnt = sum(1 for a in self.agents if a.state == 'R')
            att_rate = ((self.num_agents - s_cnt) / self.num_agents) * 100.0

            history.append({
                'day': d,
                'S': s_cnt,
                'E': e_cnt,
                'I': i_cnt,
                'R': r_cnt,
                'attack_rate_pct': round(att_rate, 2)
            })

            if d % 10 == 0 or d == days:
                print(f"  Day {d:2d} | S: {s_cnt:4d} | E: {e_cnt:4d} | I: {i_cnt:4d} | R: {r_cnt:4d} | Attack Rate: {att_rate:5.1f}%", flush=True)

        return history

    def get_ward_attack_rates(self):
        ward_stats = defaultdict(lambda: {'total': 0, 'infected': 0})
        for ag in self.agents:
            ward_stats[ag.ward_id]['total'] += 1
            if ag.state in ('E', 'I', 'R'):
                ward_stats[ag.ward_id]['infected'] += 1

        results = {}
        for wid, st in ward_stats.items():
            tot = st['total']
            inf = st['infected']
            results[wid] = round((inf / tot * 100.0) if tot > 0 else 0.0, 1)
        return results

def main():
    print("=== Commencing Comparative Epidemiological Policy Experiment ===")
    scenarios = ['Baseline', 'Targeted_Closure', 'Lockdown', 'Testing_Quarantine']
    all_histories = {}
    ward_attack_rates = {}

    for sc in scenarios:
        abm = NedumangadABM(num_agents=2500, initial_infected=12, scenario=sc, seed=42)
        hist = abm.run(days=60)
        all_histories[sc] = hist
        ward_attack_rates[sc] = abm.get_ward_attack_rates()

        log_path = os.path.join(DATA_DIR, f"simulation_{sc.lower()}_log.csv")
        with open(log_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['day', 'S', 'E', 'I', 'R', 'attack_rate_pct'])
            writer.writeheader()
            writer.writerows(hist)
        print(f"Saved {log_path}", flush=True)

    # Save combined comparison log
    comb_path = os.path.join(DATA_DIR, "scenario_comparison.csv")
    with open(comb_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'day',
            'baseline_I', 'targeted_closure_I', 'lockdown_I', 'testing_quarantine_I',
            'baseline_attack_pct', 'targeted_closure_attack_pct', 'lockdown_attack_pct', 'testing_quarantine_attack_pct'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for d in range(60):
            writer.writerow({
                'day': d + 1,
                'baseline_I': all_histories['Baseline'][d]['I'],
                'targeted_closure_I': all_histories['Targeted_Closure'][d]['I'],
                'lockdown_I': all_histories['Lockdown'][d]['I'],
                'testing_quarantine_I': all_histories['Testing_Quarantine'][d]['I'],
                'baseline_attack_pct': all_histories['Baseline'][d]['attack_rate_pct'],
                'targeted_closure_attack_pct': all_histories['Targeted_Closure'][d]['attack_rate_pct'],
                'lockdown_attack_pct': all_histories['Lockdown'][d]['attack_rate_pct'],
                'testing_quarantine_attack_pct': all_histories['Testing_Quarantine'][d]['attack_rate_pct']
            })
    print(f"\nSaved combined comparison log to {comb_path}", flush=True)

    # Save ward attack rates
    ward_path = os.path.join(DATA_DIR, "ward_simulation_attack_rates.csv")
    with open(ward_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['ward_no', 'ward_name', 'baseline_attack_pct', 'targeted_closure_attack_pct', 'lockdown_attack_pct', 'testing_quarantine_attack_pct']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for w in abm.wards:
            wno = w['ward_no']
            writer.writerow({
                'ward_no': wno,
                'ward_name': w['ward_name'],
                'baseline_attack_pct': ward_attack_rates['Baseline'].get(wno, 0.0),
                'targeted_closure_attack_pct': ward_attack_rates['Targeted_Closure'].get(wno, 0.0),
                'lockdown_attack_pct': ward_attack_rates['Lockdown'].get(wno, 0.0),
                'testing_quarantine_attack_pct': ward_attack_rates['Testing_Quarantine'].get(wno, 0.0)
            })
    print(f"Saved ward attack rates to {ward_path}", flush=True)

    print("\n=== Scenario Outcomes Summary ===")
    for sc in scenarios:
        hist = all_histories[sc]
        max_i = max(h['I'] for h in hist)
        peak_day = [h['day'] for h in hist if h['I'] == max_i][0]
        final_att = hist[-1]['attack_rate_pct']
        print(f"  {sc:<20}: Peak Infections = {max_i:4d} (Day {peak_day:2d}) | Final Attack Rate = {final_att:5.1f}%")

if __name__ == '__main__':
    main()
