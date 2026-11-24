;; ======================================================================
;; A GIS-Integrated Agent-Based Model for Simulating the Spatial Spread
;; of an Infectious Epidemic in Nedumangad Municipality, Kerala
;; ======================================================================

extensions [ gis ]

globals [
  ;; GIS datasets
  boundary-dataset
  wards-dataset
  roads-dataset
  hubs-dataset
  pop-dataset

  ;; Epidemic trackers
  count-S
  count-E
  count-I
  count-R
  cumulative-cases
  peak-infected
  peak-day
  effective-Rt
  recent-new-infections
  hospitalized-cases
  hospital-capacity

  ;; Time keeping
  simulation-day
  hour-of-day
  ticks-per-day
]

breed [ people person ]
breed [ hubs hub ]
breed [ quarantine-centers quarantine-center ]

people-own [
  health-status          ;; "S", "E", "I", "R"
  days-exposed           ;; hours/days in latent state
  days-infected          ;; hours/days in infectious state
  latent-duration        ;; threshold for E -> I
  infectious-duration    ;; threshold for I -> R
  home-patch-var         ;; home patch reference
  assigned-hub-var       ;; daytime hub destination
  current-target-patch   ;; target patch
  mobility-phase         ;; "home", "commuting-out", "at-hub", "commuting-in"
  dwell-hours-left       ;; hours remaining at hub
  is-isolated?           ;; in quarantine
  compliance-score       ;; 0.0 .. 1.0 adherence to restrictions
  is-mask-wearer?        ;; true/false
  ward-id                ;; 1 .. 39
  secondary-cases        ;; offspring cases for Rt calculation
]

hubs-own [
  hub-id
  hub-name
  hub-category           ;; "Healthcare", "Market", "Transit", "Education", "Religious", "Commercial", "Civic"
  hub-capacity
  hub-risk-score
  visitors-count
  infections-generated
  is-closed?
]

patches-own [
  pop-density            ;; from nedumangad_population.asc
  is-road?               ;; boolean
  road-hierarchy         ;; "primary", "secondary", "tertiary", "residential"
  ward-no                ;; 1..39
  cumulative-patch-cases ;; spatial infection tracker
]

;; ==========================================
;; SETUP PROCEDURES
;; ==========================================

to setup
  clear-all
  set ticks-per-day 24
  set simulation-day 1
  set hour-of-day 0
  set hospital-capacity 120
  set hospitalized-cases 0
  set peak-infected 0
  set peak-day 1
  set effective-Rt 1.50
  set recent-new-infections 0

  setup-gis
  setup-patches
  setup-hubs
  setup-population
  update-visual-display

  reset-ticks
  update-epidemic-metrics
  print (word "Nedumangad GIS Model Initialized: " count people " agents, " count hubs " activity hubs.")
end

to setup-gis
  ;; Load coordinate system and datasets
  gis:load-coordinate-system "data/nedumangad_boundary.prj"
  set boundary-dataset gis:load-dataset "data/nedumangad_boundary.shp"
  set wards-dataset gis:load-dataset "data/nedumangad_wards.shp"
  set roads-dataset gis:load-dataset "data/nedumangad_roads.shp"
  set hubs-dataset gis:load-dataset "data/nedumangad_hubs.shp"
  set pop-dataset gis:load-dataset "data/nedumangad_population.asc"

  ;; Set world envelope to encompass all datasets
  gis:set-world-envelope (gis:envelope-union-of
    (gis:envelope-of boundary-dataset)
    (gis:envelope-of roads-dataset)
    (gis:envelope-of pop-dataset))

  ;; Sample population density into patches
  gis:apply-raster pop-dataset pop-density
end

to setup-patches
  ask patches [
    set is-road? false
    set road-hierarchy "none"
    set cumulative-patch-cases 0
    if pop-density = false or pop-density < 0 [
      set pop-density 0.0
    ]
  ]

  ;; Discretize roads onto patches for routing
  gis:set-drawing-color 35  ;; light orange
  gis:draw roads-dataset 1.0
end

