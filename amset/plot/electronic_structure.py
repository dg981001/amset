import logging
from pathlib import Path

from amset.constants import defaults
from amset.electronic_structure.interpolate import Interpolater
from amset.log import initialize_amset_logger
from pymatgen.electronic_structure.bandstructure import BandStructure
from sumo.plotting.bs_plotter import SBSPlotter
from sumo.plotting.dos_plotter import SDOSPlotter

logger = logging.getLogger(__name__)


class ElectronicStructurePlotter(object):
    def __init__(
        self,
        bandstructure: BandStructure,
        nelect: int,
        soc: bool = False,
        interpolation_factor=defaults["interpolation_factor"],
        print_log=defaults["print_log"],
        symprec=defaults["symprec"],
        energy_cutoff=None,
    ):
        if print_log:
            initialize_amset_logger(filename="amset_electronic_structure_plot.log")

        self.symprec = symprec
        self.interpolater = Interpolater(
            bandstructure, nelect, interpolation_factor=interpolation_factor, soc=soc
        )
        self.structure = bandstructure.structure
        self.energy_cutoff = energy_cutoff

    @classmethod
    def from_vasprun(cls, vasprun, **kwargs):
        from pymatgen.io.vasp import Vasprun

        if isinstance(vasprun, str):
            vasprun_gz = vasprun + ".gz"

            if Path(vasprun).exists():
                vasprun = Vasprun(vasprun)

            elif Path(vasprun_gz).exists():
                vasprun = Vasprun(vasprun_gz)

        bandstructure = vasprun.get_band_structure()
        nelect = vasprun.parameters["NELECT"]
        soc = vasprun.parameters["LSORBIT"]
        return cls(bandstructure, nelect, soc=soc, **kwargs)

    def get_plot(
        self,
        plot_dos=True,
        plot_band_structure=True,
        kpath=None,
        line_density=100.0,
        dos_kpoints=50.0,
        dos_estep=defaults["dos_estep"],
        zero_to_efermi=True,
        vbm_cbm_marker=False,
        height=6,
        width=None,
        emin=None,
        emax=None,
        elabel="Energy (eV)",
        plt=None,
        dos_aspect=3,
        aspect=None,
        style=None,
        no_base_style=False,
        fonts=None,
    ):
        if width is None and plot_band_structure:
            width = 6

        if plot_band_structure:
            logger.info("Generating band structure...")
            bs_plotter = self.get_bs_plotter(line_density=line_density, kpath=kpath)

        if plot_dos:
            logger.info("Generating density of states...")
            dos_plotter = self.get_dos_plotter(
                dos_density=dos_kpoints, dos_estep=dos_estep
            )

        logger.info("Plotting...")
        common_kwargs = dict(
            zero_to_efermi=zero_to_efermi,
            width=width,
            height=height,
            plt=plt,
            style=style,
            no_base_style=no_base_style,
            fonts=fonts,
        )
        if plot_band_structure:
            bs_kwargs = {
                "ymin": emin,
                "ymax": emax,
                "ylabel": elabel,
                "aspect": aspect,
                "vbm_cbm_marker": vbm_cbm_marker,
            }
            common_kwargs.update(bs_kwargs)

            if plot_dos:
                bs_dos_kwargs = {
                    # "dos_label": "DOS",
                    "dos_aspect": dos_aspect,
                    "dos_plotter": dos_plotter,
                    "plot_dos_legend": False,
                }
                common_kwargs.update(bs_dos_kwargs)

            return bs_plotter.get_plot(**common_kwargs)

        else:
            dos_kwargs = {
                "xmin": emin,
                "xmax": emax,
                "legend_on": False,
                "xlabel": elabel,
                "ylabel": "DOS",
            }
            common_kwargs.update(dos_kwargs)

            return dos_plotter.get_plot(common_kwargs)

    def get_bs_plotter(self, line_density=100, kpath=None):
        lm_bs = self.interpolater.get_line_mode_band_structure(
            line_density=line_density,
            kpath=kpath,
            symprec=self.symprec,
            energy_cutoff=self.energy_cutoff,
        )
        return SBSPlotter(lm_bs)

    def get_dos_plotter(self, dos_density=50.0, dos_estep=defaults["dos_estep"]):
        dos = self.interpolater.get_dos(
            kpoint_mesh=dos_density,
            symprec=self.symprec,
            estep=dos_estep,
            energy_cutoff=self.energy_cutoff,
        )

        return SDOSPlotter(dos, {})
