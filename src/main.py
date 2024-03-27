from argparse import ArgumentParser
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from plot import plot_field_contour, plot_report
from report import DiscreteFieldReport, FullFieldReport
from constants import magnitude
from coil import Coil

matplotlib.rcParams.update({
    "pgf.texsystem": "pdflatex",
    'font.family': 'serif',
    'font.size' : 14,
    'text.usetex': False,
    'pgf.rcfonts': False,
})

parser = ArgumentParser(
    prog = 'coilsim',
    description = 'Simulate and compare coil designs',
)

parser.add_argument(
    'file',
    help = 'Path to an input coil file',
)

parser.add_argument(
    '-e',
    '--allowable-error',
    dest = 'allowable_error',
    help = 'Value in mT that field may deviate from the mean when checking field uniformity',
    default = 0.05,
    type = float,
)

cmds = parser.add_subparsers(
    title = 'COMMANDS',
    help = 'Simulations to perform on the given coil',
    dest = 'cmd'
)

plot = cmds.add_parser(
    name = 'plot',
    help = 'Perform a detailed field simulation and display or write to a file',
)
plot.add_argument(
    '-f',
    '--field-only',
    dest = 'field_only',
    action = 'store_true',
    help = 'Display only the B field simulation'
)
plot.add_argument(
    '-o',
    '--output',
    type = str,
    default = None,
    dest = 'output',
    help = 'Path to an output image or document file that report will be written to'
)
plot.add_argument(
    '-r',
    '--resolution',
    type = int,
    help = "Observer grid size for contour and line field graphs",
    default = 200
)

quick = cmds.add_parser(
    name = 'discrete',
    help = 'Quickly simulate lateral, diagonal, and central flux densities'
)

view = cmds.add_parser(
    name = 'view',
    help = 'View the given coil in 3D'
)

if __name__ == '__main__':
    args = parser.parse_args()
    
    coil = Coil(args.file)

    field = DiscreteFieldReport(coil)
    ALLOW_ERR = args.allowable_error / 1000
    for p, d in zip(field.sensor_pos_diagonal, field.diagonals):
        mag = magnitude(d)
        pos = p * 1000
        if np.abs(mag - field.diagonal_avg) >= ALLOW_ERR:
            print(f'WARNING: Diagonal field strength is not uniform: {mag * 1000:.4f} mT @ ({pos[0], pos[2]}) mm, mean is {field.diagonal_avg * 1000:.4f} mT')

    for p, t in zip(field.sensor_pos_lateral, field.laterals):
        mag = magnitude(t)
        pos = p * 1000
        if np.abs(mag - field.lateral_avg) >= ALLOW_ERR:
            print(f'WARNING: Lateral field strength is not uniform: {mag * 1000:.4f} mT @ ({pos[0], pos[2]}) mm, mean is {field.lateral_avg * 1000:.4f} mT')

    match args.cmd:
        case 'plot':
            report = FullFieldReport(coil, resolution = args.resolution)
            figure = plot_report(coil, report) if not args.field_only else plot_field_contour(coil, report)
            
            if args.output is not None:
                figure.set_size_inches(20, 10)
                plt.savefig(args.output, dpi = 100)
            else:
                plt.show()
        case 'discrete':
            

            

            print(
    f"""
    {coil.analysis_title()}
                 Magnitude      |    Centering Component

    Center:     {field.center_avg*1000:2.7f} mT    |
    Lateral:    {field.lateral_avg*1000:2.7f} mT    |        {field.centering_lateral_avg*1000:2.7f} mT
    Diagonal:   {field.diagonal_avg*1000:2.7f} mT    |        {field.centering_diagonal_avg*1000:2.7f} mT
    """
            )
        case 'view':
            coil.simulation_model().show()
