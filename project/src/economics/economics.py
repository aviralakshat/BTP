class EconomicsModel:
    def __init__(self, baseline_model):
        self.model = baseline_model
        
        # Default Costs in INR (₹)
        self.ore_price_t = 6000
        self.coal_price_t = 8000
        self.dolomite_price_t = 1500
        self.electricity_price_kwh = 7
        self.fixed_opex_d = 50000

    def calculate_economics(self, coal_tpd, ore_tpd, dolomite_tpd, electricity_mwh_d):
        daily_ore_cost = ore_tpd * self.ore_price_t
        daily_coal_cost = coal_tpd * self.coal_price_t
        daily_dolomite_cost = dolomite_tpd * self.dolomite_price_t
        daily_elec_cost = electricity_mwh_d * 1000 * self.electricity_price_kwh
        
        total_daily_opex = daily_ore_cost + daily_coal_cost + daily_dolomite_cost + daily_elec_cost + self.fixed_opex_d
        cost_per_t_dri = total_daily_opex / self.model.production_tpd if self.model.production_tpd > 0 else 0
        
        return {
            "total_daily_opex": total_daily_opex,
            "cost_per_t_dri": cost_per_t_dri,
            "daily_ore_cost": daily_ore_cost,
            "daily_coal_cost": daily_coal_cost
        }

if __name__ == "__main__":
    import sys
    sys.path.append('project/src/models')
    from baseline import BaselineModel
    model = BaselineModel(100)
    econ = EconomicsModel(model)
    print("Economics Output:", econ.calculate_economics(model.coal_feed_rate_tpd, model.ore_feed_rate_tpd, model.dolomite_feed_rate_tpd, 24))
