#####
#Patrick Halter, 2021
#
#Write a simple software simulation of a heating solar panel connected to a tank
#
#Minimum Requirements:
##1. The system should simulate the heat transfer from a solar panel to a storage tank
##2. Use whichever coding language you wish
##3. We will evaluate thermodynamic correctness, code approach, and results.

###
#ASSUMPTIONS & SIMPLIFICATIONS
###

#1. This solar heater is used for heating water for building use. The code is agnostic
#about what for, but does not simulate anything like an exchanger, considering only
#removal of hot working fluid from the tank and replacement with fluid of some other temperature.
#2. Angle of the solar collector does not change. Instead this is subsumed in change in solar irradiance.
#3. Movement of working fluid between tank and panel is adiabatic. The lines are unimportant.
#4. The tank is perfectly mixed. Mixing takes no energy.
#5. Ambient conditions (temperature, heat transfer coefficients from tank and panel) do not change.
#6. Working fluid experiences no appreciable changes in density, specific volume, pressure, or specific heat capacity
#7. Collector working fluid and tank fluid are not necessarily the same, but the working fluid
#   coming from the tank to the collector is equal to the average tank temperature - heat transfer to equilibrium
#7a.In other words, exchanger efficiency is 100%
#8. Net heat flow from collector to tank is never negative. (Justification: temperature sensors allow flow shutdown.)


from matplotlib import pyplot as plt

def c2k (centigrade): 
    return (centigrade+273)

#cfg = config.ConfigParser()
#cfg.read('../swh.ini')
#panelcfg = cfg['Panel']
#solarcfg = cfg['Solar']
#tankcfg = cfg['Tank']
#loadcfg = cfg['Load']

class Collector:
    def __init__ (self, cfg):

        panelcfg = cfg['Panel']
        solarcfg = cfg['Solar']

        self.area = panelcfg.getfloat('Area')
        self.optEff = panelcfg.getfloat('Optical Eff')
        self.insul = panelcfg.getfloat('Insul')
        self.fluid = panelcfg['Fluid']
        self.density = panelcfg.getfloat('Density')
        self.cp = panelcfg.getfloat('Cp') 
        self.ambient = panelcfg.getfloat('Ambient') #TODO: give range (or function) of ambient temp for hourly variation
        self.temp = panelcfg.getfloat('Start Temp')

        self.irr = [float(val) for val in solarcfg['Irradiance'].split(' ')]
        


class Tank:
    def __init__ (self, cfg):
        tankcfg = cfg['Tank']
        loadcfg = cfg['Load']

        self.vol = tankcfg.getfloat('Volume')
        self.area =  tankcfg.getfloat('Area')
        self.insul = tankcfg.getfloat('Insul')
        self.fluid = tankcfg['Fluid']
        self.density = tankcfg.getfloat('Density')
        self.mass = self.vol * self.density
        self.cp = tankcfg.getfloat('Cp') 
        self.ambient = tankcfg.getfloat('Ambient') #TODO: give range (or function) of ambient temp for hourly variation
        self.mains = tankcfg.getfloat('Mains Temp')
        self.temp = tankcfg.getfloat('Start Temp')
        self.max = tankcfg.getfloat('Max Temp')

        self.auxHeat = tankcfg.getboolean('Aux Heat')
        if self.auxHeat:
            self.auxTemp = tankcfg.getfloat('Aux Temp')

        self.load = [float(val) for val in loadcfg['Profile'].split(' ')]
        self.loadTemp = loadcfg.getfloat('Temp')

class Grapher:
    def __init__ (self, cfg):
        graphcfg = cfg['Graphing']

        self.tankGraph = graphcfg.getboolean('Tank Temperature')
        self.auxGraph = graphcfg.getboolean('Aux Heating')
        self.loadGraph = graphcfg.getboolean('Load')
        self.irrGraph = graphcfg.getboolean('Irradiance')

    def buildGraphs(self, startTime, endTime, temps, auxHeats, tank, panel, times):
        if self.tankGraph:
            #xarray = [i for i in range (startTime, endTime+1)]
            tankPlot = plt.subplot()
            #plt.figure(fig)
            tankPlot.plot(times, temps, 'b^-')
            #tankPlot.axis('tight')
            tankPlot.set_xlabel('Hours Elapsed')
            tankPlot.set_ylabel('Tank temperature, Celsius')
            plt.title('System Performance over {} hours'.format(endTime-startTime))
            
        if self.auxGraph:
            try: QPlot = tankPlot.twinx()
            except: print("You must graph tank temperature to view auxiliary heating.")
            QPlot.set_ylabel('Auxiliary heating, kJ')
            QPlot.plot(times, auxHeats, 'r*-')

        if self.loadGraph:
            plt.figure(2)
            plt.plot(range(24), tank.load)
            plt.xlabel('Hour of the Day')
            plt.ylabel('Water demand, Liters')
            plt.title('Daily load profile, desired temp {} °C'.format(tank.loadTemp))

        if self.irrGraph:
            plt.figure(3)
            plt.plot(range(24), panel.irr)
            plt.xlabel('Hour of the Day')
            plt.ylabel('Irradiance, W/sq meter')
            plt.title('Solar energy profile')
                      
        
        plt.show()
        
