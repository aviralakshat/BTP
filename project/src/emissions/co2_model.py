class CO2Model:
    def __init__(self, baseline_model):
        self.model = baseline_model
        
        # Default emission factors (t CO2 / t)
        self.ef_coal = 2.4 # t CO2 / t coal
        self.ef_electricity = 0.82 # t CO2 / MWh

    def calculate_emissions(self, coal_consumption_tpd, electricity_mwh_d):
        fossil_co2_tpd = coal_consumption_tpd * self.ef_coal
        electricity_co2_tpd = electricity_mwh_d * self.ef_electricity
        
        total_co2_tpd = fossil_co2_tpd + electricity_co2_tpd
        co2_per_t_dri = total_co2_tpd / self.model.production_tpd if self.model.production_tpd > 0 else 0
        
        return {
            "total_co2_tpd": total_co2_tpd,
            "fossil_co2_tpd": fossil_co2_tpd,
            "electricity_co2_tpd": electricity_co2_tpd,
            "co2_per_t_dri": co2_per_t_dri
        }

if __name__ == "__main__":
    import sys
    sys.path.append('project/src/models')
    from baseline import BaselineModel
    model = BaselineModel(100)
    co2 = CO2Model(model)
    print("CO2 Emissions:", co2.calculate_emissions(model.coal_feed_rate_tpd, 24))
