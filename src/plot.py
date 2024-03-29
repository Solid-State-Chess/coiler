from typing import Optional, cast
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
import numpy as np

from coil import Coil
from constants import CHESS_SQUARE_SIZE, magnitude, centering_strength
from report import FullFieldReport

# Write a field centering strength contour map of the given coil to the given axis
def plot_field_contour_on_axis(topax: Axes, coil: Coil, report: FullFieldReport, cutoff: Optional[float] = None) -> None:
    topax.set_title("Centering Magnetic Flux Density")
    topax.set_axis_off()
    topax.set_aspect('equal')

    verts = np.array(coil.verts) + coil.center
    topax.plot(
        verts[:, 0],
        verts[:, 1],
        color=(0, 0, 0, 0.1),
        linewidth=0.1,
    )
    
    def map_field_strength(pos, field):
        strength = centering_strength(
                pos,
                field,
                np.array([
                    coil.center[0],
                    report.observer_height,
                    coil.center[1]
                ])
            )
        
        if cutoff is None or strength >= cutoff:
            return strength
        else:
            return 1 / 1_000_000

    field = [
        [
            map_field_strength(pos, field)
            for pos, field in zip(*row)
        ]
        for row in zip(report.top_observer_grid, report.B_top)
    ]

    topax.contourf(
        report.top_observer_grid[:, :, 0],
        report.top_observer_grid[:, :, 2],
        np.log(np.abs(field)) * np.sign(field),
        levels=50,
        cmap = "inferno",
        zorder = 1
    )
    
    if cutoff is None:
        topax.streamplot(
            report.top_observer_grid[:, :, 0],
            report.top_observer_grid[:, :, 2],
            report.B_top[:, :, 0],
            report.B_top[:, :, 2],
            density = 1,
            color = np.log(field),
            linewidth = 2,
            cmap = 'plasma',
            zorder = 10
        )

    board_square = np.array([
        (0,                            0),
        (CHESS_SQUARE_SIZE,               0),
        (CHESS_SQUARE_SIZE,  CHESS_SQUARE_SIZE),
        (0,               CHESS_SQUARE_SIZE),
        (0,                            0)
    ])

    a1 = board_square
    a2 = board_square + (0,              CHESS_SQUARE_SIZE)
    b1 = board_square + (CHESS_SQUARE_SIZE,              0)
    b2 = board_square + (CHESS_SQUARE_SIZE, CHESS_SQUARE_SIZE)

    for sq in [a1, a2, b1, b2]:
        topax.plot(sq[:, 0], sq[:, 1], "w-", zorder=1000)

# Create a standalone figure that only displays a contour map of centering strength for the given coil
def plot_field_contour(coil: Coil, report: FullFieldReport) -> Figure:
    figure = plt.figure(layout='constrained')
    figure.suptitle(coil.analysis_title())

    plot_field_contour_on_axis(cast(Axes, figure.subplots()), coil, report)
    return figure

# Create a full-field report on the given coil and plot its B field with matplotlib
def plot_report(coil: Coil, report: FullFieldReport) -> Figure:
    figure = plt.figure(layout='constrained')
    figure.suptitle(coil.analysis_title())
    [left, right] = figure.subfigures(1, 2)
    plot_field_contour_on_axis(left.subplots(), coil, report)

    [labels, sideax] = right.subplots(2, 1)
    labels: Axes = labels

    categories = ('Center', 'Lateral', 'Diagonal')
    x = np.arange(3)

    magnitudes = [
        field * 1000 for field in (report.center_avg, report.lateral_avg, report.diagonal_avg)
    ]

    centering_strengths = [
        0,
        report.centering_lateral_avg * 1000,
        report.centering_diagonal_avg * 1000
    ]

    magnitude_bars = labels.bar(
        x,
        magnitudes,
        width=0.25,
        label='Total',
    )
    labels.bar_label(magnitude_bars, label_type='edge', fmt='{:.4f}')

    centering_bars = labels.bar(
        x + 0.25,
        centering_strengths,
        width=0.25,
        label='Centering Component',
    )
    labels.bar_label(centering_bars, label_type='edge', fmt='{:.4f}')
    labels.legend()
    labels.set_xticks(x + 0.25, categories)

    labels.set_title('Discrete Flux Density')
    labels.set_ylabel('Flux Density (mT)')
    
    sideax: Axes = sideax
    sideax.set_title('Side View Streamplot')
    bound = report.bound * 1000
    sideax.set_xlim(0, bound)
    sideax.set_ylim(-bound / 2, bound / 2)
    sideax.set_facecolor('black')
    sideax.set_aspect(0.5)
    sideax.streamplot(
        report.side_observer_grid[:, :, 0] * 1000,
        report.side_observer_grid[:, :, 1] * 1000,
        report.B_side[:, :, 0],
        report.B_side[:, :, 1],
        density = 1,
        cmap = 'inferno',
        color = np.log([[magnitude(j) for j in i] for i in report.B_side]),
    )

    sideax.plot([0,bound], [0,0], 'w-')
    sideax.plot([bound/2,bound/2], [bound/2,-bound/2], 'w--')

    sideax.set_xlabel('Length (mm)')

    
    return figure
