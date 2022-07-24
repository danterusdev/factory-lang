import sys
from enum import Enum

args = sys.argv

if len(sys.argv) < 2:
    print("Input assembly line file path!")
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

stage = Stage.MACHINES

product_cap = 0

machines_inputs = {}
machine_outputs = {}

def parse(raw):
    parsed = []

    for input in raw:
        if input:
            if input[0] == '"':
                input = input[1 : len(input) - 1]
            else:
                try:
                    int_value = int(input)
                    input = int_value
                except ValueError:
                    pass
        parsed.append(input)

    return parsed

for row, line in enumerate(spec_file.readlines()):
    if stage == Stage.MACHINES:
        line = line.replace('\n', '')
        if "machine " in line and not line.startswith('#'):
            name = line[line.index("machine ") + 8 : line.index(':')]
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

            if name in machines:
                print("Machine " + name + " has duplicate definitions!")
                exit()
            machines.append(name)

            transformation = line.split(':')[1].split(' ')[1].strip()

            inputs = []

            parsed = []
            raw = []
            buffer = ""
            in_quotes = False
            for character in ' '.join(line.split(':')[1].split(' ')[2:]):
                if character == '"':
                    in_quotes = not in_quotes

                if character == ' ' and not in_quotes:
                    raw.append(buffer)
                    buffer = ""
                else:
                    buffer += character

            if buffer:
                raw.append(buffer)

            inputs.extend(parse(raw))

            modifiers = []

            for modifier in line.split(' '):
                if modifier == "machine":
                    break

                modifiers.append(modifier)
                
            machine_definitions[name] = (input_count, transformation, inputs, modifiers)

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
    if True:
        if name in output_uses or not name in machine_outputs:
            run = False

            actual_inputs = [None] * definition[0]
            if "input" in definition[3]:
                actual_inputs = [None] * len(args)
                for index, actual_input in enumerate(parse(args[2:])):
                    actual_inputs[index] = actual_input

            if definition[0] > 0:
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
                    if "product" in definition[3]:
                        exiting = True

                    #print(output)

                run_count[name] += 1
            else:
                output_uses.extend(machines_inputs[name])

            if name in output_uses:
                output_uses.remove(name)

for machine in machines:
    machine_inputs_available[machine] = []

while not exiting:
    for machine in machines:
        run_machine(machine)