to setup-hubs
  ;; Create hub turtles directly from GIS features
  let hub-features gis:feature-list-of hubs-dataset
  let counter 1

  foreach hub-features [ feat ->
    let vertex-lists gis:vertex-lists-of feat
    if not empty? vertex-lists [
      let first-poly first vertex-lists
      if not empty? first-poly [
        let loc gis:location-of first first-poly
        if not empty? loc [
          let hx item 0 loc
          let hy item 1 loc
          if (hx >= min-pxcor and hx <= max-pxcor and hy >= min-pycor and hy <= max-pycor) [
            create-hubs 1 [
              set xcor hx
              set ycor hy
              set hub-id counter
              set hub-name gis:property-value feat "NAME"
              set hub-category gis:property-value feat "CATEGORY"
              set hub-capacity gis:property-value feat "CAPACITY"
              set hub-risk-score gis:property-value feat "RISK_SCORE"
              set visitors-count 0
              set infections-generated 0
              set is-closed? false

              ;; Style hub icon by category
              style-hub-icon self
              set counter counter + 1
            ]
          ]
        ]
      ]
    ]
  ]
end

to style-hub-icon [ h ]
  ask h [
    ifelse hub-category = "Healthcare" [
      set shape "plus"
      set color red
      set size 2.2
    ] [
      ifelse hub-category = "Market" [
        set shape "box"
        set color orange
        set size 2.0
      ] [
        ifelse hub-category = "Transit" [
          set shape "triangle"
          set color yellow
          set size 2.2
        ] [
          ifelse hub-category = "Education" [
            set shape "circle"
            set color sky
            set size 1.8
          ] [
            ifelse hub-category = "Religious" [
              set shape "star"
              set color violet
              set size 1.6
            ] [
              set shape "circle"
              set color cyan
              set size 1.4
            ]
          ]
        ]
      ]
    ]
  ]
end

to setup-population
  let eligible-patches patches with [ pop-density > 0.05 ]
  if not any? eligible-patches [ set eligible-patches patches ]

  let initial-count initial-population
  create-people initial-count [
    ;; Seed spatially according to population density raster
    let p [self] of one-of-weighted eligible-patches pop-density
    move-to p
    set home-patch-var p
    set current-target-patch p
    set mobility-phase "home"
    set dwell-hours-left 0

    ;; Health status
    set health-status "S"
    set days-exposed 0
    set days-infected 0
    set latent-duration (latent-period-days * 24 + random 24)
    set infectious-duration (infectious-period-days * 24 + random 48)
    set is-isolated? false
    set secondary-cases 0

    ;; Behavioral traits
    set compliance-score (0.50 + random-float 0.50)
    set is-mask-wearer? (random-float 100.0 < mask-coverage-pct)
    set ward-id (1 + random 39)

    ;; Assign primary activity hub (prefer closer hubs)
    let nearby-hubs hubs in-radius 30
    ifelse any? nearby-hubs [
      set assigned-hub-var one-of nearby-hubs
    ] [
      set assigned-hub-var one-of hubs
    ]

    ;; Visual appearance
    set shape "person"
    set color 55  ;; Green for Susceptible
    set size 1.2
  ]

  ;; Seed initial infections in town center
  let center-patch patch (round ((min-pxcor + max-pxcor) / 2)) (round ((min-pycor + max-pycor) / 2))
  let center-people [ people in-radius 25 ] of center-patch
  let seed-targets []
  ifelse count center-people >= initial-infected [
    set seed-targets n-of initial-infected center-people
  ] [
    set seed-targets n-of initial-infected people
  ]

  ask seed-targets [
    set health-status "I"
    set color red
    set days-infected (random 24)  ;; partly into infectious window
  ]

  set cumulative-cases initial-infected
end

;; Helper: Weighted random selection
to-report one-of-weighted [ agent-set weight-reporter ]
  let total-w sum [ pop-density ] of agent-set
  if total-w <= 0 [ report one-of agent-set ]
  let threshold random-float total-w
  let running 0.0
  let chosen nobody
  ask agent-set [
    if chosen = nobody [
      set running running + pop-density
      if running >= threshold [
        set chosen self
      ]
    ]
  ]
  ifelse chosen != nobody [ report chosen ] [ report one-of agent-set ]
end

;; ==========================================
;; MAIN SIMULATION CYCLE
;; ==========================================

