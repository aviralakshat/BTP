class Hydrogen:
    def __init__(self, baseline_model, substitution_percent=0.10):
        self.model = baseline_model
        self.substitution_percent = substitution_percent
        self.h2_lhv_kcal_kg = 28680
        self.h2_price_kg = 300 # Rs per kg
        
    def calculate_impact(self):
        # Substitute based on energy
        total_coal_energy = self.model.coal_feed_rate_tpd * self.model.coal_lhv_kcal_kg
        h2_energy = total_coal_energy * self.substitution_percent
        
        coal_displaced_tpd = self.model.coal_feed_rate_tpd * self.substitution_percent
        h2_required_tpd = h2_energy / self.h2_lhv_kcal_kg
        
        return {
            "coal_displaced_tpd": coal_displaced_tpd,
            "h2_required_tpd": h2_required_tpd,
            "h2_cost_d": h2_required_tpd * 1000 * self.h2_price_kg,
            "fossil_co2_reduction_tpd": coal_displaced_tpd * 2.4
        }
