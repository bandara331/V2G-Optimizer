class V2GOptimizer:
    def __init__(self, min_battery_reserve=20.0, max_battery=100.0, charge_rate=5.0, discharge_rate=5.0):
        self.min_battery_reserve = min_battery_reserve
        self.max_battery = max_battery
        self.charge_rate = charge_rate
        self.discharge_rate = discharge_rate
        
        # Price thresholds for decision making ($/kWh)
        self.high_price_threshold = 0.25
        self.low_price_threshold = 0.15

    def decide_action(self, current_soc, current_price, current_demand):
        """
        AI-driven "Smart Discharge" / "Smart Charge" logic.
        Returns a tuple: (action_type, energy_amount)
        action_type can be "CHARGE", "DISCHARGE", or "IDLE"
        energy_amount is the % of battery changed in this step.
        """
        
        if current_price >= self.high_price_threshold and current_demand > 50:
            # Peak Hours: High price and high demand. Discharge to support grid.
            if current_soc > self.min_battery_reserve:
                amount_to_discharge = min(self.discharge_rate, current_soc - self.min_battery_reserve)
                return "DISCHARGE", amount_to_discharge
        
        elif current_price <= self.low_price_threshold:
            # Off-Peak Hours: Low price. Charge the EV.
            if current_soc < self.max_battery:
                amount_to_charge = min(self.charge_rate, self.max_battery - current_soc)
                return "CHARGE", amount_to_charge
                
        # If neither, or battery limits reached, stay idle
        return "IDLE", 0.0
