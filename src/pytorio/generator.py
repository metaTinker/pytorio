
import math

from .blueprint import *
from .prototype_loader import recipes

def add_single_am3_module(entities:list, x, y, recipe_name, request_filter_list, output_passive_provider_bar,
                          am_direction=Direction.NORTH, machine_name="assembling-machine-3",
                          input_inserter="fast-inserter", output_inserter="fast-inserter",
                          items=None, power_pole=True):
    entities.extend([
        Entity(machine_name, Position(x, y), recipe=recipe_name, direction=am_direction, items=items),
        Entity(input_inserter, Position(x - 1, y - 2), direction=Direction.NORTH),
        Entity("logistic-chest-requester", Position(x - 1, y - 3),
               request_filter_list=request_filter_list
        ),
        Entity(output_inserter, Position(x + 1, y - 2), direction=Direction.SOUTH),
        Entity("logistic-chest-passive-provider", Position(x + 1, y - 3), bar=output_passive_provider_bar),
    ])

    if power_pole:
        entities.append(Entity("medium-electric-pole", Position(x, y - 2)))


def add_single_am3_unbarreler(entities:list, x, y, recipe_name, request_filter_list, direction):
    entities.extend([
        Entity("assembling-machine-3", Position(x, y), recipe=recipe_name, direction=direction),
        Entity("fast-inserter", Position(x - 1, y - 2), direction=Direction.NORTH),
        Entity("logistic-chest-requester", Position(x - 1, y - 3),
               request_filter_list=request_filter_list
        ),
        Entity("fast-inserter", Position(x + 1, y - 2), direction=Direction.SOUTH),
        Entity("logistic-chest-active-provider", Position(x + 1, y - 3)),
        # Entity("medium-electric-pole", Position(x, y - 2))
    ])

def add_single_am3_liquid_module(entities: list, x, y, recipe_name, request_filter_list,
                                 unbarrel_recipe_name, unbarreler_request_filter_list, output_passive_provider_bar,
                                 input_inserter=None, output_inserter=None, items=None):

    add_single_am3_module(entities, x, y, recipe_name, request_filter_list, output_passive_provider_bar, Direction.EAST,
                          input_inserter=input_inserter, output_inserter=output_inserter, items=items)
    add_single_am3_unbarreler(entities, x + 3, y, unbarrel_recipe_name, unbarreler_request_filter_list, Direction.EAST)


def add_single_speed_beacon(entities:list, x, y):
    entities.append(
        Entity("beacon", Position(x, y), items={"speed-module-3": 2})
    )


def assembler_liquid(prod_node):
    for ingredient in prod_node['ingredients']:
        if ingredient['item_type'] == 'fluid':
            return ingredient
    return None


def count_machines(prod_list:list):

    assembler_furnace_count = 0
    for prod_node in prod_list:

        if prod_node['machine_name'] == 'assembling-machine-3' or prod_node['machine_name'] == 'electric-furnace':
            machine_amount = math.ceil(round(prod_node['machine_amount'], 2))
            if assembler_liquid(prod_node) == None:
                assembler_furnace_count += machine_amount
            else:
                assembler_furnace_count += machine_amount * 2

    return assembler_furnace_count


