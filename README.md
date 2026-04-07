<<<<<<< HEAD
# Social-Media-Data-Generator
SMDG is an ongoing project to finish my university computer engineering course.
=======
# Social Media Data Generator

Gerador de dados sintéticos georreferenciados para redes sociais baseadas em localização.

Este projeto foi desenvolvido como Trabalho de Conclusão de Curso em Engenharia de Computação, com foco na geração de pontos sintéticos espacialmente coerentes a partir de camadas geográficas, restrições espaciais e atributos socioespaciais, sem utilizar dados pessoais reais.

O sistema foi concebido para apoiar estudos em simulação urbana, análise espacial, mobilidade, testes metodológicos e experimentos com dados sintéticos em contextos onde o acesso a dados reais é restrito por questões éticas, legais ou operacionais.

## Objetivo

O projeto busca gerar pontos sintéticos que simulem a distribuição espacial de atividade em redes sociais, considerando:

- uma área principal de geração;
- exclusão de regiões onde não se espera atividade;
- concentração opcional em áreas de interesse;
- ponderação probabilística por atributos territoriais, como densidade demográfica e vulnerabilidade social.

## Funcionalidades

- Geração de pontos aleatórios dentro de uma área geográfica válida;
- Exclusão de regiões a partir de shapefiles poligonais ou lineares;
- Concentração opcional de pontos em regiões específicas;
- Distribuição probabilística com base em shapefiles com coluna `prob`;
- Construção de pesos espaciais a partir de densidade populacional e IPVS;
- Exportação de resultados em:
  - CSV com latitude, longitude e timestamp;
  - PNG com visualização estática;
  - HTML com mapa interativo;
- Agregação dos dados sintéticos e reais por unidade espacial;
- Comparação cartográfica entre distribuições reais e sintéticas;
- Validação estatística por Moran global, Pearson e Kappa.

## Estrutura do projeto

### Arquivos principais

- `generator.py`  
  Script principal de geração dos pontos sintéticos. Lê a área principal, exclusões, áreas de concentração e shapefile ponderado, executa a geração e salva as saídas.

- `utilities.py`  
  Funções auxiliares usadas pelo gerador, como criação da área permitida, geração de pontos, construção de áreas circulares e manipulação espacial básica.

- `regulator.py`  
  Constrói um shapefile ponderado com a coluna `prob` a partir de densidade demográfica, IPVS e população.

- `agregador.py`  
  Agrega os pontos sintéticos e os pontos reais por polígono, produzindo um GeoPackage com contagens por unidade espacial.

- `comparador.py`  
  Gera mapas comparativos lado a lado entre a distribuição real e a sintética.

- `validator.py`  
  Calcula métricas de validação espacial e estatística, incluindo Moran global, correlação de Pearson e índice Kappa.

- `exec.sh`  
  Script de execução do gerador principal com parâmetros definidos manualmente.

### Arquivos auxiliares

- `README.md`  
  Documentação principal do projeto.

## Requisitos

- Python 3.10 ou superior
- Ambiente com suporte a bibliotecas geoespaciais
- Arquivos de entrada em formato compatível com `GeoPandas` (`.shp`, `.zip`, `.gpkg`, `.csv`)

## Dependências Python

Instale as dependências com:

```bash
pip install geopandas pandas numpy matplotlib scipy libpysal esda mapclassify folium shapely pyogrio fiona
```

Dependendo do sistema operacional, pode ser necessário instalar dependências nativas para bibliotecas geoespaciais, especialmente:

- GDAL
- GEOS
- PROJ

Em Linux, recomenda-se o uso de ambiente virtual e, se necessário, instalação via gerenciador do sistema.

## Formato esperado dos dados de entrada

### 1. Shapefile principal

Arquivo que representa a área total onde os pontos poderão ser gerados.

Exemplo:
- `Distrito-SP.zip`

### 2. Shapefiles de exclusão

Arquivos que representam áreas a serem removidas da geração.

Exemplos:
- represas;
- linhas férreas;
- faixas viárias;
- zonas específicas sem interesse analítico.

### 3. Shapefile ponderado

Arquivo vetorial com uma coluna chamada `prob`, usada para distribuir os pontos restantes de forma não uniforme.

Exemplo:
- `final-SP.zip`

### 4. CSV de dados reais

Arquivo com coordenadas reais, usado para comparação e validação.

Colunas esperadas no estado atual:
- `lat`
- `lon`

### 5. CSV de dados sintéticos

Saída do gerador, contendo:
- `latitude`
- `longitude`
- `timestamp`

## Como executar

### 1. Gerar shapefile ponderado com o regulador

```bash
python regulator.py densidade-SP.zip ipvs-SP.zip --lambda-dens 0.5 --mu-ipvs 0.5 --out-prefix final-SP
```

Esse passo produz um shapefile com a coluna `prob`, que pode ser usado pelo gerador principal.

### 2. Gerar os pontos sintéticos

```bash
bash exec.sh
```

Ou diretamente:

```bash
python generator.py \
  10000 \
  180 \
  1719304546 \
  1719701874 \
  "Distrito-SP.zip" \
  "represa-SP.zip" "trem-SP.zip" "faixas-SP.zip" \
  --weighted_shapefile "final-SP.zip"
```

### 3. Agregar dados reais e sintéticos

```bash
python agregador.py
```

### 4. Gerar mapa comparativo

```bash
python comparador.py
```

### 5. Executar validação estatística

```bash
python validator.py
```

## Saídas geradas

### Pelo `generator.py`

- `output/points.csv`
- `output/map.png`
- `output/map.html`

### Pelo `regulator.py`

- pasta com shapefile regulado
- arquivo `.zip` correspondente, se `--no-zip` não for usado

### Pelo `agregador.py`

- `sp_aggregado.gpkg`

### Pelo `comparador.py`

- `comparacao_distritos.png`

## Observações importantes

- O projeto trabalha com arquivos geoespaciais externos, que devem estar consistentes em relação à geometria e ao sistema de referência.
- Se um shapefile estiver sem CRS definido, alguns scripts assumem `EPSG:31983`.
- A qualidade geométrica dos arquivos de entrada influencia diretamente a robustez das operações espaciais.
- O gerador foi concebido como ferramenta modular, permitindo continuação e adaptação em trabalhos futuros.

## Possibilidades de continuidade

O projeto pode ser estendido com:

- inclusão de perfis sintéticos de usuários;
- modelagem temporal mais realista;
- novos atributos territoriais;
- calibração empírica dos pesos;
- otimização computacional para volumes maiores;
- integração com análise de redes e geração de conteúdo sintético.

## Autor

Guilherme Gabriel de Oliveira

## Licença

Este projeto foi desenvolvido em contexto acadêmico. Recomenda-se consultar o trabalho final e a instituição para definir a forma mais adequada de reutilização e citação.
>>>>>>> 0b6ef74 (Updated project files)
