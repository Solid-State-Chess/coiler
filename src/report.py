
# Report generated following a simulation of a coil

from magpylib import Sensor
import numpy as np

from coil import Coil
from constants import CHESS_SQUARE_SIZE, magnitude, centering_strength


SENSOR_POS_CENTER =     (0, 0)
SENSOR_POS_LATERAL =    (CHESS_SQUARE_SIZE / 2, 0)
SENSOR_POS_DIAGONAL =   (CHESS_SQUARE_SIZE / 2, CHESS_SQUARE_SIZE / 2)

DFLT_OBSERVER_HEIGHT = 3 / 1000

# Fast to generate report on field strength at the center, lateral, and diagonal positions
class DiscreteFieldReport(object):
    def __init__(
            self,
            coil: Coil,
            observer_height: float = DFLT_OBSERVER_HEIGHT,
        ) -> None:
        model = coil.simulation_model()
        self.observer_height = observer_height

        self.sensor_pos_lateral = []
        for v in (1, -1):
            self.sensor_pos_lateral.extend([
                np.array([SENSOR_POS_LATERAL[0] * v, self.observer_height, 0]),
                np.array([0, self.observer_height, SENSOR_POS_LATERAL[0] * v]),
            ])
        self.sensor_pos_center = np.array([SENSOR_POS_CENTER[0], self.observer_height, SENSOR_POS_CENTER[1]])
        self.sensor_pos_diagonal = [
            np.array([SENSOR_POS_DIAGONAL[0] * x, self.observer_height, SENSOR_POS_DIAGONAL[1] * y])
            for x in (1, -1) for y in (1, -1)
        ]

        self.laterals =  [Sensor(pos).getB(model) for pos in self.sensor_pos_lateral ]
        self.center =     Sensor(self.sensor_pos_center).getB(model)
        self.diagonals = [Sensor(pos).getB(model) for pos in self.sensor_pos_diagonal]
        
        self.lateral_avg =  sum(magnitude(v) for v in self.laterals)  / 4
        self.center_avg = magnitude(self.center)
        self.diagonal_avg = sum(magnitude(v) for v in self.diagonals) / 4

        center = np.array([0, self.observer_height, 0])
        self.centering_laterals = [centering_strength(pos, lat, center) for pos, lat in zip(self.sensor_pos_lateral, self.laterals)]
        self.centering_diagonals = [centering_strength(pos, dia, center) for pos, dia in zip(self.sensor_pos_diagonal, self.diagonals)]

        self.centering_lateral_avg = sum(self.centering_laterals) / 4
        self.centering_diagonal_avg = sum(self.centering_diagonals) / 4

        self._12mm = Sensor([12 / 1000, self.observer_height, 0]).getB(model)
        print(f'12mm is {magnitude(self._12mm) * 1000}mT      centering {centering_strength(np.array([12 / 1000, self.observer_height, 0]), self._12mm, [0,self.observer_height,0]) * 1000}mT')

class FullFieldReport(DiscreteFieldReport):
    # Run a simulation to view the magnetic field of a given coil design
    def __init__(
            self,
            coil: Coil,
            resolution: int = 100,
            bound: float = CHESS_SQUARE_SIZE * 2,
            observer_height: float = DFLT_OBSERVER_HEIGHT,
        ) -> None:
        super().__init__(coil, observer_height=observer_height)

        self._model = coil.simulation_model()
        self._model.move((coil.center[0], 0, coil.center[1]))
        self.bound = bound
        self.resolution = resolution
        self.grid_step = np.linspace(0, self.bound, self.resolution)
        self.top_observer_grid = np.array(
            [
                [
                    (x, self.observer_height, z)
                    for x in self.grid_step
                ]
                for z in self.grid_step
            ]
        )

        self.side_observer_grid = np.array(
            [
                [
                    (x, y - self.bound / 2, 0)
                    for x in self.grid_step
                ]
                for y in self.grid_step
            ]
        )

        self._B_top = None
        self._B_side = None
    
    @property
    def B_top(self):
        if self._B_top is None:
            self._B_top = self._model.getB(self.top_observer_grid)
        return self._B_top

    @property
    def B_side(self):
        if self._B_side is None:
            self._B_side = self._model.getB(self.side_observer_grid)
        return self._B_side

