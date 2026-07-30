import geopandas as gpd

# --- Load original shapefile ---
shapefile_path = r"D:\Reserch Material\Home Ownership\Data Pengantar\batas-administrasi-indonesia-master\batas-administrasi-indonesia-master\Provinsi\Provinsi SHP.7z\Provinsi.shp"
gdf_provinces = gpd.read_file(shapefile_path)

# --- Ensure correct CRS ---
if gdf_provinces.crs != "EPSG:4326":
    gdf_provinces = gdf_provinces.to_crs(epsg=4326)

# --- Filter only the target Papua provinces to save space ---
target_provinces = ['Papua', 'Papua Selatan', 'Papua Tengah', 'Papua Pegunungan']
gdf_papua = gdf_provinces[gdf_provinces['PROVINSI'].isin(target_provinces)].copy()

# --- Optional: Simplify geometries to reduce vertex count and file size ---
# tolerance=0.01 simplifies boundaries without noticeably degrading visual quality on small maps
gdf_papua['geometry'] = gdf_papua['geometry'].simplify(tolerance=0.01, preserve_topology=True)

# --- Export options for lightweight deployment ---
# Option A: GeoParquet (Recommended for performance and smallest file size)
gdf_papua.to_parquet("papua_provinces.parquet")

# Option B: Minified GeoJSON (Great for standard web hosting)
# gdf_papua.to_file("papua_provinces.geojson", driver="GeoJSON")

print("Successfully exported optimized Papua provinces file!")