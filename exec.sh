#!/bin/bash

# Args order:
# points_number
# temporal_component
# start_timestamp
# end_timestamp
# shapefile_main
# exclusion_shapefiles
# concentration_targets (file:ratio[:circle:radius:position])

points_number=10
temporal_component=180
start_timestamp=1719304546
end_timestamp=1719701874
shapefile_main="BR_pais.zip"
exclusion_shapefiles=("SP_UF.zip")

concentration_targets=(
  "MG_UF.zip:0.4:circle:5000:in"
  "PR_UF.zip:0.3:circle:10000:out"
  "AC_UF.zip:0.2"  # modo padrão (dentro do polígono)
)

python generator.py \
  $points_number \
  $temporal_component \
  $start_timestamp \
  $end_timestamp \
  "$shapefile_main" \
  "${exclusion_shapefiles[@]}" \
  --concentration_targets "${concentration_targets[@]}"