to go
  ;; Check completion condition
  if count-I = 0 and count-E = 0 and ticks > 48 [
    print (word "Epidemic Extinguished at Day " simulation-day "! Final Attack Rate: " precision ((cumulative-cases / count people) * 100) 1 "%")
    stop
  ]

  ;; Update clocks
  set hour-of-day (ticks mod ticks-per-day)
  set simulation-day (floor (ticks / ticks-per-day) + 1)

  ;; Dynamic Policy Checks
  evaluate-interventions

  ;; Update Mobility & Movements
  simulate-daily-mobility

  ;; Disease Transmission
  simulate-transmission

  ;; Disease Progression (E -> I -> R)
  update-disease-progression

  ;; Active Testing & Isolation
  perform-testing-and-isolation

  ;; Update Metrics & Graphics
  update-epidemic-metrics
  if hour-of-day = 0 [
    update-visual-display
  ]

  tick
end

;; ==========================================
;; INTERVENTION & POLICY ENGINE
;; ==========================================

to evaluate-interventions
  ;; Auto-trigger lockdown if threshold exceeded
  if auto-lockdown-threshold > 0 and count-I >= auto-lockdown-threshold and not lockdown-active? [
    set lockdown-active? true
    print (word "ALERT: Auto-Lockdown Triggered on Day " simulation-day " due to " count-I " active cases!")
  ]

  ;; Update hub closure status
  ask hubs [
    ifelse markets-closed? and (hub-category = "Market" or hub-category = "Transit") [
      set is-closed? true
      set color 5  ;; Dark gray
    ] [
      set is-closed? false
      style-hub-icon self
    ]
  ]
end

;; ==========================================
;; MOBILITY ENGINE
;; ==========================================

to simulate-daily-mobility
  ;; Diurnal Schedule:
  ;; Hours 0-7: Night (all at home)
  ;; Hours 8-9: Morning Commute to Hub
  ;; Hours 10-16: Daytime Activity at Hub
  ;; Hours 17-18: Evening Commute back to Home
  ;; Hours 19-23: Evening at Home/Neighborhood

  ask people [
    ifelse is-isolated? [
      ;; Isolated agents stay at home or hospital
      set mobility-phase "home"
      move-to home-patch-var
    ] [
      ifelse lockdown-active? and (random-float 100.0 < (lockdown-compliance-pct * compliance-score)) [
        ;; Under lockdown, compliant citizens remain at home
        set mobility-phase "home"
        move-to home-patch-var
      ] [
        ;; Normal schedule
        ifelse hour-of-day >= 8 and hour-of-day <= 16 [
          ;; Heading to or at activity hub
          if assigned-hub-var != nobody and not [is-closed?] of assigned-hub-var [
            set mobility-phase "at-hub"
            move-to assigned-hub-var
            fd (random-float 0.8)
          ]
        ] [
          ;; Heading home or at home
          set mobility-phase "home"
          move-to home-patch-var
          if hour-of-day >= 19 and hour-of-day <= 22 [
            ;; Local evening neighborhood walk
            rt (random 360)
            fd (random-float 0.5)
          ]
        ]
      ]
    ]
  ]

  ;; Update hub occupant counters
  ask hubs [
    set visitors-count count people-here
  ]
end

;; ==========================================
;; TRANSMISSION ENGINE
;; ==========================================

to simulate-transmission
  set recent-new-infections 0

  ;; 1. Hub Transmission (Crowded Indoor Environments)
  ask hubs with [ not is-closed? and visitors-count > 1 ] [
    let infected-visitors people-here with [ health-status = "I" and not is-isolated? ]
    let susceptible-visitors people-here with [ health-status = "S" ]

    if any? infected-visitors and any? susceptible-visitors [
      let num-inf count infected-visitors
      let p-trans (1.0 - ((1.0 - (beta-hub-base * hub-risk-score * hub-crowding-factor / 2.0)) ^ num-inf))

      ask susceptible-visitors [
        let eff-p p-trans
        if is-mask-wearer? [ set eff-p eff-p * (1.0 - (mask-efficacy-pct / 100.0)) ]
        if random-float 1.0 < eff-p [
          set health-status "E"
          set days-exposed 0
          set color 45  ;; Yellow
          set recent-new-infections recent-new-infections + 1
          set cumulative-cases cumulative-cases + 1
          ask patch-here [ set cumulative-patch-cases cumulative-patch-cases + 1 ]
          ask one-of infected-visitors [
            set secondary-cases secondary-cases + 1
          ]
          ask myself [
            set infections-generated infections-generated + 1
          ]
        ]
      ]
    ]
  ]

  ;; 2. Street / Neighborhood Transmission
  let active-infectious people with [ health-status = "I" and not is-isolated? ]
  ask active-infectious [
    let nearby-susceptibles (people in-radius street-proximity-radius) with [ health-status = "S" ]
    if any? nearby-susceptibles [
      ask nearby-susceptibles [
        let p-street beta-street
        if [is-mask-wearer?] of myself [ set p-street p-street * (1.0 - (mask-efficacy-pct / 100.0)) ]
        if is-mask-wearer? [ set p-street p-street * (1.0 - (mask-efficacy-pct / 100.0)) ]
        if random-float 1.0 < p-street [
          set health-status "E"
          set days-exposed 0
          set color 45  ;; Yellow
          set recent-new-infections recent-new-infections + 1
          set cumulative-cases cumulative-cases + 1
          ask patch-here [ set cumulative-patch-cases cumulative-patch-cases + 1 ]
          ask myself [
            set secondary-cases secondary-cases + 1
          ]
        ]
      ]
    ]
  ]
