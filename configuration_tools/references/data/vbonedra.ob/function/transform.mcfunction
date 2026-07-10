# try setblock
execute store success entity @s Item.components."minecraft:custom_data"."vbonedra.ob".succeed_setblock byte 1 run function vbonedra.ob:transform_setblock with entity @s Item.components."minecraft:custom_data"."vbonedra.ob"
# clear item if succeed
execute unless data entity @s Item.components."minecraft:custom_data"."vbonedra.ob".succeed_setblock run kill @s
execute unless data entity @s Item.components."minecraft:custom_data"."vbonedra.ob".succeed_setblock run return 1
# summon if setblock failed
execute store result entity @s Item.components."minecraft:custom_data"."vbonedra.ob".x int 1 run data get entity @s Pos[0]
execute store result entity @s Item.components."minecraft:custom_data"."vbonedra.ob".y int 1 run data get entity @s Pos[1]
execute store result entity @s Item.components."minecraft:custom_data"."vbonedra.ob".z int 1 run data get entity @s Pos[2]
function vbonedra.ob:transform_summon with entity @s Item.components."minecraft:custom_data"."vbonedra.ob"
# clear item
kill @s
return 1