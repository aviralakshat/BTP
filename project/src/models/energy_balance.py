class EnergyBalance:
    def __init__(self, baseline_model):
        self.model = baseline_model

    def calculate_balance(self):
        # Energy In
        coal_energy_gcal = self.model.coal_feed_rate_tpd * self.model.coal_lhv_kcal_kg / 1000 # Gcal/day
        total_energy_in = coal_energy_gcal
        
        # Energy Out (Simplified)
        # Reduction Energy ~ 0.5 Gcal/t DRI
        reduction_energy_gcal = self.model.production_tpd * 0.5
        
        # Sensible heat in DRI (approx 0.15 Gcal/t)
        dri_sensible_gcal = self.model.production_tpd * 0.15
        
        # Off gas sensible heat
        off_gas_sensible_gcal = total_energy_in * 0.35 # Approx 35% lost to off-gas
        
        # Radiation
        radiation_gcal = total_energy_in * 0.10 # 10% lost to radiation
        
        total_energy_out = reduction_energy_gcal + dri_sensible_gcal + off_gas_sensible_gcal + radiation_gcal
        error = abs(total_energy_in - total_energy_out) / total_energy_in
        
        # Specific Energy Consumption
        sec_gcal_t_dri = total_energy_in / self.model.production_tpd
        
        return {
            "energy_in_gcal_d": total_energy_in,
            "energy_out_gcal_d": total_energy_out,
            "error_percent": error * 100,
            "sec_gcal_t_dri": sec_gcal_t_dri
        }

if __name__ == "__main__":
    from baseline import BaselineModel
    model = BaselineModel(100)
    eb = EnergyBalance(model)
    print("Energy Balance Output:", eb.calculate_balance())
