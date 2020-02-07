import os
import pickle

import pandas as pd

from DataStructures.City import City

from SingleRun.get_traceB_input import get_traceB_input
from SingleRun.get_eventG_input import get_eventG_input
from SingleRun.run_traceB_sim import run_traceB_sim
from SingleRun.run_eventG_sim import run_eventG_sim

from SimulationOutput.EFFCS_SimOutput import EFFCS_SimOutput
from SimulationOutput.EFFCS_SimOutputPlotter import EFFCS_SimOutputPlotter

from utils.path_utils import check_create_path

def single_run(city,
			   sim_general_conf,
			   sim_scenario_conf,
			   sim_type="eventG",
			   sim_scenario_name="trial"):

	results_path = os.path.join(os.getcwd(), "Results", city, "single_run")
	if not os.path.exists(results_path):
		os.mkdir(results_path)

	sim_general_conf["city"] = city
	sim_general_conf["bin_side_length"] = 500

	city_obj = City\
		(city,
		 sim_general_conf)

	if sim_type == "eventG":

		simInput_eventG = get_eventG_input\
			((sim_general_conf,
			 sim_scenario_conf,
			 city_obj))
		sim_eventG = run_eventG_sim\
			(simInput = simInput_eventG)
		simOutput_eventG = EFFCS_SimOutput(sim_eventG)
		sim_stats  = simOutput_eventG.sim_stats
		simInput = simInput_eventG
		simOutput = simOutput_eventG

	elif sim_type == "traceB":

		simInput_traceB = get_traceB_input \
			((sim_general_conf,
			  sim_scenario_conf,
			  city_obj))
		sim_traceB = run_traceB_sim \
			(simInput=simInput_traceB)
		simOutput_traceB = EFFCS_SimOutput(sim_traceB)
		sim_stats  = simOutput_traceB.sim_stats
		simInput = simInput_traceB
		simOutput = simOutput_traceB

	results_path = os.path.join(os.getcwd(), "Results", city, "single_run", sim_scenario_name)
	if not os.path.exists(results_path):
		os.mkdir(results_path)

	model_conf_string = "_".join([str(v) for v in sim_scenario_conf.values()]).replace("'", "")
	check_create_path(results_path)
	results_path = os.path.join(
		results_path,
		model_conf_string
	)
	check_create_path(results_path)

	sim_stats.to_pickle\
		(os.path.join(results_path,
					  "sim_stats.pickle"))

	pd.Series(sim_general_conf).to_pickle\
		(os.path.join(results_path,
					  "sim_general_conf.pickle"))

	pd.Series(sim_scenario_conf).to_pickle\
		(os.path.join(results_path,
					  "sim_scenario_conf.pickle"))

	simOutput.sim_booking_requests.to_pickle(
		os.path.join(
			results_path,
			"sim_booking_requests.pickle"
		)
	)
	simOutput.sim_bookings.to_pickle(
		os.path.join(
			results_path,
			"sim_bookings.pickle"
		)
	)
	simOutput.sim_charges.to_pickle(
		os.path.join(
			results_path,
			"sim_charges.pickle"
		)
	)
	simOutput.sim_deaths.to_pickle(
		os.path.join(
			results_path,
			"sim_unsatisfied_no-energy.pickle"
		)
	)
	simOutput.sim_unsatisfied_requests.to_pickle(
		os.path.join(
			results_path,
			"sim_unsatisfied_requests.pickle"
		)
	)
	simOutput.sim_system_charges_bookings.to_pickle(
		os.path.join(
			results_path,
			"sim_system_charges_bookings.pickle"
		)
	)
	simOutput.sim_users_charges_bookings.to_pickle(
		os.path.join(
			results_path,
			"sim_users_charges_bookings.pickle"
		)
	)
	simOutput.sim_unfeasible_charge_bookings.to_pickle(
		os.path.join(
			results_path,
			"sim_unfeasible_charge_bookings.pickle"
		)
	)
	simOutput.sim_charge_deaths.to_pickle(
		os.path.join(
			results_path,
			"sim_unfeasible_charges.pickle"
		)
	)
	f_out = open(
		os.path.join(
			results_path,
			"sim_output.pickle"
		), "wb"
	)
	pickle.dump(
		simOutput,
		f_out
	)

	plotter = EFFCS_SimOutputPlotter\
		(simOutput, city, simInput.grid, sim_scenario_name)

	# plotter.plot_events_profile()
	#
	# plotter.plot_charging_t_hist()
	# plotter.plot_hourly_events_boxplot("charges")
	# plotter.plot_hourly_charging_boxplot("system")
	# plotter.plot_hourly_charging_boxplot("users")
	# plotter.plot_fleet_status()
	#
	# plotter.plot_unsatisfied_t_hist()
	# plotter.plot_hourly_events_boxplot("unsatisfied")
	# plotter.plot_unsatisfied_origins_heatmap()
	#
	# plotter.plot_hourly_relocost_boxplot()
	# plotter.plot_charging_needed_heatmap_system()
	# plotter.plot_charging_needed_heatmap_users()
	#
	# plotter.plot_charging_duration_hist()
	# plotter.plot_charging_energy_avg()
	# plotter.plot_tot_energy()
	# plotter.plot_n_cars_charging()
	# plotter.plot_relo_cost_t()
	#
	# plotter.plot_origin_heatmap()
	# plotter.plot_charging_needed_heatmap_system()
	# plotter.plot_charging_needed_heatmap_users()
	# plotter.plot_unsatisfied_origins_heatmap()

	# plotter.plot_deaths_t_hist()
	# plotter.plot_deaths_origins_heatmap()
	# plotter.plot_charge_deaths_t_hist()
	# plotter.plot_charge_deaths_origins_heatmap()
