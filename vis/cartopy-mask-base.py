import matplotlib.pyplot as plt
import numpy as np

import cartopy.crs as ccrs
import cartopy.feature as cfeature


fig = plt.figure(figsize=(14, 7))
ax = fig.add_subplot(
    1, 1, 1, projection=ccrs.Robinson(central_longitude=300.)
    # could also try, for sphere: projection=ccrs.Orthographic(-10, 45))
)

ax.add_feature(cfeature.OCEAN, zorder=0)
ax.add_feature(cfeature.LAND, zorder=0, edgecolor='black')

ax.set_global()
ax.stock_img()

plt.tight_layout()
plt.savefig("globe_cartopy_1.png")
plt.show()
