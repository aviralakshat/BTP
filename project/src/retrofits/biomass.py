class Biomass:
    def __init__(self, baseline_model, substitution_percent=0.10):
        self.model = baseline_model
        self.substitution_percent = substitution_percent
        self.biomass_lhv_kcal_kg = 3500
        self.biomass_price_t = 4000

    def calculate_impact(self):
        # Substitute based on energy
        total_coal_energy = self.model.coal_feed_rate_tpd * self.model.coal_lhv_kcal_kg
        biomass_energy = total_coal_energy * self.substitution_percent
        
        coal_displaced_tpd = self.model.coal_feed_rate_tpd * self.substitution_percent
        biomass_required_tpd = biomass_energy / self.biomass_lhv_kcal_kg
        
        return {
            "coal_displaced_tpd": coal_displaced_tpd,
            "biomass_required_tpd": biomass_required_tpd,
            "biomass_cost_d": biomass_required_tpd * self.biomass_price_t,
            "fossil_co2_reduction_tpd": coal_displaced_tpd * 2.4 # using coal EF
        }
