import json
from itertools import pairwise

from KicadModTree.Vector import Vector2D

from constants import magnitude, normalized

import numpy as np
from magpylib import Collection, current

from KicadModTree import Footprint, KicadFileHandler, Line, Pad, Text, RingPad

# Coil deserialized from a JSON descriptor file
class Coil(object):
    def __init__(self, desc):
        self.layers = desc['layers']
        self.center = np.array(desc['center']) / 1000
        self.name = desc['name']
        self.spacing = desc['spacing'] / 1000
        self.trace_width = desc['trace_width'] / 1000
        self.base = desc['base']
        self.turns = desc['turns'] if self.base == 'inner' else desc['turns']
        self.trace_height = desc['trace_height'] / 1000 if 'trace_height' in desc else 34.1 / 1_000_000

        if 'current' in desc:
            self.current: float = desc['current']

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
        
        def angle_between(v1, v2):
            angle = np.arctan2(v1[1], v1[0]) - np.arctan2(v2[1], v2[0])
            if angle < 0:
                angle = 2 * np.pi + angle
            return angle

        space_between = self.spacing + self.trace_width
        extension_vectors = []
        to_remove = []
        for i, vert in enumerate(self.base_verts):
            last_line = normalized(vert - self.base_verts[i - 1])
            next_line = normalized(self.base_verts[(i + 1) % len(self.base_verts)] - vert)

            last_normal = normalized(np.array([-last_line[1], last_line[0]]))
            next_normal = normalized(np.array([-next_line[1], next_line[0]]))

            normal_angle = angle_between(last_normal, next_normal)
            if normal_angle == 0:
                to_remove.append(i)
                continue

            extension = np.tan(normal_angle / 2) * last_line

            extension_vectors.append(extension + last_normal)
        
        removed = 0
        for i in to_remove:
            del self.base_verts[i + removed]
            removed -= 1

        for i in range(self.turns):
            space = space_between * i
            for vert, ext in zip(self.base_verts, extension_vectors):
                angle = np.arctan2(vert[1], vert[0])
                if angle < 0:
                    angle = 2 * np.pi + angle

                vert_space = space + (space_between * angle / (2 * np.pi))
                vert_space *= -1 if self.base == 'inner' else 1
                
                self.verts.append(vert + vert_space * ext)


        self.verts = np.array(self.verts)
        self.size = np.array(
            max(self.verts[:, 0]) - min(self.verts[:, 0]),
            max(self.verts[:, 1]) - min(self.verts[:, 0])
        )

        self.length = sum(magnitude(v2 - v1) for v1, v2 in pairwise(self.verts)) * self.layers
        
        p_cu = 1.724e-8
        self.resistance = p_cu * (self.length / (self.trace_width * self.trace_height))

        if 'current' not in desc:
            self.current: float = np.sqrt(desc['power'] / self.resistance)

    # Get a magpylib simulation model for this coil 
    def simulation_model(self):
        sim_verts = []
        for i in range(self.layers):
            layer = [(v[0], i * -self.spacing, v[1]) for v in self.verts]
            sim_verts.extend(layer)
        return current.Polyline(position=(0,0,0), vertices=sim_verts, current=self.current)
    
    # Generate a KiCad footprint object that represents this coil
    def kicad_model(self, layer: str) -> Footprint:
        footprint = Footprint(self.name)
        footprint.setTags("coil")
        
        footprint.append(Text(
            type='reference',
            text='REF**',
            at=Vector2D(tuple(self.size + [1, 1])),
            layer='F.SilkS'
        ))
        
        footprint.append(Pad(
            number = 1,
            type = Pad.TYPE_CONNECT,
            shape = Pad.SHAPE_RECT,
            size=Vector2D(1,1),
            at = Vector2D(tuple(self.verts[0])),
            layers=[layer]
        ))

        for last_vert, next_vert in pairwise(self.verts):
            footprint.append(Line(
                start=Vector2D(tuple(last_vert * 1000)),
                end  =Vector2D(tuple(next_vert * 1000)),
                layer=layer,
                width=self.trace_width * 1000,
            ))

        footprint.append(Pad(
            number = 2,
            type = Pad.TYPE_CONNECT,
            shape = Pad.SHAPE_RECT,
            size=[1,1],
            at = Vector2D(tuple(self.verts[len(self.verts) - 1])),
            layers=[layer]
        ))

        return footprint

    
    # Get a title for an analysis of this coil
    def analysis_title(self) -> str:
        return f'Field Analysis: {self.name} ({self.layers} Layer{"s" if self.layers != 1 else ""}, {self.turns} Turns) @ {self.current * 1000:.0f}mA ({self.resistance:.2f}Ω)'
