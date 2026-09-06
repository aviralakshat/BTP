class WHR:
    def __init__(self, baseline_model):
        self.model = baseline_model
        self.efficiency = 0.25 # 25% conversion of waste heat to power
        self.capex_per_mw = 60000000 # 6 Crore per MW

    def calculate_impact(self, energy_balance_result):
        # Waste heat is roughly 35% of input energy
        waste_heat_gcal_d = energy_balance_result['energy_in_gcal_d'] * 0.35
        # Convert Gcal/d to MWh/d: 1 Gcal = 1.163 MWh
        waste_heat_mwh_d = waste_heat_gcal_d * 1.163
        
        power_generated_mwh_d = waste_heat_mwh_d * self.efficiency
        power_mw = power_generated_mwh_d / 24.0
        
        total_capex = power_mw * self.capex_per_mw
        
        return {
            "power_generated_mwh_d": power_generated_mwh_d,
            "power_capacity_mw": power_mw,
            "whr_capex": total_capex
        }
