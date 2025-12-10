#!/bin/bash

# Args order:
# points_number
# temporal_component
# start_timestamp
# end_timestamp
# shapefile_main
# exclusion_shapefiles
# concentration_targets (file:ratio[:circle:radius:position])

points_number=10000
temporal_component=180
start_timestamp=1719304546
end_timestamp=1719701874
shapefile_main="Distrito-SP.zip"
#exclusion_shapefiles=("")
exclusion_shapefiles=("represa-SP.zip" "trem-SP.zip" "faixas-SP.zip")
weighted_shapefile="final-SP.zip"

#concentration_targets=(
#  "hospital-SP.zip:0.05:circle:5000:in"
#  "esporte-SP.zip:0.05:circle:5000:in"
# "mercados-SP.zip:0.05"
#  "POC_exclude_center.zip:0.75"  # modo padrão (dentro do polígono)
#)

python generator.py \
  $points_number \
  $temporal_component \
  $start_timestamp \
  $end_timestamp \
  "$shapefile_main" \
  "${exclusion_shapefiles[@]}" \
  --concentration_targets "${concentration_targets[@]}" \
  --weighted_shapefile "$weighted_shapefile"
