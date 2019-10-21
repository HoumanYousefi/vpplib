# -*- coding: utf-8 -*-
"""
Created on Tue Jul  2 10:38:17 2019

@author: Sascha Birk
"""

import pandas as pd
import pandapower as pp
import pandapower.networks as pn

from model.VPPEnvironment import VPPEnvironment
from model.VPPUserProfile import VPPUserProfile
from model.VPPPhotovoltaic import VPPPhotovoltaic
from model.VPPBEV import VPPBEV
from model.VPPHeatPump import VPPHeatPump
from model.VPPEnergyStorage import VPPEnergyStorage
from model.VPPWind import VPPWind
from model.VirtualPowerPlant import VirtualPowerPlant
from model.VPPOperator import VPPOperator

import logging
logging.getLogger().setLevel(logging.DEBUG)



#environment
start = '2017-03-01 00:00:00'
end = '2017-03-01 23:45:00'
timezone = 'Europe/Berlin'
year = '2017'
time_freq = "15 min"
timebase=15
index=pd.date_range(start=start, end=end, freq=time_freq)

#user_profile
identifier = "bus_1"
latitude = 50.941357
longitude = 6.958307
yearly_heat_demand = 12500
comfort_factor=None
daily_vehicle_usage=None
building_type = 'DE_HEF33'
t_0 = 40
week_trip_start=[]
week_trip_end=[]
weekend_trip_start=[]
weekend_trip_end=[]

baseload = pd.read_csv("./Input_House/Base_Szenario/df_S_15min.csv")
baseload.set_index("Time", inplace=True)
baseload.index = pd.to_datetime(baseload.index)

unit = "kW"

#WindTurbine data
turbine_type = 'E-126/4200'
hub_height = 135
rotor_diameter = 127
fetch_curve = 'power_curve'
data_source = 'oedb'

#Wind ModelChain data
wind_file = "./Input_House/wind/dwd_wind_data_2017.csv"
wind_speed_model = 'logarithmic'
density_model = 'ideal_gas'
temperature_model = 'linear_gradient'
power_output_model = 'power_curve'
density_correction = True
obstacle_height = 0
hellman_exp = None

#PV data
module_lib = 'SandiaMod'
module = 'Canadian_Solar_CS5P_220M___2009_'
inverter_lib = 'cecinverter'
inverter = 'ABB__PVI_4_2_OUTD_S_US_Z_M_A__208_V__208V__CEC_2014_'
surface_tilt = 20, 
surface_azimuth = 200
modules_per_string = 4
strings_per_inverter = 2

#BEV data
battery_max = 16
battery_min = 0
battery_usage = 1
charging_power = 11
charge_efficiency_bev = 0.98

#heat pump data
heatpump_type="Air"
heat_sys_temp=60
el_power=5
building_type = 'DE_HEF33'

#storage
charge_efficiency_storage = 0.98
discharge_efficiency_storage = 0.98
max_power = 4 #kW
capacity = 4 #kWh
max_c = 1 #factor between 0.5 and 1.2

#%% define the amount of components in the grid
# NOT VALIDE for all component distribution methods (see line 131-143)

pv_percentage = 50
storage_percentage = 50
bev_percentage = 0
hp_percentage = 0
wind_percentage = 0

#%% environment

environment = VPPEnvironment(timebase=timebase, timezone=timezone, 
                             start=start, end=end, year=year,
                             time_freq=time_freq)

environment.get_wind_data(file=wind_file, utc=False)

#%% user profile

user_profile = VPPUserProfile(identifier=identifier,
                     latitude=latitude,
                     longitude=longitude,
                     yearly_heat_demand=yearly_heat_demand,
                     building_type=building_type,
                     comfort_factor=comfort_factor,
                     t_0=t_0, year=year,
                     daily_vehicle_usage=daily_vehicle_usage,
                     week_trip_start=week_trip_start, 
                     week_trip_end=week_trip_end,
                     weekend_trip_start=weekend_trip_start, 
                     weekend_trip_end=weekend_trip_end)

#%% create instance of VirtualPowerPlant and the designated grid
vpp = VirtualPowerPlant("Master")

net = pn.panda_four_load_branch()

#%% assign names and types to baseloads for later p and q assignment
for bus in net.bus.index:
    
    net.load.name[net.load.bus == bus] = net.bus.name[bus]+'_baseload'
    net.load.type[net.load.bus == bus] = 'baseload'

#%% assign components to random bus names

def test_get_buses_with_components(vpp):
    vpp.get_buses_with_components(net, method='random', 
                                          pv_percentage=pv_percentage,
                                          hp_percentage=hp_percentage,
                                          bev_percentage=bev_percentage,
                                          wind_percentage=wind_percentage,
                                          storage_percentage=storage_percentage)


#%% assign components to the bus names for testing purposes
    
def test_get_assigned_buses_with_components(vpp, 
                                            buses_with_pv,
                                            buses_with_hp,
                                            buses_with_bev,
                                            buses_with_storage,
                                            buses_with_wind):
    
    vpp.buses_with_pv = buses_with_pv
    
    vpp.buses_with_hp = buses_with_hp
    
    vpp.buses_with_bev = buses_with_bev
    
    vpp.buses_with_wind = buses_with_wind
    
    # storages should only be assigned to buses with pv
    vpp.buses_with_storage = buses_with_storage


    
#%% assign components to the loadbuses

def test_get_loadbuses_with_components(vpp):
    
    vpp.get_buses_with_components(net, method='random_loadbus',
                                       pv_percentage=pv_percentage,
                                       hp_percentage=hp_percentage,
                                       bev_percentage=bev_percentage,
                                       wind_percentage=wind_percentage,
                                       storage_percentage=storage_percentage)


