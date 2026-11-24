extensions [ gis ]

globals [
  boundary-dataset
  roads-dataset
  hubs-dataset
  pop-dataset
]

to setup
  clear-all
  set boundary-dataset gis:load-dataset "data/nedumangad_boundary.shp"
  set roads-dataset gis:load-dataset "data/nedumangad_roads.shp"
  set hubs-dataset gis:load-dataset "data/nedumangad_hubs.shp"
  set pop-dataset gis:load-dataset "data/nedumangad_population.asc"
  gis:set-world-envelope (gis:envelope-union-of
    (gis:envelope-of boundary-dataset)
    (gis:envelope-of roads-dataset)
    (gis:envelope-of pop-dataset))
  print "GIS Datasets Loaded and Envelope Set Successfully!"
  gis:set-drawing-color red
  gis:draw boundary-dataset 1
  print "Boundary drawn successfully!"
  reset-ticks
end