end

;; ==========================================
;; DISEASE PROGRESSION & TESTING
;; ==========================================

to update-disease-progression
  ask people [
    if health-status = "E" [
      set days-exposed days-exposed + 1
      if days-exposed >= latent-duration [
        set health-status "I"
        set days-infected 0
        set color red
      ]
    ]

    if health-status = "I" [
      set days-infected days-infected + 1
      if days-infected >= infectious-duration [
        set health-status "R"
        set color sky  ;; Blue
        set is-isolated? false
      ]
    ]
  ]
end

to perform-testing-and-isolation
  if quarantine-active? [
    let unisolated-infected people with [ health-status = "I" and not is-isolated? ]
    ask unisolated-infected [
      ;; Daily detection probability scaled to hourly ticks
      let hourly-detect-prob (testing-quarantine-pct / 100.0) / 24.0
      if random-float 1.0 < hourly-detect-prob [
        set is-isolated? true
        set color 5  ;; Gray indicates isolated
        if hospitalized-cases < hospital-capacity [
          set hospitalized-cases hospitalized-cases + 1
        ]
      ]
    ]
  ]

  let active-hosp count people with [ health-status = "I" and is-isolated? ]
  set hospitalized-cases min (list active-hosp hospital-capacity)
end

;; ==========================================
;; METRICS & DISPLAY
;; ==========================================

to update-epidemic-metrics
  set count-S count people with [ health-status = "S" ]
  set count-E count people with [ health-status = "E" ]
  set count-I count people with [ health-status = "I" ]
  set count-R count people with [ health-status = "R" ]

  if count-I > peak-infected [
    set peak-infected count-I
    set peak-day simulation-day
  ]

  let recovered-sample people with [ health-status = "R" or (health-status = "I" and days-infected > (infectious-duration / 2)) ]
  ifelse any? recovered-sample [
    set effective-Rt precision (mean [ secondary-cases ] of recovered-sample) 2
  ] [
    set effective-Rt 1.85
  ]
end

to update-visual-display
  ifelse display-layer = "Population Density" [
    ask patches [
      ifelse pop-density > 0 [
        set pcolor scale-color brown pop-density 0.0 5.0
      ] [
        set pcolor black
      ]
    ]
    gis:set-drawing-color 37
    gis:draw roads-dataset 0.8
  ] [
    ifelse display-layer = "Infection Heatmap" [
      let max-c max [ cumulative-patch-cases ] of patches
      if max-c = 0 [ set max-c 1 ]
      ask patches [
        ifelse cumulative-patch-cases > 0 [
          set pcolor scale-color red cumulative-patch-cases 0 max-c
        ] [
          set pcolor 0
        ]
      ]
      gis:set-drawing-color white
      gis:draw boundary-dataset 1.5
    ] [
      ifelse display-layer = "Road Network" [
        ask patches [ set pcolor black ]
        gis:set-drawing-color yellow
        gis:draw roads-dataset 1.2
        gis:set-drawing-color red
        gis:draw boundary-dataset 2.0
      ] [
        ask patches [ set pcolor black ]
      ]
    ]
  ]
end

to enact-lockdown
  set lockdown-active? not lockdown-active?
  print (word "Lockdown status toggled to: " lockdown-active?)
end

to close-market-hubs
  set markets-closed? not markets-closed?
  print (word "Markets/Transit closure toggled to: " markets-closed?)
end
