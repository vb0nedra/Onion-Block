import os
import json
import yaml
import shutil
from pathlib import Path
import itertools

# BUG:
# - ISSUE: stone-like blocks mined without pickaxe doesn't transform cause incorrect tool => no loot_table roll
# i mean, why fix it? well yea is for sure sucks to mine diamonds with wooden pickaxe and get air instead of at least cobblestone ore gravel, but thats how vanilla works!
# plus only fix i could come up with requires removing items from "...mineable/pickaxe" => rewriting tag => no compatibility with other datapack and relying on references like in CaTE (aka GlobalItemModifier)

# Terminal color definitions
class fg:
    BLACK   = '\033[30m'
    RED     = '\033[31m'
    GREEN   = '\033[32m'
    YELLOW  = '\033[33m'
    BLUE    = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN    = '\033[36m'
    WHITE   = '\033[37m'
    RESET   = '\033[39m'
    GRAY    = '\033[90m'
class bg:
    BLACK   = '\033[40m'
    RED     = '\033[41m'
    GREEN   = '\033[42m'
    YELLOW  = '\033[43m'
    BLUE    = '\033[44m'
    MAGENTA = '\033[45m'
    CYAN    = '\033[46m'
    WHITE   = '\033[47m'
    RESET   = '\033[49m'
class style:
    BRIGHT    = '\033[1m'
    DIM       = '\033[2m'
    NORMAL    = '\033[22m'
    RESET_ALL = '\033[0m'
style_error = fg.YELLOW+'[ERROR] '
style_fatal = fg.RED+'[FATAL-ERROR] '
style_progress = fg.GREEN+'[PROGRESS] '
style_warning = fg.CYAN
style_warning_grand = fg.YELLOW
style_reset = style.RESET_ALL
style_unimportant = fg.GRAY


# global generator configs
datapack_name = 'vbonedra.ob'
executable_path = Path(__file__).resolve().parent
datapack_path = executable_path.parent

executable_path = str(executable_path)
datapack_path = str(datapack_path)
result_path = datapack_path+'\\data'


block_state_properties = {
    'simple_block': {},
    'slab': {
        'type': ['bottom','top','double'],
        # 'waterlogged': ['true', 'false'],
    },
    'stairs': {
        'half': ['bottom','top'],
        'facing': ['north','south','west','east'],
        # 'shape': ['straight','inner_left','inner_right','outer_left','outer_right'],
        # 'waterlogged': ['true', 'false'],
    },
    'wall': {
        # 'waterlogged': ['true', 'false'],
    },
    'directional': {
        'axis': ['x','y','z'],
    },
    'bulb': {
        'lit': ['true', 'false'],
        'powered': ['true', 'false'],
    }
}

all_onion_blocks = []

### temp notes
'''

'''
###


def fix_item_name(item):
    if item.find(':') == -1: return f'minecraft:{item}'
    return item
def state_to_filename(state):
    return '_'+str(state).replace(':','_').replace('{','').replace('}','').replace("'",'').replace(" ",'').replace(",",'_') if state != {} else ''
def last_n_in_path(path, n=1, last_style = str): return style_unimportant + path.replace(result_path, '') + last_style
def save_data(path, data, indent=None):
    try:
        open(path, 'w').close()
        open(path, 'r+').write(json.dumps(data, indent=indent))
    except:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w').close()
        open(path, 'r+').write(json.dumps(data, indent=indent))
def save_data_mcfunction(path, data):
    try:
        open(path, 'w').close()
        open(path, 'r+').write(data)
    except:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        open(path, 'w').close()
        open(path, 'r+').write(data)


