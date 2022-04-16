import math


class Psychrometrics:

    def SaturationPressure(self, temperature):
        # Using the buck equation
        return 0.61121 * math.exp((18.678 - temperature / 234.5)*(temperature / (257.14 + temperature))) * 1000

    def VapourPressure(self, temperature, relative_humidity):
        return self.SaturationPressure(temperature) * relative_humidity / 100

    def DewPoint(self, vapour_pressure):
        return (math.log(vapour_pressure / 610.78) * 237.3)/(17.27 - math.log(vapour_pressure / 610.78))

    def RelativeHumidity(self, temperature, vapour_pressure):
        return vapour_pressure / self.SaturationPressure(temperature) * 100


class IntermediateConditions:
    def __init__(self, layer, min_step=0.005):
        self.layer = layer
        self.num_step = int(math.ceil(self.layer.thickness / min_step))
        self.step = self.layer.thickness / self.num_step
        self.temperatures = []
        self.vapour_pressures = []
        self.depths = []
        for i in range(self.num_step):
            self.temperatures.append(self.layer.ti + i / self.num_step * self.layer.dt)
            self.vapour_pressures.append(self.layer.pi + i / self.num_step * self.layer.dp)
            self.depths.append(self.layer.xi + i / self.num_step * self.layer.thickness)
        self.temperatures.append(self.layer.te)
        self.vapour_pressures.append(self.layer.pe)
        self.depths.append(self.layer.xe)

        self.dew_points = []
        self.relative_humidities = []
        p = Psychrometrics()
        for i in range(self.num_step + 1):
            self.dew_points.append(p.DewPoint(self.vapour_pressures[i]))
            self.relative_humidities.append(p.RelativeHumidity(self.temperatures[i], self.vapour_pressures[i]))



class Material:

    def __init__(self, conductivity=2.0, vapour_resistivity=0.6, density=2400, heat_capacity=900, name="Default Material - Concrete"):
        self.conductivity = conductivity
        self.vapour_resistivity = vapour_resistivity
        self.density = density
        self.heat_capacity = heat_capacity
        self.name = name


    @property
    def Air(self):
        return Material(0.025, 1, 1.2, 1000, "Air") # ordinary air

    @property
    def Concrete(self):
        return Material(2.0, 80, 2400, 900, "Concrete")

    @property
    def Cork(self):
        return Material(0.05, 5, 160, 1800, "Cork")

    @property
    def Lamination(self):
        return Material(0.13, 30, 500, 1600, "Lamination")

    @property
    def VapourRetarder(self):
        return Material(0.25, 70000, 1230, 10000, "Vapour Retarder")

class Layer:

    def __init__(self, material=Material(), thickness=0.5):
        self.material = material
        self.thickness = thickness
        self.xi = 0.0
        self.ti = 15.0
        self.dt = -5.0
        self.pi = 2000
        self.dp = -300

    @property
    def Conductivity(self):
        return self.material.conductivity

    @property
    def Resistivity(self):
        return self.thickness / self.material.conductivity

    @property
    def VapourResistivity(self):
        return self.material.vapour_resistivity * self.thickness

    @property
    def te(self):
        return self.ti + self.dt

    @property
    def pe(self):
        return self.pi + self.dp

    @property
    def hi(self):
        return Psychrometrics().RelativeHumidity(self.ti, self.pi)

    @property
    def he(self):
        return Psychrometrics().RelativeHumidity(self.te, self.pe)

    @property
    def IntermediateConditions(self):
        return IntermediateConditions(self)

    @property
    def xe(self):
        return self.xi + self.thickness


class Construction:

    def __init__(self, layers=[Layer()]):
        self.layers = layers
        self.Ti = 20.0
        self.Te = 5.0
        self.Hi = 50.0
        self.He = 80.0


        self.UpdateLayers()


    @property
    def Thickness(self):
        s = 0
        for layer in self.layers:
            s += layer.thickness
        return s

    @property
    def Resistance(self):
        rr = 0
        for layer in self.layers:
            rr += layer.Resistivity
        return rr

    @property
    def VapourResistance(self):
        rr = 0
        for layer in self.layers:
            rr += layer.VapourResistivity
        return rr

    @property
    def U(self):
        return 1 / self.Resistance

    @property
    def dT(self):
        return self.Te - self.Ti

    @property
    def Pi(self):
        return Psychrometrics().VapourPressure(self.Ti, self.Hi)

    @property
    def Pe(self):
        return Psychrometrics().VapourPressure(self.Te, self.He)

    @property
    def dP(self):
        return self.Pe - self.Pi

    def UpdateLayers(self):
        T = self.Ti
        P = self.Pi
        X = 0.0
        for layer in self.layers:
            layer.dt = layer.Resistivity / self.Resistance * self.dT
            layer.ti = T
            T += layer.dt

            layer.dp = layer.VapourResistivity / self.VapourResistance * self.dP
            layer.pi = P
            P += layer.dp

            layer.xi = X
            X += layer.thickness





class Parameters:

    def __init__(self, interior_temperature=20.0, interior_humidity=50.0, exterior_temperature=5.0, exterior_humidity=80.0, interior_contact_distance = 0.00625, exterior_contact_distance = 0.001):
        self.interior_temperature = interior_temperature
        self.interior_humidity = interior_humidity
        self.exterior_temperature = exterior_temperature
        self.exterior_humidity = exterior_humidity
        self.interior_contact_distance = interior_contact_distance
        self.exterior_contact_distance = exterior_contact_distance



class Model:

    def __init__(self, construction=Construction(), parameters=Parameters()):

        self.parameters = parameters
        layers = construction.layers
        layers.insert(0, Layer(Material().Air, self.parameters.interior_contact_distance))
        layers.append(Layer(Material().Air, self.parameters.exterior_contact_distance))
        self.construction = Construction(layers)

        self.construction.Ti = self.parameters.interior_temperature
        self.construction.Hi = self.parameters.interior_humidity

        self.construction.Te = self.parameters.exterior_temperature
        self.construction.He = self.parameters.exterior_humidity
        self.construction.UpdateLayers()

class GeometryPrep:
    def __init__(self, model=Model()):
        self.model = model
        xc = []
        tc = []
        pc = []
        dpc = []
        rhc = []
        for layer in self.model.construction.layers:
            xs = layer.IntermediateConditions.depths
            xs.pop()
            xc += xs

            ts = layer.IntermediateConditions.temperatures
            ts.pop()
            tc += ts

            ps = layer.IntermediateConditions.vapour_pressures
            ps.pop()
            pc += ps

            dps = layer.IntermediateConditions.dew_points
            dps.pop()
            dpc += dps

            rhs = layer.IntermediateConditions.relative_humidities
            rhs.pop()
            rhc += rhs

        xc.append(self.model.construction.Thickness)
        tc.append(self.model.construction.Te)
        pc.append(self.model.construction.Pe)
        dpc.append(Psychrometrics().DewPoint(self.model.construction.Pe))
        rhc.append(self.model.construction.He)

        self.xc = xc
        self.tc = tc
        self.pc = pc
        self.dpc = dpc
        self.rhc = rhc



l1 = Layer(Material().Concrete, 0.3)
l2 = Layer(Material().Cork, 0.2)
l3 = Layer(Material().Lamination, 0.1)
c = Construction([l1, l2, l3])
m = Model(construction=c)
gp = GeometryPrep(m)

xc = gp.xc
tc = gp.tc
pc = gp.pc
dpc = gp.dpc
rhc = gp.rhc


