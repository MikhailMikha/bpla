from flask import Flask, request, jsonify


# Паттерн Singleton для модели данных дрона
class DroneModelSingleton:
    """
    Singleton class for drone data model
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DroneModelSingleton, cls).__new__(cls)
            cls._instance.altitude = 0
            cls._instance.speed = 0
            cls._instance.position = (0, 0)
            cls._instance.battery_level = 100
        return cls._instance

    def update_position(self, new_position):
        """
        Update the drone's position
        """
        self.position = new_position

    def update_altitude(self, new_altitude):
        """
        Update the drone's altitude
        """
        self.altitude = new_altitude

    def update_speed(self, new_speed):
        """
        Update the drone's speed
        """
        self.speed = new_speed

    def update_battery_level(self, consumption):
        """
        Update the drone's battery level
        """
        self.battery_level -= consumption


# Паттерн Observer для сенсоров
class SensorObserver:
    """
    Observer class for sensors
    """

    def update(self, data):
        raise NotImplementedError("Method update must be implemented")


class ObstacleSensor(SensorObserver):
    """
    Obstacle sensor class
    """

    def __init__(self, controller):
        self.controller = controller

    def update(self, data):
        if data['distance'] < 10:
            print("Obstacle too close! Changing course...")
            new_position = (self.controller.model.position[0] + 10, self.controller.model.position[1])
            self.controller.change_position(new_position)
        elif data['distance'] < 5:
            print("Dangerous distance! Stopping drone.")
            self.controller.change_speed(0)


# Drone view class
class DroneView:
    """
    Class for drone view
    """

    def display_status(self, model):
        """
        Display drone status
        """
        return {
            "altitude": model.altitude,
            "speed": model.speed,
            "position": model.position,
            "battery_level": model.battery_level
        }

    def alert(self, message):
        """
        Display alert message
        """
        return {"alert": message}


# Drone controller class
class DroneController:
    """
    Class for drone controller
    """

    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.sensors = []

    def attach_sensor(self, sensor):
        """
        Attach sensor to the controller
        """
        self.sensors.append(sensor)

    def notify_sensors(self, data):
        """
        Notify sensors with data
        """
        for sensor in self.sensors:
            sensor.update(data)

    def change_position(self, new_position):
        """
        Change drone's position
        """
        self.model.update_position(new_position)
        return self.view.display_status(self.model)

    def change_altitude(self, new_altitude):
        """
        Change drone's altitude
        """
        self.model.update_altitude(new_altitude)
        return self.view.display_status(self.model)

    def change_speed(self, new_speed):
        """
        Change drone's speed
        """
        self.model.update_speed(new_speed)
        return self.view.display_status(self.model)

    def monitor_battery(self):
        """
        Monitor drone's battery level
        """
        if self.model.battery_level < 20:
            return self.view.alert("Low battery! Returning to base.")
        return {"battery_level": self.model.battery_level}

    def return_to_base(self):
        """
        Return drone to base
        """
        self.model.update_position((0, 0))
        self.model.update_altitude(0)
        self.model.update_speed(0)
        return self.view.alert("Drone has returned to base.")

    def auto_return_to_base(self):
        """
        Automatically return drone to base
        """
        return self.return_to_base()


# Flight strategy pattern
class FlightStrategy:
    """
    Flight strategy interface
    """

    def execute(self, drone):
        raise NotImplementedError("Method execute must be implemented")


class TakeoffStrategy(FlightStrategy):
    """
    Takeoff strategy class
    """

    def execute(self, drone):
        print("Taking off...")
        drone.model.update_altitude(10)


class LandingStrategy(FlightStrategy):
    """
    Landing strategy class
    """

    def execute(self, drone):
        print("Landing...")
        drone.model.update_altitude(0)


class PatrolStrategy(FlightStrategy):
    """
    Patrol strategy class
    """

    def execute(self, drone):
        print("Patrolling...")
        # Implement patrol logic here


class StatefulDrone:
    """
    Class for stateful drone
    """

    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.strategy = None

    def set_strategy(self, strategy):
        """
        Set flight strategy for the drone
        """
        self.strategy = strategy

    def perform_action(self):
        """
        Perform action based on the current strategy
        """
        if self.strategy:
            self.strategy.execute(self)
        self.view.display_status(self.model)

    def auto_return_to_base(self):
        """
        Automatically return drone to base
        """
        return self.strategy.execute(self)


# Функция маршрутизации в Flask приложении
app = Flask(__name__)
drone_model = DroneModelSingleton()
drone_view = DroneView()
drone_controller = DroneController(drone_model, drone_view)
# Подключаем сенсор препятствий (Observer)
obstacle_sensor = ObstacleSensor(drone_controller)
drone_controller.attach_sensor(obstacle_sensor)

# Дрон с поддержкой стратегий полета (Strategy)
stateful_drone = StatefulDrone(drone_model, drone_view)



# API для управления дроном
@app.route('/', methods=['GET'])
def get_status():
    return jsonify(drone_view.display_status(drone_model))


@app.route('/position', methods=['POST'])
def update_position():
    data = request.get_json()
    new_position = data.get('position', (0, 0))
    return jsonify(drone_controller.change_position(new_position))


@app.route('/altitude', methods=['POST'])
def update_altitude():
    data = request.get_json()
    new_altitude = data.get('altitude', 0)
    return jsonify(drone_controller.change_altitude(new_altitude))


@app.route('/speed', methods=['POST'])
def update_speed():
    data = request.get_json()
    new_speed = data.get('speed', 0)
    return jsonify(drone_controller.change_speed(new_speed))


@app.route('/battery', methods=['GET'])
def check_battery():
    return jsonify(drone_controller.monitor_battery())


@app.route('/return_to_base', methods=['POST'])
def return_to_base():
    return jsonify(drone_controller.return_to_base())


@app.route('/takeoff', methods=['POST'])
def takeoff():
    stateful_drone.set_strategy(TakeoffStrategy())
    stateful_drone.perform_action()
    return jsonify({"message": "Drone is taking off"})


@app.route('/patrol', methods=['POST'])
def patrol():
    stateful_drone.set_strategy(PatrolStrategy())
    stateful_drone.perform_action()
    return jsonify({"message": "Drone is patrolling"})


@app.route('/land', methods=['POST'])
def land():
    stateful_drone.set_strategy(LandingStrategy())
    stateful_drone.perform_action()
    return jsonify({"message": "Drone is landing"})


if __name__ == '__main__':
    app.run(debug=True)
