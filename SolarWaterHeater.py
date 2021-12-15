#####
#Patrick Halter, 2021
#
#Write a simple software simulation of a heating solar panel connected to a tank
#
#Minimum Requirements:
##1. The system should simulate the heat transfer from a solar panel to a storage tank
##2. Use whichever coding language you wish
##3. We will evaluate thermodynamic correctness, code approach, and results.

#REQUIREMENTS: Need access to the python packages matplotlib and sys. matplotlib may only be available as part of conda
#for Windows; I'm uncertain.
#Specifically this was developed in Python 3.9.6 on Arch Linux 5.13.4

import configparser as config
import sys


try:
    sys.path.append('libs/') #add the libs to the system path so we can import them
    import SWHlib as swh
except ModuleNotFoundError:
    print('Please only run this from the base directory.')
    raise ModuleNotFoundError
    sys.exit()

#grab our config values
cfg = config.ConfigParser()
cfg.read('swh.ini')

panel = swh.Collector(cfg)
tank = swh.Tank(cfg)

sim = cfg['Simulation Times']
startTime = sim.getint('Start Time')
endTime = sim.getint('End Time')
dt = sim.getfloat('Timestep') #in hours.

timeArray = []
time = startTime
while time <= endTime:
    timeArray.append(time)
    time += dt
    
#accumulators for info
tankTemps = [tank.temp]
auxHeats = [0]

hour = startTime
for t in timeArray[:-1]:
    #update the hour so we know what irradiance to look for
    if t%1== 0:
        hour+=1
        if hour >=24:
            hour=0
    
    #calculate the collection rate of the collector, factoring in thermal and optical efficiency losses
    #First order approximation
    #dQ/dt = I*surface area * combined efficiency
    QcollectRate = panel.irr[hour] * panel.area * ((panel.optEff) - panel.insul * (panel.temp - panel.ambient))
    
    #now to deal with heat removal from the tank
    QlossRate = tank.insul * tank.area * (tank.temp - tank.ambient) #heat lost to environment

    #TODO: Figure out how to track when desired load temp is higher than tank
    #can provide and there is no aux heater
    #Also (maybe) a check to flush the tank and provide with mains water if
    #it is ever colder than mains

    loadMassRate = tank.density * tank.load[hour]/3600
    tankMassRate = loadMassRate * (tank.loadTemp - tank.mains) / (tank.temp - tank.mains) #mass-weighted temperature downmixing to the desired output temp
    
    if tank.auxHeat: #track how much energy the auxiliary heater uses
        if tank.temp < tank.auxTemp: #tank heater kicks in b/c sun isn't enough
            auxHeats.append(tank.mass*tank.cp*(tank.auxTemp - tank.temp))
            tank.temp = tank.auxTemp
        else:
            auxHeats.append(0)
            
    QoutRate = tankMassRate * tank.cp * (tank.temp - tank.mains)
    if tank.temp >= tank.loadTemp:
        QloadRate = loadMassRate * tank.cp * (tank.loadTemp - tank.mains) #downmix for desired temperature
    else: QloadRate = QoutRate

    #and now we're ready to actually do our time step
    #simple forward Euler, since 1st order is enough

    tank.temp = tank.temp + dt*3600 * (QcollectRate - QlossRate - QloadRate)/(tank.mass * tank.cp) #double check units

    if tank.temp >= tank.max: tank.temp = tank.max #clamp at max temp; simulates system shutdown or prorating flow to avoid oversafe conditions
    tankTemps.append(tank.temp)
    panel.temp = tank.temp #Since exchanger is 100%, inlet temp for the panel = tank temp
    if panel.temp >= panel.ambient: panel.temp = panel.ambient

plots = swh.Grapher(cfg)
plots.buildGraphs(startTime, endTime, tankTemps, [i/1000 for i in auxHeats], tank, panel, timeArray)