def create_loot_table_block(block, next_block, drop_player={}, drop_ore={}, block_state_property='simple_block', silk_touch_self_drop=True):
    print(f'{style_unimportant}[GENERATING] {block} -> {next_block} as {block_state_property}{style_reset}')
    block = fix_item_name(block)
    namespace_block = block[:block.rfind(':')]
    name_block = block[block.rfind(':')+1:]
    next_block = fix_item_name(next_block)
    namespace_next_block = next_block[:next_block.rfind(':')]
    name_next_block = next_block[next_block.rfind(':')+1:]
    if block not in all_onion_blocks: all_onion_blocks.append(block)
    if next_block not in all_onion_blocks: all_onion_blocks.append(next_block)

    states = [dict(combo) for combo in itertools.product(*[[(key, val) for val in values] for key, values in block_state_properties[block_state_property].items()])]
    data_loot_table = {
        "type": "block",
        "pools": [
            {
                "rolls": 1,
                "entries": [
                    {
                        "type": "alternatives",
                        "children": [
                            {
                                "type": "item",
                                "name": block if silk_touch_self_drop else next_block,
                                "conditions": [
                                    {
                                        "condition": "match_tool",
                                        "predicate": {
                                            "predicates": {
                                                "enchantments": [
                                                    {
                                                        "enchantments": "silk_touch"
                                                    }
                                                ] 
                                            }
                                        }
                                    }
                                ]
                            },
                            {
                                "type": "alternatives",
                                "conditions": [
                                    {
                                        "condition": "entity_properties",
                                        "entity": "this",
                                        "predicate": {
                                            "entity_type": "player"
                                        }
                                    }
                                ],
                                "children": []
                            },
                            {
                                "type": "alternatives",
                                "children": []
                            }
                        ]
                    }
                ]
            }
        ]
    }

    create_drop_table(namespace_block, name_block, drop_player, drop_ore=drop_ore)
    create_roll_any_table(namespace_block, name_block, namespace_next_block, name_next_block)
    for state in states:
        create_roll_any_table(namespace_block, name_block, namespace_next_block, name_next_block, state=state)
        data_loot_table["pools"][0]["entries"][0]["children"][2]["children"].append( # non_player
            {
                "type": "minecraft:loot_table",
                "value": f"{datapack_name}:non_player/roll/{namespace_block}/{name_block+state_to_filename(state)}",
                "conditions": [
                    {
                        "condition": "block_state_property",
                        "block": block,
                        "properties": state
                    }
                ] if state != {} else []
            }
        )
        data_loot_table["pools"][0]["entries"][0]["children"][1]["children"].append( # player
            {
                "type": "minecraft:loot_table",
                "value": f"{datapack_name}:player/roll/{namespace_block}/{name_block+state_to_filename(state)}",
                "conditions": [
                    {
                        "condition": "block_state_property",
                        "block": block,
                        "properties": state
                    }
                ] if state != {} else []
            }
        )
    save_data(f'{result_path}\\{namespace_block}\\loot_table\\blocks\\{name_block}.json', data_loot_table)

def create_roll_any_table(namespace_block, name_block, namespace_next_block, name_next_block, state={}):
    # player
    path = f'{result_path}\\{datapack_name}\\loot_table\\player\\roll\\{namespace_block}\\{name_block+state_to_filename(state)}.json'
    data = {
        "type": "block",
        "pools": [
            {
                "rolls": 1,
                "entries": [
                    {
                        "type": "loot_table",
                        "value": f"{datapack_name}:transform",
                        "functions": [
                            {
                                "function": "minecraft:set_components",
                                "components": {
                                    "custom_data": {
                                        "vbonedra.ob": {
                                            "id": name_next_block,
                                            "setblock": str(state).replace(':','=').replace('{','[').replace('}',']').replace("'",'').replace(" ",''),
                                            "modified": True
                                        }
                                    }
                                }
                            }
                        ]
                    }
                ]
            },
            {
                "rolls": 1,
                "entries": [
                    {
                        "type": "loot_table",
                        "value": f"{datapack_name}:player/drop/{namespace_block}/{name_block}"
                    }
                ]
            }
        ],
    }
    save_data(path, data)
    
    # non_player
    path = f'{result_path}\\{datapack_name}\\loot_table\\non_player\\roll\\{namespace_block}\\{name_block+state_to_filename(state)}.json'
    data = {
        "type": "block",
        "pools": [
            {
                "rolls": 1,
                "entries": [
                    {
                        "type": "loot_table",
                        "value": f"{namespace_next_block}:blocks/{name_next_block}",
                        "weight": 1
                    },
                    {
                        "weight": 1,
                        "type": "loot_table",
                        "value": f"{datapack_name}:transform",
                        "functions": [
                            {
                                "function": "minecraft:set_components",
                                "components": {
                                    "custom_data": {
                                        "vbonedra.ob": {
                                            "id": name_next_block,
                                            "summon": state,
                                            "modified": True
                                        }
                                    }
                                }
                            }
                        ]
                    }
                ]
            },
            {
                "rolls": 1,
                "entries": [
                    {
                        "type": "loot_table",
                        "value": f"{datapack_name}:player/drop/{namespace_block}/{name_block}"
                    }
                ]
            }
        ],
    }
    save_data(path, data)