def generate(prod_list:list):

    total_assemblers_placed = 0
    total_assemblers = count_machines(prod_list)

    machines_per_row = round(math.sqrt(total_assemblers) * math.sqrt(5/3))

    entities = []

    prod_node_index = 0
    i = 0
    j = 0

    node_assemblers_placed = 0
    while total_assemblers_placed < total_assemblers:
        if j >= machines_per_row:
            i += 1
            j = 0

        prod_node = prod_list[prod_node_index]
        prod_node_machine_amount = math.ceil(round(prod_node['machine_amount'], 2))

        requester_filter_list = []
        barreler_filter_list = []
        for ingr in prod_node['ingredients']:
            if ingr['item_type'] == 'item':
                requester_filter_list.append(Logistic_Filter(ingr['item_name'], (ingr['item_rate']/prod_node_machine_amount) * 50))
            else:
                barreler_filter_list.append(Logistic_Filter(ingr['item_name'] + '-barrel', (ingr['item_rate']/prod_node_machine_amount)*2))

        if len(barreler_filter_list) == 0:
            add_single_am3_module(entities, j*3, i*5, prod_node['recipe_name'], requester_filter_list,
                                  1, machine_name=prod_node['machine_name'], input_inserter=prod_node["input_inserter"],
                                  output_inserter=prod_node["output_inserter"], power_pole=(j % 2 == 0 or j == (machines_per_row - 1)))
            j += 1
            total_assemblers_placed += 1
        elif len(barreler_filter_list) == 1:
            add_single_am3_liquid_module(entities, j*3, i*5, prod_node['recipe_name'], requester_filter_list,
                                         'empty-' + ingr['item_name'] + '-barrel', barreler_filter_list, 1)
            j += 2
            total_assemblers_placed += 2
        else:
            raise NotImplementedError

        node_assemblers_placed += 1
        if node_assemblers_placed >= prod_node_machine_amount:
            prod_node_index += 1
            node_assemblers_placed = 0

    return Blueprint.to_dict(Blueprint(entities))


def generate_with_beacons(prod_list:list):
    def calc_machines_per_row(total_assemblers:int)->int:
        a = round(math.sqrt(total_assemblers) * (0.5))
        machines_per_column = a if a <= 5 else 5
        machines_per_row = math.ceil(total_assemblers / machines_per_column)
        return machines_per_row, machines_per_column

    def generate_beacons(entities, x_start, y_start, beacons_width, beacons_height):
        for i in range(0, beacons_height):
            for j in range(0, beacons_width):
                add_single_speed_beacon(entities, x_start + j*3, y_start + i * 8)

    total_assemblers_placed = 0
    total_assemblers = count_machines(prod_list)

    machines_per_row, machines_per_column = calc_machines_per_row(total_assemblers)
    beacons_per_row = machines_per_row + 3

    entities = []
    generate_beacons(entities, -4, -5, beacons_per_row, machines_per_column + 1)

    prod_node_index = 0
    i = 0
    j = 0

    node_assemblers_placed = 0
    while total_assemblers_placed < total_assemblers:
        if j >= machines_per_row:
            i += 1
            j = 0

        prod_node = prod_list[prod_node_index]
        prod_node_machine_amount = math.ceil(round(prod_node['machine_amount'], 2))

        requester_filter_list = []
        barreler_filter_list = []
        for ingr in prod_node['ingredients']:
            if ingr['item_type'] == 'item':
                requester_filter_list.append(Logistic_Filter(ingr['item_name'], math.ceil(ingr['item_rate']/prod_node_machine_amount) * 12))
            else:
                barreler_filter_list.append(Logistic_Filter(ingr['item_name'] + '-barrel', math.ceil(ingr['item_rate']/prod_node_machine_amount) * 2))

        if len(barreler_filter_list) == 0:
            add_single_am3_module(entities, j*3, i*8, prod_node['recipe_name'], requester_filter_list,
                                  1, machine_name=prod_node['machine_name'], input_inserter=prod_node["input_inserter"],
                                  output_inserter=prod_node["output_inserter"], items=prod_node['machine_modules'],
                                  power_pole=(j % 2 == 0 or j == (machines_per_row - 1)))
            j += 1
            total_assemblers_placed += 1
        elif len(barreler_filter_list) == 1:
            add_single_am3_liquid_module(entities, j*3, i*8, prod_node['recipe_name'], requester_filter_list,
                                         'empty-' + ingr['item_name'] + '-barrel', barreler_filter_list, 1,
                                         input_inserter=prod_node['input_inserter'], output_inserter=prod_node['output_inserter'],
                                         items=prod_node['machine_modules'])
            j += 2
            total_assemblers_placed += 2
        else:
            raise NotImplementedError

        node_assemblers_placed += 1
        if node_assemblers_placed >= prod_node_machine_amount:
            prod_node_index += 1
            node_assemblers_placed = 0

    return Blueprint.to_dict(Blueprint(entities))

