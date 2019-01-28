## Self-Adjoint H Sphere Uniform Source Test ##

# Forward Setup
Infinite medium H sphere of density 5.53e-7 g/cm3.
0.001 - 0.01 MeV isotropic uniform source at the center of the sphere.
Measure flux and current on the surface and the track flux for spheres of radius 10.0, 15.0, and 20.0 cm.
Set energy bins for all estimators.

# Adjoint Setup
Infinite medium H sphere of density 5.53e-7 g/cm3.
cutoff energy to 0.01 MeV isotropic isotropic uniform source at the center of the sphere.
Measure adjoint flux and current on the surface and the track flux for spheres of radius 10.0, 15.0, and 20.0 cm.
Set source energy bins for all estimators.
Set a uniform distribution to match the forward source as a response function.

# Trelis geometry commands
To construct the geometry run 'construct_geometry.sh' and enter the desired energy.

# Running the simulation if FRENSIE

# Running the simulation if MCNP6.2

# Plotting results