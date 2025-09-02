import matplotlib.pyplot as plt
import contextily as ctx
from pyproj import Transformer
from geoapify_planner import get_scenic_points
import os

def to_webmerc(lon, lat):
    transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
    x, y = transformer.transform(lon, lat)
    return float(x), float(y)

def main():
    scenic_points = get_scenic_points()
    print(f"Loaded {len(scenic_points)} scenic points")

    coords = []
    for idx, p in enumerate(scenic_points[:10]):
        print(f"{idx:2d}  {p['name'][:25]:25s}  lon={p['coords'][0]:.6f}  lat={p['coords'][1]:.6f}")

    # Transform all points
    xy = [to_webmerc(p['coords'][0], p['coords'][1]) for p in scenic_points]
    scenic_x, scenic_y = zip(*xy)

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(scenic_x, scenic_y, c='red', marker='^', s=60, edgecolor='k', label='Scenic point')
    ax.set_title('Lake District scenic points – debug view')

    margin = 1000
    ax.set_xlim(min(scenic_x)-margin, max(scenic_x)+margin)
    ax.set_ylim(min(scenic_y)-margin, max(scenic_y)+margin)

    # Try to use local MBTiles file for offline basemap
    mbtiles_path = 'lake_district.mbtiles'
    if os.path.exists(mbtiles_path):
        print(f"Using offline MBTiles basemap: {mbtiles_path}")
        offline = ctx.TileProvider(f'sqlite:///{mbtiles_path}')
        ctx.add_basemap(ax, crs='epsg:3857', source=offline)
    else:
        print("No offline MBTiles found. No basemap will be shown.")
        ax.set_facecolor('#f0f0f0')

    ax.legend(loc='upper left')
    fig.tight_layout()
    fig.savefig('scenic_points_debug.png', dpi=150)
    print("Saved scenic_points_debug.png in the project folder")

if __name__ == "__main__":
    main() 