class MassBalance:
    def __init__(self, baseline_model):
        self.model = baseline_model
        self.tolerance = 0.05 # 5% error tolerance

    def calculate_balance(self):
        mass_in = self.model.ore_feed_rate_tpd + self.model.coal_feed_rate_tpd + self.model.dolomite_feed_rate_tpd + (self.model.air_flow_nm3_h * 24 * 1.29 / 1000) # air in tonnes
        
        # Simplified outputs
        dri_out = self.model.production_tpd
        char_out = self.model.coal_feed_rate_tpd * 0.10
        ash_out = self.model.coal_feed_rate_tpd * self.model.coal_ash_percent
        
        # Oxygen removed from ore (Fe2O3 to Fe)
        o_removed = self.model.ore_feed_rate_tpd * self.model.ore_fe2o3_percent * (48.0 / 159.7) # Mass of O in Fe2O3
        
        # Coal gasification/combustion products (simplified)
        carbon_in = self.model.coal_feed_rate_tpd * (self.model.coal_fc_percent + self.model.coal_vm_percent * 0.5)
        co2_out = carbon_in * (44.0 / 12.0)
        
        mass_out = dri_out + char_out + ash_out + co2_out + (self.model.air_flow_nm3_h * 24 * 1.0 / 1000) # remaining gas approx
        
        error = abs(mass_in - mass_out) / mass_in
        
        return {
            "mass_in_tpd": mass_in,
            "mass_out_tpd": mass_out,
            "error_percent": error * 100,
            "is_valid": error <= self.tolerance
        }

if __name__ == "__main__":
    from baseline import BaselineModel
    model = BaselineModel(100)
    mb = MassBalance(model)
    print("Mass Balance Output:", mb.calculate_balance())
