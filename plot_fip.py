from sunpy.map import Map
import matplotlib.pyplot as plt
import matplotlib.colors as mcolor

fip_map = Map("fip_out/fip_map.fits")
fig = plt.figure()
ax = fig.add_subplot(111, projection=fip_map)
cmap = plt.get_cmap('RdBu')
cmap.set_bad('gray')
im = fip_map.plot(axes=ax, cmap=cmap, norm=mcolor.LogNorm(vmin=0.1, vmax=10))
ax.set_aspect(0.25)
fig.colorbar(im, label="FIP bias")
plt.show()