def create_drop_table(namespace_block, name_block, drop_player, drop_ore={}):
    data_drop_player_table = {"type": "block","pools": []}
    for item_name, count in drop_player.items():
        data_drop_player_table["pools"].append(
            {
                "rolls": 1,
                "entries": [
                    {
                        "type": "item",
                        "name": fix_item_name(item_name),
                        "functions": [
                            {
                                "function": "set_count",
                                "count": count
                            },
                            {
                                "function": "minecraft:explosion_decay"
                            }
                        ]
                    }
                ]
            }
        )
    if drop_ore != {}: data_drop_player_table["pools"].append(drop_ore)
    save_data(f'{result_path}\\{datapack_name}\\loot_table\\player\\drop\\{namespace_block}\\{name_block}.json', data_drop_player_table)

def create_slabs_to_block_recipe_and_advancement(slab, block):
    if block not in all_onion_blocks: all_onion_blocks.append(block)
    if slab not in all_onion_blocks: all_onion_blocks.append(slab)
    data_recipe = {
        "type": "crafting_shaped",
        "group": "slabs_to_block",
        "category": "misc",
        "key": {
            "#": fix_item_name(slab)
        },
        "pattern": [
            "##",
        ],
        "result": {
            "id": fix_item_name(block),
            "count": 1
        }
    }
    block = block[block.find(':')+1:]
    save_data(f'{result_path}\\{datapack_name}\\recipe\\slabs_to_block\\{block}.json', data_recipe)
    data_advancement = {
        "parent": "minecraft:recipes/root",
        "criteria": {
            "has_recipe": {
                "conditions": {
                    "recipe": f"{datapack_name}:slabs_to_block/{block}"
                },
                "trigger": "minecraft:recipe_unlocked"
            },
            "has_items": {
                "conditions": {
                    "items": [
                        {
                            "items": [
                                slab,
                                block
                            ]
                        }
                    ]
                },
                "trigger": "minecraft:inventory_changed"
            }
        },
        "requirements": [
            [
                "has_recipe",
                "has_items"
            ]
        ],
        "rewards": {
            "recipes": [
                f"{datapack_name}:slabs_to_block/{block}"
            ]
        }
    }
    save_data(f'{result_path}\\{datapack_name}\\advancement\\recipe\\slabs_to_block\\{block}.json', data_advancement)


