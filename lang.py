import sys
import threading
from enum import Enum

#test = []
#test.append(None)
#test.append(None)
#print(len(test))
#test[1] = None

args = sys.argv

if len(sys.argv) < 2:
    print("Input spec file path!")
    sys.exit()

spec_file = sys.argv[1]
spec_file = open(spec_file)

machines = []
machine_locations = {}
machine_locations_reversed = {}
machine_output_directions = {}

searching_machines = False

machine_definitions = {}

class Stage(Enum):
    CONFIGURATION = 0
    LAYOUT = 1
    MACHINES = 2

stage = Stage.CONFIGURATION

product_cap = 0

machines_inputs = {}
machine_outputs = {}

for row, line in enumerate(spec_file.readlines()):
    if stage == Stage.CONFIGURATION:
        if line.startswith("#"):
            stage = Stage.MACHINES
            continue

        split = line.split('=')
        id = split[0].strip()

        if id == "product_cap":
            product_cap = int(split[1].strip())

    #elif stage == Stage.LAYOUT:
    #    if line.startswith("#"):
    #        stage = Stage.MACHINES
    #        continue

    #    line = line.replace('\n', '')
    #    for column, machine in enumerate(line.replace('/', '-').split('-')):
    #        machine = machine.strip()
    #        if machine:
    #            machine_locations[machine] = (row, column)
    #            machine_locations_reversed[(row, column)] = machine
    #            split = line.split(' ')
    #            index = split.index(machine) + 1
    #            output_direction = None
    #            while not output_direction:
    #                if index < len(split):
    #                    if split[index].strip():
    #                        output_direction = split[index]
    #                    else:
    #                        index += 1
    #                else:
    #                    output_direction = 'X'

    #            if not output_direction == 'X':
    #                machine_output_directions[machine] = output_direction
    elif stage == Stage.MACHINES:
        line = line.replace('\n', '')
        if line.startswith("machine "):
            name = line[8 : line.index(':')]
            input_count = 0
            if '(' in name:
                inputs = name[name.index('(') + 1 : name.index(')')].split(',')
                input_count = len(inputs)
                name = name[0 : name.index('(')]

                machines_inputs[name] = list(inputs)
                for input in inputs:
                    machine_outputs[input] = name
            else:
                machines_inputs[name] = []

            machines.append(name)

            transformation = line.split(':')[1].split(' ')[1].strip()

            inputs = []

            for input in line.split(':')[1].split(' ')[2:]:
                if input:
                    try:
                        int_value = int(input)
                        input = int_value
                    except ValueError:
                        pass

                    inputs.append(input)
                
            machine_definitions[name] = (input_count, transformation, inputs)

#for machine, direction in machine_output_directions.items():
#    location = machine_locations[machine]
#    reciever_machine_location = None
#    if direction == '-':
#        reciever_machine_location = (location[0], location[1] + 1)
#    elif direction == '/':
#        reciever_machine_location = (location[0] - 1, location[1] + 1)
#
#    reciever_machine = machine_locations_reversed[reciever_machine_location]
#
#    if not reciever_machine in machines_inputs:
#        machines_inputs[reciever_machine] = []
#
#    machines_inputs[reciever_machine].append(machine)
#    machine_outputs[machine] = reciever_machine

machine_inputs_available = {}
run_count = {}

def run_transformation(id, inputs):
    match id:
        case "add":
            return add_(inputs[0], inputs[1])
        case "print":
            return print_(inputs[0])

def add_(value1, value2):
    return value1 + value2

def print_(value):
    print(value)

exiting = False
output_uses = []

def run_machine(name):
    global exiting
    run_count[name] = 0
    definition = machine_definitions[name]
    while not exiting:
        if name in output_uses or not name in machine_outputs:
            run = False

            actual_inputs = [None] * definition[0]
            if len(actual_inputs) > 0:
                for index, input in enumerate(machine_inputs_available[name]):
                    if input:
                        is_valid = True
                        for input0 in input:
                            if input0 == None:
                                is_valid = False

                        if is_valid:
                            actual_inputs = machine_inputs_available[name][index]
                            machine_inputs_available[name][index] = None
                            run = True
                            break
            else:
                run = True


            if run:
                transformation_inputs = list(definition[2])
                for index, input in enumerate(list(transformation_inputs)):
                    if isinstance(input, str) and input.startswith("["):
                        transformation_inputs[index] = actual_inputs[int(input[1 : len(input) - 1])]

                output = run_transformation(definition[1], transformation_inputs)
                if name in machine_outputs:
                    next_machine = machine_outputs[name]
                    if len(machine_inputs_available[next_machine]) < run_count[name] + 1:
                        machine_inputs_available[next_machine].append([None] * machine_definitions[next_machine][0])

                    machine_inputs_available[next_machine][run_count[name]][machines_inputs[next_machine].index(name)] = output
                else:
                    if run_count[name] == product_cap - 1:
                        exiting = True

                    #print(output)

                run_count[name] += 1
            else:
                output_uses.extend(machines_inputs[name])

            if name in output_uses:
                output_uses.remove(name)

for machine in machines:
    machine_inputs_available[machine] = []

for machine in machines:
    thread = threading.Thread(target=run_machine, args=(machine,))
    thread.start()
