$setblock ~ ~ ~ $(id)$(setblock) destroy
# move items if could so they don't fly away because of collision with transformed block
execute if entity @p[distance=..5] run function vbonedra.ob:move_items