def main():
    print(f'{style_progress}Copying data...{style_reset}')
    if os.path.exists(result_path):
        if input(f'{style_warning_grand}result_path ({style_unimportant}{result_path}{style_warning_grand}) already exists, type "1" to delete it and regenerate from "references\\data": {style_reset}') == '1': shutil.rmtree(result_path)
    shutil.copytree(f'{executable_path}\\references\\data', result_path, dirs_exist_ok=True)
    

    # logs
    for block in [
        'acacia',
        'birch',
        'cherry',
        'dark_oak',
        'jungle',
        'mangrove',
        'oak',
        'pale_oak',
        'spruce',
    ]:
        create_loot_table_block(f'{block}_log', f'stripped_{block}_log', block_state_property='directional')
        create_loot_table_block(f'{block}_wood', f'stripped_{block}_wood', block_state_property='directional')
    for block in [
        'crimson',
        'warped',
    ]:
        create_loot_table_block(f'{block}_hyphae', f'stripped_{block}_hyphae', block_state_property='directional')
        create_loot_table_block(f'{block}_stem', f'stripped_{block}_stem', block_state_property='directional')


    # planks
    for block in [
        'acacia',
        'birch',
        'cherry',
        'dark_oak',
        'jungle',
        'mangrove',
        'oak',
        'pale_oak',
        'spruce',
        'crimson',
        'warped',
    ]:
        create_loot_table_block(f'{block}_planks', f'{block}_slab', {f'{block}_slab':1})
        create_slabs_to_block_recipe_and_advancement(f'{block}_slab',f'{block}_planks')



    # stone
    for block, next_block in {
        'stone': 'stone_slab',
        'smooth_stone': 'smooth_stone_slab',
        'cobblestone': 'cobblestone_slab',
        'stone_bricks': 'stone_brick_slab',
        'mossy_cobblestone': 'mossy_cobblestone_slab',
        'mossy_stone_bricks': 'mossy_stone_brick_slab',
    }.items():
        create_slabs_to_block_recipe_and_advancement(next_block,block)
    
    for block, next_block in {
        'smooth_stone': 'stone',
        'stone': 'cobblestone',
        'stone_brick': 'cobblestone',
        'mossy_cobblestone': 'cobblestone',
        'mossy_stone_brick': 'stone_brick',
    }.items():
        create_loot_table_block(f'{block}_slab', f'{next_block}_slab', block_state_property='slab')
        if block != 'smooth_stone':
            create_loot_table_block(f'{block}_stairs', f'{next_block}_stairs', block_state_property='stairs')
            if block != 'stone': create_loot_table_block(f'{block}_wall', f'{next_block}_wall')

    for block, next_block in {
        'smooth_stone': 'stone',
        'mossy_stone_bricks': 'stone_bricks',
        'stone_bricks': 'cracked_stone_bricks',
        'chiseled_stone_bricks': 'stone_bricks',
        'stone':'cobblestone',
        'cracked_stone_bricks':'cobblestone',
    }.items():
        create_loot_table_block(block, next_block)

    for block, next_block in {
        'cobblestone': 'gravel',
        'mossy_cobblestone': 'gravel',
    }.items():
        create_loot_table_block(block, next_block, {'cobblestone_slab':1})
    
    create_loot_table_block('coal_ore', 'cobblestone', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:coal"
            }
            ]
        }
    )
    create_loot_table_block('copper_ore', 'cobblestone', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "count": {
                    "type": "minecraft:uniform",
                    "max": 5,
                    "min": 2
                  },
                  "function": "minecraft:set_count"
                },
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:raw_copper"
            }
            ]
        }
    )
    create_loot_table_block('diamond_ore', 'cobblestone', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:diamond"
            }
            ]
        }
    )
    create_loot_table_block('emerald_ore', 'cobblestone', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:emerald"
            }
            ]
        }
    )
    create_loot_table_block('gold_ore', 'cobblestone', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:raw_gold"
            }
            ]
        }
    )
    create_loot_table_block('iron_ore', 'cobblestone', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:raw_iron"
            }
            ]
        }
    )
    create_loot_table_block('lapis_ore', 'cobblestone', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "count": {
                    "type": "minecraft:uniform",
                    "max": 9,
                    "min": 4
                  },
                  "function": "minecraft:set_count"
                },
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:lapis_lazuli"
            }
            ]
        }
    )
    create_loot_table_block('redstone_ore', 'cobblestone', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "count": {
                    "type": "minecraft:uniform",
                    "max": 5,
                    "min": 4
                  },
                  "function": "minecraft:set_count"
                },
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:uniform_bonus_count",
                  "function": "minecraft:apply_bonus",
                  "parameters": {
                    "bonusMultiplier": 1
                  }
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:redstone"
            }
            ]
        }
    )



    # deepslate
    for block, next_block in {
        'polished_deepslate': 'polished_deepslate_slab',
        'cobbled_deepslate': 'cobbled_deepslate_slab',
        'deepslate_bricks': 'deepslate_brick_slab',
    }.items():
        create_slabs_to_block_recipe_and_advancement(next_block,block)
    
    for block, next_block in {
        'polished_deepslate': 'cobbled_deepslate',
        'deepslate_brick': 'cobbled_deepslate',
        'deepslate_tile': 'cobbled_deepslate',
    }.items():
        create_loot_table_block(f'{block}_slab', f'{next_block}_slab', block_state_property='slab')
        create_loot_table_block(f'{block}_stairs', f'{next_block}_stairs', block_state_property='stairs')
        create_loot_table_block(f'{block}_wall', f'{next_block}_wall')

    for block, next_block in {
        'deepslate_bricks': 'cracked_deepslate_bricks',
        'deepslate_tiles': 'cracked_deepslate_tiles',
        'polished_deepslate': 'cobbled_deepslate',
        'chiseled_deepslate': 'cobbled_deepslate',
        'deepslate': 'cobbled_deepslate',
        'cracked_deepslate_bricks': 'cobbled_deepslate',
        'cracked_deepslate_tiles': 'cobbled_deepslate',
    }.items():
        create_loot_table_block(block, next_block)

    for block, next_block in {
        'cobbled_deepslate': 'gravel',
    }.items():
        create_loot_table_block(block, next_block, {'cobbled_deepslate_slab':1})

    create_loot_table_block('deepslate_coal_ore', 'cobbled_deepslate', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:coal"
            }
            ]
        }
    )
    create_loot_table_block('deepslate_copper_ore', 'cobbled_deepslate', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "count": {
                    "type": "minecraft:uniform",
                    "max": 5,
                    "min": 2
                  },
                  "function": "minecraft:set_count"
                },
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:raw_copper"
            }
            ]
        }
    )
    create_loot_table_block('deepslate_diamond_ore', 'cobbled_deepslate', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:diamond"
            }
            ]
        }
    )
    create_loot_table_block('deepslate_emerald_ore', 'cobbled_deepslate', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:emerald"
            }
            ]
        }
    )
    create_loot_table_block('deepslate_gold_ore', 'cobbled_deepslate', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:raw_gold"
            }
            ]
        }
    )
    create_loot_table_block('deepslate_iron_ore', 'cobbled_deepslate', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:raw_iron"
            }
            ]
        }
    )
    create_loot_table_block('deepslate_lapis_ore', 'cobbled_deepslate', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "count": {
                    "type": "minecraft:uniform",
                    "max": 9,
                    "min": 4
                  },
                  "function": "minecraft:set_count"
                },
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:lapis_lazuli"
            }
            ]
        }
    )
    create_loot_table_block('deepslate_redstone_ore', 'cobbled_deepslate', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "count": {
                    "type": "minecraft:uniform",
                    "max": 5,
                    "min": 4
                  },
                  "function": "minecraft:set_count"
                },
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:uniform_bonus_count",
                  "function": "minecraft:apply_bonus",
                  "parameters": {
                    "bonusMultiplier": 1
                  }
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:redstone"
            }
            ]
        }
    )
    


    # blackstone
    for block, next_block in {
        'blackstone': 'blackstone_slab',
        'polished_blackstone': 'polished_blackstone_slab',
        'polished_blackstone_bricks': 'polished_blackstone_brick_slab',
    }.items():
        create_slabs_to_block_recipe_and_advancement(next_block,block)
    
    for block, next_block in {
        'polished_blackstone': 'blackstone',
        'polished_blackstone_brick': 'blackstone',
    }.items():
        create_loot_table_block(f'{block}_slab', f'{next_block}_slab', block_state_property='slab')
        create_loot_table_block(f'{block}_stairs', f'{next_block}_stairs', block_state_property='stairs')
        create_loot_table_block(f'{block}_wall', f'{next_block}_wall')

    for block, next_block in {
        'polished_blackstone_bricks': 'cracked_polished_blackstone_bricks',
        'polished_blackstone': 'blackstone',
        'cracked_polished_blackstone_bricks': 'blackstone',
    }.items():
        create_loot_table_block(block, next_block)

    for block, next_block in {
        'blackstone': 'gravel',
    }.items():
        create_loot_table_block(block, next_block, {'blackstone_slab':1})

    create_loot_table_block('gilded_blackstone', 'blackstone', {'gold_nugget':1})



    # nether
    for block, next_block in {
        'nether_bricks': 'nether_brick_slab',
        'red_nether_bricks': 'red_nether_brick_slab',
    }.items():
        create_slabs_to_block_recipe_and_advancement(next_block,block)
    
    create_loot_table_block('chiseled_nether_bricks', 'nether_bricks')
    create_loot_table_block('nether_bricks', 'cracked_nether_bricks')

    create_loot_table_block('cracked_nether_bricks', 'netherrack', {'nether_brick':3})
    create_loot_table_block('warped_nylium', 'netherrack')
    create_loot_table_block('crimson_nylium', 'netherrack')
    
    create_loot_table_block('nether_brick_wall', 'nether_brick_fence', {'nether_brick':1})
    create_loot_table_block('red_nether_bricks', 'netherrack', {'nether_wart':2,'nether_brick':1})
    
    create_loot_table_block('nether_gold_ore', 'netherrack', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "count": {
                    "type": "minecraft:uniform",
                    "max": 6,
                    "min": 2
                  },
                  "function": "minecraft:set_count"
                },
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:gold_nugget"
            }
            ]
        }
    )
    create_loot_table_block('nether_quartz_ore', 'netherrack', drop_ore={
            "rolls": 1,
            "entries": [
            {
              "type": "minecraft:item",
              "functions": [
                {
                  "enchantment": "minecraft:fortune",
                  "formula": "minecraft:ore_drops",
                  "function": "minecraft:apply_bonus"
                },
                {
                  "function": "minecraft:explosion_decay"
                }
              ],
              "name": "minecraft:quartz"
            }
            ]
        }
    )


    # sandstone
    for sand in [
        'red_sand',
        'sand',
    ]:
        for block, next_block in {
            f'{sand}stone': f'{sand}stone_slab',
            f'smooth_{sand}stone': f'smooth_{sand}stone_slab',
            f'cut_{sand}stone': f'cut_{sand}stone_slab',
        }.items():
            create_slabs_to_block_recipe_and_advancement(next_block,block)
            
        for block, next_block in {
            f'smooth_{sand}stone': f'{sand}stone',
            f'cut_{sand}stone': f'{sand}stone',
        }.items():
            create_loot_table_block(f'{block}_slab', f'{next_block}_slab', block_state_property='slab')
            
        create_loot_table_block(f'smooth_{sand}stone_stairs', f'{sand}stone_stairs')
    
    
        create_loot_table_block(f'smooth_{sand}stone', f'{sand}stone')
        create_loot_table_block(f'cut_{sand}stone', f'{sand}stone')
        create_loot_table_block(f'chiseled_{sand}stone', f'{sand}stone')
    
        create_loot_table_block(f'{sand}stone', sand, {sand:3})



    # dirt
    for block, next_block in {
        'grass_block': 'dirt',
        'podzol': 'dirt',
        'mycelium': 'dirt',
        'coarse_dirt': 'dirt',
        'rooted_dirt': 'dirt',
        'mud': 'dirt',
    }.items():
        create_loot_table_block(block, next_block)


    # colored blocks
    for color in [
    'black',
    'blue',
    'brown',
    'cyan',
    'gray',
    'green',
    'light_blue',
    'light_gray',
    'lime',
    'magenta',
    'orange',
    'pink',
    'purple',
    'red',
    'white',
    'yellow',
    ]:
        for block, next_block in {
            f'{color}_concrete': f'{color}_concrete_powder', 
            f'{color}_glazed_terracotta': f'{color}_terracotta', 
        }.items():
            create_loot_table_block(block, next_block)


    # tuff
    for block, next_block in {
        'tuff': 'tuff_slab',
        'polished_tuff': 'polished_tuff_slab',
        'tuff_bricks': 'tuff_brick_slab',
    }.items():
        create_slabs_to_block_recipe_and_advancement(next_block,block)
    
    for block, next_block in {
        'tuff_brick': 'polished_tuff',
        'polished_tuff': 'tuff',
    }.items():
        create_loot_table_block(f'{block}_slab', f'{next_block}_slab', block_state_property='slab')
        create_loot_table_block(f'{block}_stairs', f'{next_block}_stairs', block_state_property='stairs')
        create_loot_table_block(f'{block}_wall', f'{next_block}_wall')

    for block, next_block in {
        'chiseled_tuff': 'tuff',
        'chiseled_tuff_bricks': 'tuff_bricks',
        'tuff_bricks': 'polished_tuff',
        'polished_tuff': 'tuff',
    }.items():
        create_loot_table_block(block, next_block, {'tuff_slab':1,'gravel':1})

    create_loot_table_block('tuff', 'gravel', {'tuff_slab':1,'gravel':1})


    # stone variants
    for variant in [
        'diorite',
        'andesite',
        'granite',
    ]:
        create_slabs_to_block_recipe_and_advancement(variant+'_slab', variant)
        create_slabs_to_block_recipe_and_advancement('polished_'+variant+'_slab', 'polished_'+variant)
        create_loot_table_block(variant, 'gravel', {f'{variant}_slab':1})
        create_loot_table_block(f'polished_{variant}', variant)
        create_loot_table_block(f'polished_{variant}_slab', f'{variant}_slab', block_state_property='slab')
        create_loot_table_block(f'polished_{variant}_stairs', f'{variant}_stairs', block_state_property='stairs')
    
    
    # copper
    for oxidation, next_oxidation in {
        'exposed_': '',
        'weathered_': 'exposed_',
        'oxidized_': 'weathered_',
    }.items():
        create_loot_table_block(f'waxed_{oxidation}copper', f'{oxidation}copper')
        if next_oxidation != '': create_loot_table_block(f'{oxidation}copper', f'{next_oxidation}copper')
        else: create_loot_table_block(f'{oxidation}copper', f'copper_block')
        for block in [
            'chiseled_copper',
            'copper_grate',
            'cut_copper',
            'copper_bars',
            'copper_bulb',
            'copper_chain',
        ]:
            create_loot_table_block(f'waxed_{oxidation}{block}', f'{oxidation}{block}')
            create_loot_table_block(f'{oxidation}{block}', f'{next_oxidation}{block}')
        
        create_loot_table_block(f'{oxidation}cut_copper_slab', f'{next_oxidation}cut_copper_slab', block_state_property='slab')
        create_loot_table_block(f'waxed_{oxidation}cut_copper_stairs', f'{oxidation}cut_copper_stairs', block_state_property='stairs')

    for block, next_block in {
        'cut_copper': 'copper_block',
        'chiseled_copper': 'cut_copper',
    }.items():
        create_loot_table_block(block, next_block)

    create_loot_table_block(f'exposed_copper', f'copper_block')
    create_loot_table_block(f'waxed_copper_block', f'copper_block')


    # other things
    create_loot_table_block('polished_basalt', 'basalt', block_state_property='directional')

    for block, next_block in {
        'smooth_basalt': 'basalt',
        'blue_ice': 'packed_ice',
        'packed_ice': 'snow_block',
        'crying_obsidian': 'obsidian',
        'end_stone_bricks': 'end_stone',
        'end_stone': 'sand',
        'packed_mud': 'mud',
        'mud_bricks': 'mud',
        'purpur_pillar': 'purpur_block',
        'smooth_quartz': 'quartz_block',
        'quartz_pillar': 'quartz_block',
        'quartz_bricks': 'quartz_block',
        'chiseled_quartz_block': 'quartz_block',
    }.items():
        create_loot_table_block(block, next_block)

    create_loot_table_block('muddy_mangrove_roots', 'mangrove_roots', {'mud':1})

    for block, next_block in {
        'prismarine_bricks': 'prismarine',
        'dark_prismarine': 'prismarine',
    }.items():
        create_loot_table_block(block, next_block, {next_block:2})
    for block, next_block in {
        'prismarine_brick': 'prismarine',
        'dark_prismarine': 'prismarine',
    }.items():
        create_loot_table_block(f'{block}_slab', f'{next_block}_slab', block_state_property='slab')
        create_loot_table_block(f'{block}_stairs', f'{next_block}_stairs', block_state_property='stairs')
        
    for block, next_block in {
        'smooth_quartz': 'quartz',
    }.items():
        create_loot_table_block(f'{block}_slab', f'{next_block}_slab', block_state_property='slab')
        create_loot_table_block(f'{block}_stairs', f'{next_block}_stairs', block_state_property='stairs')
    create_loot_table_block('quartz_block', 'quartz_slab', {'quartz_slab':1})

    # sulfur
    for block, next_block in {
        'sulfur': 'sulfur_slab',
        'polished_sulfur': 'polished_sulfur_slab',
        'sulfur_bricks': 'sulfur_brick_slab',
    }.items():
        create_slabs_to_block_recipe_and_advancement(next_block,block)
    
    for block, next_block in {
        'potent_sulfur': 'sulfur',
        'polished_sulfur': 'sulfur',
        'sulfur_bricks': 'polished_sulfur',
        'chiseled_sulfur': 'sulfur',
    }.items():
        create_loot_table_block(block, next_block)

    for block, next_block in {
        'polished_sulfur': 'sulfur',
        'sulfur_brick': 'polished_sulfur',
    }.items():
        create_loot_table_block(f'{block}_slab', f'{next_block}_slab', block_state_property='slab')
        create_loot_table_block(f'{block}_stairs', f'{next_block}_stairs', block_state_property='stairs')
        create_loot_table_block(f'{block}_wall', f'{next_block}_wall')

    # cinnabar
    for block, next_block in {
        'cinnabar': 'cinnabar_slab',
        'polished_cinnabar': 'polished_cinnabar_slab',
        'cinnabar_bricks': 'cinnabar_brick_slab',
    }.items():
        create_slabs_to_block_recipe_and_advancement(next_block,block)
    
    for block, next_block in {
        'polished_cinnabar': 'cinnabar',
        'cinnabar_bricks': 'polished_cinnabar',
        'chiseled_cinnabar': 'cinnabar',
    }.items():
        create_loot_table_block(block, next_block)

    for block, next_block in {
        'polished_cinnabar': 'cinnabar',
        'cinnabar_brick': 'polished_cinnabar',
    }.items():
        create_loot_table_block(f'{block}_slab', f'{next_block}_slab', block_state_property='slab')
        create_loot_table_block(f'{block}_stairs', f'{next_block}_stairs', block_state_property='stairs')
        create_loot_table_block(f'{block}_wall', f'{next_block}_wall')

        

    save_data(f'{result_path}\\{datapack_name}\\tags\\item\\onion_block.json', {"values": all_onion_blocks}, 0)

    return print(f'{style_progress}Done!{style_reset}')



main()
