#set page(margin: (x: 18mm, y: 16mm))
#set text(font: "Noto Sans", size: 11pt)

#let data = json(sys.inputs.data)

= Vecka #data.week_number

#for day in data.days [
  == #day.weekday (#day.date)
  #if day.events.len() == 0 [
    _Inga kalenderposter_
  ] else [
    #for event in day.events [
      - *#event.time* #event.summary
        #if event.location != none [
          [#event.location]
        ]
    ]
  ]
]