#%% Choose assignment methode for component distribution
    
#test_get_buses_with_components(vpp)
    
test_get_assigned_buses_with_components(vpp, 
                                        buses_with_pv = ['bus3', 'bus4', 'bus5', 'bus6'],
                                        buses_with_hp = ['bus4'],
                                        buses_with_bev = ['bus5'],
                                        buses_with_storage = ['bus5'],
                                        buses_with_wind = ['bus1'])
    
#test_get_loadbuses_with_components(vpp)

#%% create components and assign components to the Virtual Powerplant

for bus in vpp.buses_with_pv:
    
    vpp.addComponent(VPPPhotovoltaic(unit=unit, identifier=(bus+'_PV'),  
                                     environment = environment, 
                                     user_profile = user_profile,
                                     module_lib = module_lib, 
                                     module = module, 
                                     inverter_lib = inverter_lib, 
                                     inverter = inverter,
                                     surface_tilt = surface_tilt, 
                                     surface_azimuth = surface_azimuth,
                                     modules_per_string = modules_per_string, 
                                     strings_per_inverter = strings_per_inverter))
    
    vpp.components[list(vpp.components.keys())[-1]].prepareTimeSeries()
    
    
for bus in vpp.buses_with_storage:
    
    vpp.addComponent(VPPEnergyStorage(unit=unit, 
                                      identifier=(bus+'_storage'), 
                                      environment=environment, 
                                      user_profile=user_profile, 
                                      capacity=capacity, 
                                      charge_efficiency=charge_efficiency_storage, 
                                      discharge_efficiency=discharge_efficiency_storage, 
                                      max_power=max_power, max_c=max_c))
    
    vpp.components[
            list(vpp.components.keys())[-1]].timeseries = pd.DataFrame(
            columns=['state_of_charge','residual_load'], 
            index=pd.date_range(start=start, end=end, freq=time_freq))
    
    
for bus in vpp.buses_with_bev:
    
    vpp.addComponent(VPPBEV(unit=unit, identifier=(bus+'_BEV'), 
                            environment=environment, user_profile=user_profile, 
                            battery_max=battery_max, battery_min=battery_min, 
                            battery_usage=battery_usage, 
                            charging_power=charging_power, 
                            charge_efficiency=charge_efficiency_bev))
    
    vpp.components[list(vpp.components.keys())[-1]].prepareTimeSeries()
    
    
for bus in vpp.buses_with_hp:
    
    vpp.addComponent(VPPHeatPump(unit=unit,identifier=(bus+'_HP'),  
                                 environment=environment, 
                                 user_profile=user_profile,
                                 heatpump_type=heatpump_type, 
                                 heat_sys_temp=heat_sys_temp, 
                                 el_power=el_power))
    
    vpp.components[list(vpp.components.keys())[-1]].prepareTimeSeries()
    
for bus in vpp.buses_with_wind:
    
    vpp.addComponent(VPPWind(unit=unit, identifier = (bus+'_Wind'), 
                 environment=environment, user_profile=user_profile,
                 turbine_type=turbine_type, hub_height=hub_height,
                 rotor_diameter=rotor_diameter, fetch_curve=fetch_curve,
                 data_source=data_source,
                 wind_speed_model=wind_speed_model, 
                 density_model=density_model,
                 temperature_model=temperature_model, 
                 power_output_model=power_output_model, 
                 density_correction=density_correction,
                 obstacle_height=obstacle_height, 
                 hellman_exp=hellman_exp))
    
    vpp.components[list(vpp.components.keys())[-1]].prepareTimeSeries()

#%% create elements in the pandapower.net

for bus in vpp.buses_with_pv:
    
    pp.create_sgen(net, bus=net.bus[net.bus.name == bus].index[0], 
                  p_mw=(vpp.components[bus+'_PV'].module.Impo*vpp.components[bus+'_PV'].module.Vmpo/1000000),
                  name=(bus+'_PV'), type = 'PV')    

for bus in vpp.buses_with_storage:
    
    pp.create_storage(net, bus=net.bus[net.bus.name == bus].index[0],
                      p_mw=0, max_e_mwh=capacity, name=(bus+'_storage'), type='LiIon')
  
for bus in vpp.buses_with_bev:
    
    pp.create_load(net, bus=net.bus[net.bus.name == bus].index[0], 
                   p_mw=(vpp.components[bus+'_BEV'].charging_power/1000), name=(bus+'_BEV'), type='BEV')
    
for bus in vpp.buses_with_hp:
    
    pp.create_load(net, bus=net.bus[net.bus.name == bus].index[0], 
                   p_mw=(vpp.components[bus+'_HP'].el_power/1000), name=(bus+'_HP'), type='HP')
    
for bus in vpp.buses_with_wind:
    
    pp.create_sgen(net, bus=net.bus[net.bus.name == bus].index[0], 
                  p_mw=(vpp.components[bus+'_Wind'].wind_turbine.nominal_power/1000000),
                  name=(bus+'_Wind'), type = 'Wind')
    
#%% initialize operator

operator = VPPOperator(virtualPowerPlant=vpp, net=net, targetData=None)

#%% run base_scenario without operation strategies

net_dict = operator.run_base_scenario(baseload)    

#%% extract results from powerflow

results = operator.extract_results(net_dict)
single_result = operator.extract_single_result(net_dict, res='ext_grid', value='p_mw')

#%% plot results of powerflow and storage values

single_result.plot(figsize=(16,9), title='ext_grid from single_result function')
operator.plot_results(results)
operator.plot_storages()
