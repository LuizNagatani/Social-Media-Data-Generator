#!/bin/bash

<<<<<<< HEAD
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
=======
# Total de pontos sintéticos a gerar.
points_number=10000

# Componente temporal mantido por compatibilidade com o gerador.
temporal_component=180

# Início e fim do intervalo temporal em timestamp Unix.
start_timestamp=1719304546
end_timestamp=1719701874

# Shapefile principal que define a área base de geração.
shapefile_main="Distrito-SP.zip"

# Shapefiles de exclusão removidos da área base.
exclusion_shapefiles=("represa-SP.zip" "trem-SP.zip" "faixas-SP.zip")

# Shapefile ponderado com a coluna "prob" usada para distribuição probabilística.
weighted_shapefile="final-SP.zip"

# Áreas opcionais de concentração no formato:
# "arquivo:proporcao[:modo[:raio[:posicao]]]"
# - modo padrão: polygon
# - modo circle: exige raio e posição ("in", "out" ou "both")
# concentration_targets=(
#   "hospital-SP.zip:0.05:circle:5000:in"
#   "esporte-SP.zip:0.05:circle:5000:in"
#   "mercados-SP.zip:0.05"
#   "POC_exclude_center.zip:0.75"
# )
>>>>>>> 0b6ef74 (Updated project files)

python generator.py \
  $points_number \
  $temporal_component \
  $start_timestamp \
  $end_timestamp \
  "$shapefile_main" \
  "${exclusion_shapefiles[@]}" \
  --concentration_targets "${concentration_targets[@]}" \
<<<<<<< HEAD
  --weighted_shapefile "$weighted_shapefile"
=======
  --weighted_shapefile "$weighted_shapefile"
>>>>>>> 0b6ef74 (Updated project files)
