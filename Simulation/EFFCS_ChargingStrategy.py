import simpy

from Simulation.EFFCS_ChargingPrimitives import EFFCS_ChargingPrimitives

class EFFCS_ChargingStrategy (EFFCS_ChargingPrimitives):

    def __init__ (
                    self,
                    env,
                    simInput
                 ):

        self.env = \
            env

        self.simInput = \
            simInput

        self.n_charging_poles_by_zone = \
            simInput.n_charging_poles_by_zone

        self.cars_soc_dict = \
            simInput.cars_soc_dict

        if self.simInput.sim_scenario_conf["hub"]:
            self.charging_hub = simpy.Resource\
                (self.env, capacity=self.simInput.hub_n_charging_poles)

        if self.simInput.sim_scenario_conf["distributed_cps"]:
            self.charging_poles_dict = {}
            for zone, n in self.n_charging_poles_by_zone.items():
                if n > 0:
                    self.charging_poles_dict[zone] = \
                        simpy.Resource(self.env, capacity=n)

        self.sim_charges = []
        self.sim_unfeasible_charge_bookings = []

        self.n_cars_charging_system = 0
        self.n_cars_charging_users = 0
        
        self.list_system_charging_bookings = []
        self.list_users_charging_bookings = []

    def check_charge (self, booking_request, car):
                
        user_charge_flag = False
        
        # Compute hub charging params

        def compute_hub_charging_params ():

            charging_zone_id = -1
            timeout_outward = 0
            timeout_return = 0
            cr_soc_delta = 0
            unfeasible_charge_flag = False
            
            if self.simInput.sim_scenario_conf["time_estimation"]:       

                charging_zone_id = \
                    self.simInput.sim_scenario_conf["hub_zone"]
                timeout_outward = self.get_timeout\
                    (booking_request["destination_id"],
                     charging_zone_id)

                if not self.simInput.sim_scenario_conf["relocation"]:
                    timeout_return = 0
                elif self.simInput.sim_scenario_conf["relocation"]:
                    timeout_return = timeout_outward

                cr_soc_delta = self.get_cr_soc_delta\
                    (booking_request["destination_id"],
                     charging_zone_id)

                if cr_soc_delta > booking_request["end_soc"]:
                    unfeasible_charge_flag = True
                    self.sim_unfeasible_charge_bookings += \
                        [booking_request]

            else:                

                charging_zone_id = -1
                timeout_outward = 0
                timeout_return = 0
                cr_soc_delta = 0

            return unfeasible_charge_flag, \
                    charging_zone_id, \
                    timeout_outward, \
                    timeout_return, \
                    cr_soc_delta

        # Compute cp charging params
        
        def compute_cp_charging_params ():

            timeout_outward = 0
            timeout_return = 0
            cr_soc_delta = 0            
            unfeasible_charge_flag = False
            
            charging_zone_id = \
                self.simInput.closest_cp_zone\
                [booking_request["destination_id"]]

            charging_station = \
                self.charging_poles_dict\
                [charging_zone_id]

            if self.simInput.sim_scenario_conf["time_estimation"]:

                timeout_outward = self.get_timeout\
                    (booking_request["destination_id"], 
                     charging_zone_id)

                if not self.simInput.sim_scenario_conf["relocation"]:
                    timeout_return = 0
                elif self.simInput.sim_scenario_conf["relocation"]:
                    timeout_return = timeout_outward

                cr_soc_delta = self.get_cr_soc_delta\
                    (booking_request["destination_id"],
                     charging_zone_id)

                if cr_soc_delta > booking_request["end_soc"]:

                    unfeasible_charge_flag = True
                    self.sim_unfeasible_charge_bookings += \
                        [booking_request]            

            else:                

                timeout_outward = 0
                timeout_return = 0
                cr_soc_delta = 0
                
            return unfeasible_charge_flag, \
                    charging_station, \
                    charging_zone_id, \
                    timeout_outward, \
                    timeout_return, \
                    cr_soc_delta
        
        # Check charging strategy
                                
        if self.simInput.sim_scenario_conf["user_contribution"]:

            charge_flag, charge = \
                self.check_user_charge(booking_request, car)

            if charge_flag:
                
                user_charge_flag = True
                self.list_users_charging_bookings += [booking_request]

                charging_zone_id = \
                    booking_request["destination_id"]
                charging_station = \
                    self.charging_poles_dict[charging_zone_id]
                relocation_zone_id = booking_request["destination_id"]
                timeout_outward = 0
                timeout_return = 0
                cr_soc_delta = 0

                yield self.env.process\
                    (self.charge_car\
                     (charge, 
                      charging_station, 
                      car, 
                      "users",
                      charging_zone_id))

            else:
                
                charge_flag, charge = \
                    self.check_system_charge(booking_request, car)

                if charge_flag:

                    self.list_system_charging_bookings\
                        += [booking_request]    

                    if self.simInput.sim_scenario_conf["hub"]:

                        unfeasible_charge_flag, \
                        charging_zone_id, \
                        timeout_outward, \
                        timeout_return, \
                        cr_soc_delta = \
                            compute_hub_charging_params()
    
                        if not unfeasible_charge_flag:
    
                            yield self.env.process\
                               (self.charge_car\
                                (charge, 
                                 self.charging_hub, 
                                 car, 
                                 "system", 
                                 charging_zone_id,
                                 timeout_outward,
                                 timeout_return,
                                 cr_soc_delta))

                    if self.simInput.sim_scenario_conf["distributed_cps"]\
                    and self.simInput.sim_scenario_conf["system_cps"]:
                        
                        self.list_system_charging_bookings\
                            += [booking_request]

                        unfeasible_charge_flag, \
                        charging_station, \
                        charging_zone_id, \
                        timeout_outward, \
                        timeout_return, \
                        cr_soc_delta = \
                            compute_cp_charging_params()

                        if not unfeasible_charge_flag:

                            yield self.env.process\
                               (self.charge_car\
                                (charge,
                                 charging_station, 
                                 car, 
                                 "system", 
                                 charging_zone_id,
                                 timeout_outward,
                                 timeout_return,
                                 cr_soc_delta))
                    
        elif not self.simInput.sim_scenario_conf["user_contribution"]:

            charge_flag, charge = \
                self.check_system_charge(booking_request, car)

            if charge_flag:

                self.list_system_charging_bookings\
                    += [booking_request]    

                if self.simInput.sim_scenario_conf["hub"]:

                    unfeasible_charge_flag, \
                    charging_zone_id, \
                    timeout_outward, \
                    timeout_return, \
                    cr_soc_delta = \
                        compute_hub_charging_params()
                    
                    if not unfeasible_charge_flag:
                        
                        yield self.env.process\
                           (self.charge_car\
                            (charge, 
                             self.charging_hub, 
                             car, 
                             "system", 
                             charging_zone_id,
                             timeout_outward,
                             timeout_return,
                             cr_soc_delta))

                if self.simInput.sim_scenario_conf["distributed_cps"]\
                and self.simInput.sim_scenario_conf["system_cps"]:

                    unfeasible_charge_flag, \
                    charging_station, \
                    charging_zone_id, \
                    timeout_outward, \
                    timeout_return, \
                    cr_soc_delta = \
                        compute_cp_charging_params()

                    if not unfeasible_charge_flag:

                        yield self.env.process\
                           (self.charge_car\
                            (charge,
                             charging_station, 
                             car, 
                             "system", 
                             charging_zone_id,
                             timeout_outward,
                             timeout_return,
                             cr_soc_delta))
        
        # Post-charging relocation
        
        if self.simInput.sim_scenario_conf["hub"]\
        and not self.simInput.sim_scenario_conf["time_estimation"]:
            relocation_zone_id = booking_request["destination_id"]
        else:
            if charge_flag and not user_charge_flag:
                if not self.simInput.sim_scenario_conf["relocation"]:
                    relocation_zone_id = charging_zone_id
                elif self.simInput.sim_scenario_conf["relocation"]:
                    relocation_zone_id = booking_request["destination_id"]
            else:
                relocation_zone_id = booking_request["destination_id"]            
        
        return relocation_zone_id
