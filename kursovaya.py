from flask import Flask, request, jsonify

# Паттерн Singleton для модели данных дрона
class DroneModelSingleton:
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
        self.position = new_position

    def update_altitude(self, new_altitude):
        self.altitude = new_altitude

    def update_speed(self, new_speed):
        self.speed = new_speed

    def update_battery_level(self, consumption):
        self.battery_level -= consumption


# Паттерн Observer для сенсоров
class SensorObserver:
    def update(self, data):
        raise NotImplementedError("Метод update должен быть реализован")

class ObstacleSensor(SensorObserver):
    def __init__(self, controller):
        self.controller = controller

    def update(self, data):
        if data['distance'] < 10:
            print("Препятствие слишком близко! Изменение курса...")
            new_position = (self.controller.model.position[0] + 10, self.controller.model.position[1])
            self.controller.change_position(new_position)
        elif data['distance'] < 5:
            print("Опасное расстояние! Остановка БПЛА.")
            self.controller.change_speed(0)


# Представление дрона
class DroneView:
    def display_status(self, model):
        return {
            "altitude": model.altitude,
            "speed": model.speed,
            "position": model.position,
            "battery_level": model.battery_level
        }

    def alert(self, message):
        return {"alert": message}


# Контроллер дрона
class DroneController:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.sensors = []

    def attach_sensor(self, sensor):
        self.sensors.append(sensor)

    def notify_sensors(self, data):
        for sensor in self.sensors:
            sensor.update(data)

    def change_position(self, new_position):
        self.model.update_position(new_position)
        return self.view.display_status(self.model)

    def change_altitude(self, new_altitude):
        self.model.update_altitude(new_altitude)
        return self.view.display_status(self.model)

    def change_speed(self, new_speed):
        self.model.update_speed(new_speed)
        return self.view.display_status(self.model)

    def monitor_battery(self):
        if self.model.battery_level < 20:
            return self.view.alert("Low battery! Returning to base.")
        return {"battery_level": self.model.battery_level}

    def return_to_base(self):
        self.model.update_position((0, 0))
        self.model.update_altitude(0)
        self.model.update_speed(0)
        return self.view.alert("Drone has returned to base.")


# Паттерн Strategy для различных стратегий полета
class FlightStrategy:
    def execute(self, drone):
        raise NotImplementedError("Метод execute должен быть реализован")

class TakeoffStrategy(FlightStrategy):
    def execute(self, drone):
        print("Взлет...")
        drone.model.update_altitude(10)

class LandingStrategy(FlightStrategy):
    def execute(self, drone):
        print("Посадка...")
        drone.model.update_altitude(0)
        drone.model.update_speed(0)

class PatrolStrategy(FlightStrategy):
    def execute(self, drone):
        print("Патрулирование...")
        drone.model.update_speed(5)
        new_position = (drone.model.position[0] + 5, drone.model.position[1] + 5)
        drone.model.update_position(new_position)


# Класс дрона с состояниями и стратегиями
class StatefulDrone:
    def __init__(self, model, view):
        self.model = model
        self.view = view
        self.strategy = None

    def set_strategy(self, strategy):
        self.strategy = strategy

    def perform_action(self):
        if self.strategy:
            self.strategy.execute(self)
        self.view.display_status(self.model)


# Flask приложение для управления дроном
app = Flask(__name__)

# Создаем модель дрона (Singleton)
drone_model = DroneModelSingleton()

# Представление дрона
drone_view = DroneView()

# Контроллер дрона
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
