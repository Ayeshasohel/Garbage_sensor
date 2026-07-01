# Imports
from mindstorms import MSHub, Motor, MotorPair, ColorSensor
from mindstorms.control import wait_for_seconds, Timer

# Initialise the Mindstorms Hub and connected devices on specific ports
class RobotHardware:
    def __init__(self):
        self.hub = MSHub()                        # Main control hub of the robot
        self.motor_pair = MotorPair('E', 'A')        # Controls the left and right drive motors on ports E and A
        self.left_motor = Motor('E')                # Left motor on port E, allows individual control
        self.right_motor = Motor('A')                # Right motor on port A, allows individual control
        self.claw_motor = Motor('B')                # Motor controlling the claw on port B
        self.arms_and_head_motor = Motor('D')        # Motor controlling the arms and head on port D
        self.color_sensor = ColorSensor('C')        # Color sensor attached to port C

# Animation Sequence
class Animation:
    def __init__(self, name, frames):
        self.name = name
        self.frames = frames

    def play(self, matrix, speed=5, loop=True, mode='overlay'):
        matrix.start_animation(self.frames, speed, loop, mode)

class AnimationLibrary:
    def __init__(self):
        self.animations = {
            "blinking": Animation("blinking", [
                '77077:00000:99099:99099:00000',
                '77077:00000:99099:99099:00000',
                '77077:00000:99099:99099:00000',
                '77077:00000:99099:99099:00000',
                '77077:00000:99099:99099:00000',
                '77077:00000:00000:77077:00000',
                '77077:00000:00000:00000:00000',
                '77077:00000:00000:88088:00000',
                '77077:00000:99099:99099:00000',
                '77077:00000:99099:99099:00000',
                '77077:00000:99099:99099:00000',
                '77077:00000:99099:99099:00000',
                '77077:00000:99099:99099:00000',
                '77077:00000:99099:99099:00000',
                '77077:00000:99099:99099:00000',
                '77077:00000:99099:99099:00000',
            ]),
            "scanning": Animation("scanning", [
                '00000:00000:56789:00000:00000',
                '00000:00000:45698:00000:00000',
                '00000:00000:34987:00000:00000',
                '00000:00000:29876:00000:00000',
                '00000:00000:98765:00000:00000',
                '00000:00000:89654:00000:00000',
                '00000:00000:78943:00000:00000',
                '00000:00000:67892:00000:00000',
            ])
        }

    def get(self, name):
        return self.animations.get(name)

# Calibration Sequence
class CalibrationController:
    def __init__(self, hardware: RobotHardware):
        self.hardware = hardware

    def calibrate(self):
        motor = self.hardware.arms_and_head_motor
        sensor = self.hardware.hub.motion_sensor
        timer = Timer()

        timer.reset()
        motor.start_at_power(100)
        wait_for_seconds(0.3)
        while motor.get_speed() > 50 and timer.now() < 3:
            wait_for_seconds(0.01)
        motor.stop()
        wait_for_seconds(0.2)

        sensor.reset_yaw_angle()
        wait_for_seconds(0.1)

        timer.reset()
        motor.start(-50)
        while sensor.get_yaw_angle() > -42 and timer.now() < 2:
            wait_for_seconds(0.01)
        motor.stop()
        wait_for_seconds(0.2)
        motor.set_degrees_counted(0)

# Traffic Sensor
class TrafficController:
    def __init__(self, hardware: RobotHardware):
        self.hardware = hardware

    def react_to_colour(self, color):
        motor_pair = self.hardware.motor_pair
        left_motor = self.hardware.left_motor
        right_motor = self.hardware.right_motor
        hub = self.hardware.hub

        if color == 'red':
            motor_pair.stop()
            hub.speaker.play_sound('Damage')

        elif color == 'green':
            hub.speaker.play_sound('Celebrate')
            motor_pair.start()

        elif color == 'yellow':
            hub.speaker.play_sound('Dial Down')
            wait_for_seconds(0.5)
            right_motor.run_for_degrees(370)
            wait_for_seconds(0.5)
            motor_pair.start()

        elif color == 'cyan':
            hub.speaker.play_sound('Dial Down')
            wait_for_seconds(0.5)
            left_motor.run_for_degrees(-370)
            wait_for_seconds(0.5)
            motor_pair.start()

        elif color == 'black':
            motor_pair.stop()
            hub.speaker.play_sound('Mission Accomplished')
            hub.speaker.play_sound('Power Down')


# Instantiate classes
hardware = RobotHardware()
calibration = CalibrationController(hardware)
animations = AnimationLibrary()
traffic = TrafficController(hardware)

valid_colours = ['red', 'green', 'yellow', 'cyan', 'black']
detected_color = None
final_colour = 'black'
end_reached = False

# Main loop
while not end_reached:
    # Setup
    hardware.hub.status_light.on('violet')
    hardware.hub.light_matrix.set_orientation('left')
    animations.get("blinking").play(hardware.hub.light_matrix)
    hardware.hub.speaker.start_sound('Bing')
    hardware.motor_pair.set_default_speed(20)
    # Timer
    timer = Timer()
    timer.reset()

    calibration.calibrate()

    # Start moving forward


    hardware.motor_pair.start()

    # Color detection loop
    while detected_color != final_colour:

        hardware.hub.status_light.on('yellow')
        animations.get("scanning").play(hardware.hub.light_matrix)

        timer.reset()
        detected_color = None# Reset for each scan attempt

        while timer.now() < 8:
            current_color = hardware.color_sensor.get_color()
            if current_color in valid_colours:
                detected_color = current_color
                break

        if detected_color:
            hardware.motor_pair.stop()
            hardware.hub.status_light.on(detected_color)
            traffic.react_to_colour(detected_color)

            if detected_color == final_colour:
                end_reached = True
                hardware.hub.status_light.on('white')
                animations.get("scanning").play(hardware.hub.light_matrix)
                hardware.hub.speaker.play_sound('Celebrate')
        else:
            # No valid color detected within time limit
            hardware.motor_pair.stop()
            hardware.hub.status_light.on('red')
            hardware.hub.speaker.play_sound('Oh No')
            hardware.hub.speaker.play_sound('Power Down')
            break# Exit inner loop to restart scanning
    break
hardware.motor_pair.stop()