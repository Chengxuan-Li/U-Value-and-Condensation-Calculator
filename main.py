class Material:

    def __init__(self, conductivity=2.0, vapour_resistance=0.6, density=2400, heat_capacity=900, name="Default Material - Concrete"):
        self.conductivity = conductivity
        self.vapour_resistance = vapour_resistance
        self.density = density
        self.heat_capacity = heat_capacity
        self.name = name


    @property
    def Air(self):
        return Material(0.025, 1, 1.2, 1000, "Air") # ordinary air

    @property
    def Concrete(self):
        return Material(2.0, 8/13, 2400, 900, "Concrete")

    @property
    def Cork(self):
        return Material(0.05, 0.5, 160, 1800, "Cork")

    @property
    def Lamination(self):
        return Material(0.13, 3/8, 500, 1600, "Lamination")

class Layer:

    def __init__(self, material=Material(), thickness=0.5):
        self.material = material
        self.thickness = thickness
        self.ti = 15.0
        self.dt = -5.0

    @property
    def Conductivity(self):
        return self.material.conductivity

    @property
    def Resistivity(self):
        return self.thickness / self.material.conductivity

    @property
    def te(self):
        return self.ti + self.dt



class Construction:

    def __init__(self, layers=[Layer()]):
        self.layers = layers
        self.Ti = 20.0
        self.Te = 5.0
        self.UpdateLayers()


    @property
    def Resistance(self):
        rr = 0
        for layer in self.layers:
            rr += layer.Resistivity
        return rr

    @property
    def U(self):
        return 1 / self.Resistance

    @property
    def dT(self):
        return self.Te - self.Ti

    def UpdateLayers(self):
        T = self.Ti
        for layer in self.layers:
            layer.dt = layer.Resistivity / self.Resistance * self.dT
            layer.ti = T
            T += layer.dt



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
        layers = construction.layers.copy()
        layers.insert(0, Layer(Material().Air, self.parameters.interior_contact_distance))
        layers.append(Layer(Material().Air, self.parameters.exterior_contact_distance))
        self.construction = Construction(layers)
        self.construction.Te = self.parameters.exterior_temperature
        self.construction.Ti = self.parameters.interior_temperature



l1 = Layer(Material().Concrete, 0.3)
l2 = Layer(Material().Cork, 0.2)
l3 = Layer(Material().Lamination, 0.1)
c = Construction([l1, l2, l3])
m = Model(construction=c)
for l in m.construction.layers:
    print(l.ti)