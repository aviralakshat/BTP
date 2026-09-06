import math

class BaselineModel:
    def __init__(self, capacity_tpd=100, utilization=0.9):
        self.capacity_tpd = capacity_tpd
        self.utilization = utilization
        self.production_tpd = self.capacity_tpd * self.utilization
        
        # Raw Material Assumptions (Default Indian context)
        self.ore_feed_rate_tpd = self.production_tpd * 1.55 # t/t DRI
        self.coal_feed_rate_tpd = self.production_tpd * 0.95 # t/t DRI
        self.dolomite_feed_rate_tpd = self.production_tpd * 0.05 # t/t DRI
        
        # Ore Composition
        self.ore_fe_percent = 0.65
        self.ore_fe2o3_percent = 0.93
        self.ore_gangue_percent = 0.05
        self.ore_moisture = 0.02
        
        # Coal Composition
        self.coal_fc_percent = 0.40
        self.coal_vm_percent = 0.28
        self.coal_ash_percent = 0.25
        self.coal_moisture = 0.07
        self.coal_lhv_kcal_kg = 4500 # kcal/kg
        
        # Operating Conditions
        self.kiln_temp_c = 1000
        self.off_gas_temp_c = 850
        self.air_flow_nm3_h = self.production_tpd * 150 # approx Nm3/hr per TPD

    def run_simulation(self):
        """Run the full baseline simulation returning a result dictionary."""
        results = {
            "production_tpd": self.production_tpd,
            "ore_tpd": self.ore_feed_rate_tpd,
            "coal_tpd": self.coal_feed_rate_tpd,
            "dolomite_tpd": self.dolomite_feed_rate_tpd
        }
        return results

if __name__ == "__main__":
    model = BaselineModel(100)
    print("Baseline 100 TPD Output:", model.run_simulation())
