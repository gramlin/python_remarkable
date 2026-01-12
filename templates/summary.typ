#let data = json(sys.inputs.data)

// --------------------
// Page + typography
// --------------------
#set page(
  margin: (x: 16mm, y: 14mm),
)

#set text(font: ("Linux Libertine", "Noto Sans", "DejaVu Sans"), size: 10.8pt)
#set par(leading: 1.2em, spacing: 0.45em)

// --------------------
// Style tokens (safe integers)
// --------------------
#let ink = rgb(18, 18, 18)
#let muted = rgb(107, 114, 128)
#let accent = rgb(37, 99, 235)
#let card = rgb(248, 250, 252)
#let line = rgb(229, 231, 235)
#let pill_bg = rgb(238, 242, 255)
#let pill_stroke = rgb(199, 210, 254)
#let pill_text = rgb(55, 48, 163)

#show heading: it => [
  #set text(weight: 700)
  #set align(left)
  #it
]

// --------------------
// Helpers
// --------------------
#let h1(title) = [
  #text(size: 22pt, weight: 800, fill: ink)[#title]
]

#let divider() = rect(height: 0.8pt, width: 100%, fill: line)

#let notes_lines(n) = [
  #for i in range(0, n) [
    #rect(height: 0.7pt, width: 100%, fill: line)
    #v(10pt)
  ]
]

#let pill(t) = box(
  inset: (x: 6pt, y: 2.5pt),
  radius: 999pt,
  fill: pill_bg,
  stroke: (paint: pill_stroke, thickness: 0.8pt),
)[
  #text(size: 9pt, fill: pill_text, weight: 650)[#t]
]

#let calendar_icon(name) = {
  if name == none {
    return ""
  }
  let lower = lower(name)
  if lower.contains("arbete") or lower.contains("work") {
    "[W]"
  } else if lower.contains("privat") or lower.contains("hem") or lower.contains("home") or lower.contains("personal") {
    "[P]"
  } else if lower.contains("semester") or lower.contains("ledigt") or lower.contains("vacation") or lower.contains("holiday") {
    "[S]"
  } else if lower.contains("träning") or lower.contains("gym") or lower.contains("sport") {
    "[G]"
  } else {
    "[·]"
  }
}

// --------------------
// Day card
// --------------------
#let day_card(day) = block(
  width: 100%,
  inset: 10pt,
  radius: 10pt,
  fill: card,
  stroke: (paint: line, thickness: 0.9pt),
)[
  // Header
  #stack(
    spacing: 6pt,
    [
      #align(left)[
        #text(size: 12.5pt, weight: 800, fill: ink)[#day.weekday]
        #h(6pt)
        #text(size: 9.5pt, fill: muted)[#day.date]
      ]
    ],
    [#rect(height: 2pt, width: 34pt, radius: 2pt, fill: accent)],
  )

  #v(8pt)

  // Content
  #if day.events.len() == 0 [
    #text(size: 10pt, fill: muted, style: "italic")[Inga kalenderposter]
    #v(6pt)
    #divider()
    #v(6pt)
    #notes_lines(8)
  ] else [
    #stack(spacing: 7pt)[
      #for event in day.events [
        #block(
          inset: (x: 8pt, y: 6pt),
          radius: 8pt,
          fill: rgb(255, 255, 255),
          stroke: (paint: line, thickness: 0.8pt),
        )[
          #stack(spacing: 4pt)[
            #align(left)[
              #pill(event.time)
              #if event.calendar != none [
                #h(5pt)
                #text(size: 10pt)[#calendar_icon(event.calendar)]
              ]
              #h(5pt)
              #text(weight: 650, fill: ink)[#event.summary]
            ]
            #if event.location != none [
              #text(size: 9.2pt, fill: muted)[📍 #event.location]
            ]
          ]
        ]
      ]
    ]

    #v(8pt)
    #divider()
    #v(6pt)
    #notes_lines(5)
  ]
]

// --------------------
// Document
// --------------------
#h1[Veckoplanering – Vecka #data.week_number]
#v(10pt)

// Focus box
#block(
  inset: 10pt,
  radius: 12pt,
  fill: rgb(255, 255, 255),
  stroke: (paint: line, thickness: 0.9pt),
)[
  #stack(spacing: 6pt)[
    #text(size: 10pt, weight: 750, fill: ink)[Komihåg ]
    #divider()
    #notes_lines(3)
  ]
]

#v(10pt)

// 2-column layout (Mon–Sun cards)
#columns(2, gutter: 10pt)[
  #for day in data.days [
    #day_card(day)
    #v(10pt)
  ]
]
