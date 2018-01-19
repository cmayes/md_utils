structure          {structure}
coordinates        {coordinates}

set temp           303.15

outputname         {output_name}
set inputname      {input_name}
binCoordinates     $inputname.coor;    # coordinates from last run (binary)
binVelocities      $inputname.vel;     # velocities from last run (binary)
extendedSystem     $inputname.xsc;     # cell dimensions from last run (binary)
firsttimestep      {first}
restartfreq      10000;                # 500 steps = every 1ps
dcdfreq           2500;
dcdUnitCell        yes;                # the file will contain unit cell info in the style of
                                       # charmm dcd files. if yes, the dcd files will contain
                                       # unit cell information in the style of charmm DCD files.
xstFreq           1500;                # XSTFreq: control how often the extended systen configuration
                                       # will be appended to the XST file
outputEnergies    1000;                # 125 steps = every 0.25ps
                                       # The number of timesteps between each energy output of NAMD
outputTiming      1500;                # The number of timesteps between each timing output shows
                                       # time per step and time to completion

# Force-Field Parameters
paraTypeCharmm     on;                 # We're using charmm type parameter file(s)
                                       # multiple definitions may be used but only one file per definition
parameters          toppar/par_all36_prot.prm
parameters          toppar/par_all36_na.prm
parameters          toppar/par_all36_carb.prm
parameters          toppar/par_all36_lipid.prm
parameters          toppar/par_all36_cgenff.prm
parameters          toppar/toppar_all36_prot_retinol.str
parameters          toppar/toppar_all36_na_rna_modified.str
parameters          toppar/toppar_all36_carb_glycopeptide.str
parameters          toppar/toppar_all36_prot_fluoro_alkanes.str
parameters          toppar/toppar_all36_prot_na_combined.str
parameters          toppar/toppar_all36_prot_heme.str
parameters          toppar/toppar_all36_lipid_bacterial.str
parameters          toppar/toppar_all36_lipid_miscellaneous.str
parameters          toppar/toppar_all36_lipid_cholesterol.str
parameters          toppar/toppar_all36_lipid_yeast.str
parameters          toppar/toppar_all36_lipid_sphingo.str
parameters          toppar/toppar_all36_lipid_inositol.str
parameters          toppar/toppar_all36_lipid_cardiolipin.str
parameters          toppar/toppar_all36_lipid_detergent.str
parameters          toppar/toppar_all36_lipid_lps.str
parameters          toppar/toppar_water_ions.str
parameters          toppar/toppar_dum_noble_gases.str
parameters          toppar/toppar_all36_na_nad_ppi.str
parameters          toppar/toppar_all36_carb_glycolipid.str
parameters          toppar/toppar_all36_carb_imlab.str
source step5_assembly.namd.str

# These are specified by CHARMM
exclude             scaled1-4          # non-bonded exclusion policy to use "none,1-2,1-3,1-4,or scaled1-4"
                                       # 1-2: all atoms pairs that are bonded are going to be ignored
                                       # 1-3: 3 consecutively bonded are excluded
                                       # scaled1-4: include all the 1-3, and modified 1-4 interactions
                                       # electrostatic scaled by 1-4scaling factor 1.0
                                       # vdW special 1-4 parameters in charmm parameter file.
1-4scaling          1.0
switching           on
vdwForceSwitching   yes;               # New option for force-based switching of vdW
                                       # if both switching and vdwForceSwitching are on CHARMM force
                                       # switching is used for vdW forces.

# You have some freedom choosing the cutoff
cutoff              12.0;              # may use smaller, maybe 10., with PME
switchdist          10.0;              # cutoff - 2.
                                       # switchdist - where you start to switch
                                       # cutoff - where you stop accounting for nonbond interactions.
                                       # correspondence in charmm:
                                       # (cutnb,ctofnb,ctonnb = pairlistdist,cutoff,switchdist)
pairlistdist        16.0;              # stores the all the pairs with in the distance it should be larger
                                       # than cutoff( + 2.)
stepspercycle       20;                # 20 redo pairlists every ten steps
pairlistsPerCycle    2;                # 2 is the default
                                       # cycle represents the number of steps between atom reassignments
                                       # this means every 20/2=10 steps the pairlist will be updated

# Integrator Parameters
timestep            2.0;               # fs/step
rigidBonds          all;               # Bound constraint all bonds involving H are fixed in length
nonbondedFreq       1;                 # nonbonded forces every step
fullElectFrequency  1;                 # PME every step

wrapWater           on;                # wrap water to central cell
wrapAll             on;                # wrap other molecules too
wrapNearest         off;               # use for non-rectangular cells (wrap to the nearest image)

# PME (for full-system periodic electrostatics)
source checkfft.str

PME                yes;
PMEInterpOrder       6;                # interpolation order (spline order 6 in charmm)
PMEGridSizeX     $fftx;                # should be close to the cell size
PMEGridSizeY     $ffty;                # corresponds to the charmm input fftx/y/z
PMEGridSizeZ     $fftz;

# Constant Pressure Control (variable volume)
useGroupPressure       yes;            # use a hydrogen-group based pseudo-molecular viral to calcualte pressure and
                                       # has less fluctuation, is needed for rigid bonds (rigidBonds/SHAKE)
useFlexibleCell        yes;            # yes for anisotropic system like membrane
useConstantRatio       yes;            # keeps the ratio of the unit cell in the x-y plane constant A=B

langevinPiston          on;            # Nose-Hoover Langevin piston pressure control
langevinPistonTarget  1.01325;         # target pressure in bar 1atm = 1.01325bar
langevinPistonPeriod  50.0;            # oscillation period in fs. correspond to pgamma T=50fs=0.05ps
                                       # f=1/T=20.0(pgamma)
langevinPistonDecay   25.0;            # oscillation decay time. smaller value correspons to larger random
                                       # forces and increased coupling to the Langevin temp bath.
                                       # Equall or smaller than piston period
langevinPistonTemp   $temp;            # coupled to heat bath

# Constant Temperature Control
langevin                on;            # langevin dynamics
langevinDamping        1.0;            # damping coefficient of 1/ps (keep low)
langevinTemp         $temp;            # random noise at this level
langevinHydrogen       off;            # don't couple bath to hydrogens

# run
numsteps        {last:>10};            # maybe write out end in ns
run               {run:>8};            # maybe write out run in ns