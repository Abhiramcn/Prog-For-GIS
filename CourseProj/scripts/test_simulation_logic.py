import unittest
from unittest.mock import patch

from process_gis_data import generate_wards_and_boundary
from simulate_epidemic_python import Agent, NedumangadABM


class SimulationLogicTests(unittest.TestCase):
    def test_generated_ward_populations_match_census_total(self):
        wards, _ = generate_wards_and_boundary()

        self.assertEqual(len(wards), 39)
        self.assertEqual(sum(ward['population'] for ward in wards), 60161)

    def test_agent_initialization_matches_requested_population(self):
        simulation = NedumangadABM.__new__(NedumangadABM)
        simulation.scenario = 'Baseline'
        simulation.num_agents = 10
        simulation.initial_infected = 0
        simulation.wards = [
            {'ward_no': 1, 'ward_name': 'One', 'population': 1},
            {'ward_no': 2, 'ward_name': 'Two', 'population': 1},
            {'ward_no': 3, 'ward_name': 'Three', 'population': 1}
        ]
        simulation.road_nodes = [(77.0, 8.6)]
        simulation.hubs = [{'id': 1, 'lon': 77.0, 'lat': 8.6}]

        simulation.init_agents()

        self.assertEqual(len(simulation.agents), simulation.num_agents)

    def test_street_transmission_checks_adjacent_spatial_buckets(self):
        simulation = NedumangadABM.__new__(NedumangadABM)
        simulation.scenario = 'Baseline'
        simulation.beta_street = 0.08
        simulation.beta_hub_base = 0.16
        simulation.street_radius_m = 25.0
        latitude = 8.6
        first_hub = {'id': 1, 'lon': 77.00099, 'lat': latitude}
        second_hub = {'id': 2, 'lon': 77.00101, 'lat': latitude}
        infectious = Agent(1, first_hub['lon'], latitude, 1, first_hub)
        susceptible = Agent(2, second_hub['lon'], latitude, 1, second_hub)
        infectious.state = 'I'
        susceptible.state = 'S'
        infectious.latent_period = susceptible.latent_period = 5
        simulation.agents = [infectious, susceptible]

        with patch('simulate_epidemic_python.random.uniform', return_value=0.0), \
                patch('simulate_epidemic_python.random.random', return_value=0.0):
            metrics = simulation.step(1)

        self.assertNotEqual(
            int(first_hub['lon'] * 1000),
            int(second_hub['lon'] * 1000)
        )
        self.assertEqual(metrics['new_infections'], 1)


if __name__ == '__main__':
    unittest.main()
