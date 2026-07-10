execute at @s if block ~1 ~ ~ #air run return run tp @e[type=item,distance=..0.75] ~1 ~ ~
execute at @s if block ~-1 ~ ~ #air run return run tp @e[type=item,distance=..0.75] ~-1 ~ ~
execute at @s if block ~ ~1 ~ #air run return run tp @e[type=item,distance=..0.75] ~ ~1 ~
execute at @s if block ~ ~-1 ~ #air run return run tp @e[type=item,distance=..0.75] ~ ~-1 ~
execute at @s if block ~ ~ ~1 #air run return run tp @e[type=item,distance=..0.75] ~ ~ ~1
execute at @s if block ~ ~ ~-1 #air run return run tp @e[type=item,distance=..0.75] ~ ~ ~-1
execute as @e[type=item,distance=..0.75] run data merge entity @s {Motion:[0d,0d,0d]}