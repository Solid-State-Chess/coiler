import json

from constants import normalized
import numpy as np
from magpylib import current

from KicadModTree import Footprint, Line, Text, RingPad

# Coil deserialized from a JSON descriptor file
class Coil(object):
    def __init__(self, path):
        desc = json.load(open(path))
        self.layers = desc['layers']
        self.center = np.array(desc['center']) / 1000
        self.name = desc['name']
        self.spacing = desc['spacing'] / 1000
        self.trace_width = desc['trace_width'] / 1000
        self.base = desc['base']
        self.turns = desc['turns'] if self.base == 'inner' else desc['turns']
        self.current = desc['current']

        unreflect_verts = [np.array(array) / 1000 for array in desc['vertices']]
        
        self.base_verts = []
        if 'reflect' in desc and desc['reflect']:
            first_vert = unreflect_verts[0]
            last_vert = unreflect_verts[0]
            self.base_verts = [unreflect_verts[0]]
            for y in [1, -1]:
                for x in [1 * y, -1 * y]:
                    iter = range(0, len(unreflect_verts)) if x == y else range(len(unreflect_verts) - 1, -1, -1)
                    for i in iter:
                        vert = np.array([unreflect_verts[i][0] * x, unreflect_verts[i][1] * y])
                        if not np.array_equal(vert, last_vert) and not np.array_equal(vert, first_vert):
                            last_vert = vert
                            self.base_verts.append(vert)
        else:
            self.base_verts = unreflect_verts
        
        self.verts = []
        
        space_between = self.spacing + (self.trace_width / 2)
        for i in range(self.turns):
            space = space_between * i
            for j, vert in enumerate(self.base_verts):
                angle = np.arctan2(vert[1], vert[0])
                if angle < 0:
                    angle = 2 * np.pi + angle

                
                last_line = normalized(vert - self.base_verts[j - 1])
                next_line = normalized(self.base_verts[(j + 1) % len(self.base_verts)] - vert)

                last_normal = normalized(np.array([last_line[1], -last_line[0]]))
                next_normal = normalized(np.array([next_line[1], -next_line[0]]))

                vert_space = space + (space_between * angle / (2 * np.pi))
                vert_space *= 1 if self.base == 'inner' else -1

                normal_angle = np.arctan2(next_normal[1], next_normal[0]) - np.arctan2(last_normal[1], last_normal[0])
                extension = (vert_space * np.tan(normal_angle / 2)) * last_line


                self.verts.append(vert + (last_normal * vert_space + extension))

        self.verts = np.array(self.verts)
        self.size = np.array(
            max(self.verts[:, 0]) - min(self.verts[:, 0]),
            max(self.verts[:, 1]) - min(self.verts[:, 0])
        )

    # Get a magpylib simulation model for this coil 
    def simulation_model(self):
        sim_verts = []
        for i in range(self.layers):
            layer = [(v[0], i * -self.spacing / 1000, v[1]) for v in self.verts]
            sim_verts.extend(layer)
        return current.Polyline(position=(0,0,0), vertices=sim_verts, current=self.current)
    
    # Generate a KiCad footprint object that represents this coil
    def kicad_model(self):
        footprint = Footprint(self.name)
        footprint.setTags("coil")
        
        footprint.append(Text(
            type='reference',
            text='REF**',
            at=self.size + [1, 1],
            layer='F.SilkS'
        ))
        
        for layer in self.layers:
            for vert in self.verts:
                pass

        pass

    
    # Get a title for an analysis of this coil
    def analysis_title(self) -> str:
        return f'Field Analysis: {self.name} ({self.layers} Layer{"s" if self.layers != 1 else ""}, {self.turns} Turns) @ {self.current * 1000:.0f}mA'
