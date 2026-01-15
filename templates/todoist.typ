#let data = json(sys.inputs.data)

#set page(
  margin: (x: 16mm, y: 14mm),
)

#set text(font: ("Linux Libertine", "Noto Sans", "DejaVu Sans"), size: 11pt)
#set par(leading: 1.25em, spacing: 0.4em)

#let ink = rgb(17, 24, 39)
#let muted = rgb(107, 114, 128)
#let line = rgb(229, 231, 235)

// Egen checkbox-funktion med stora rutor
#let checkbox(checked: false) = {
  let size = 1.5em
  let stroke-width = 1.5pt
  
  box(
    width: size,
    height: size,
    baseline: size / 2 - 0.6em,
    stroke: (paint: rgb(0, 0, 0), thickness: stroke-width),
    radius: 2pt,
    fill: rgb(255, 255, 255),
  )[
    #if checked [
      #place(center + horizon)[
        #text(size: 0.9em, weight: "bold")[✓]
      ]
    ]
  ]
}

#let header(title) = [
  #text(size: 22pt, weight: 800, fill: ink)[#title]
]

#let meta(label, value) = [
  #text(size: 9.5pt, fill: muted)[#label: #value]
]

#let item_body(item) = [
  #text(weight: 650, fill: ink)[#item.content]
  #if item.due != none [
    #h(6pt)
    #text(size: 9pt, fill: muted)[(#item.due)]
  ]
  #if item.description != none and item.description != "" [
    #v(2pt)
    #set par(leading: 0.5em)
    #text(size: 9pt, fill: muted)[#item.description]
  ]
]

#header(data.project_name)
#v(6pt)
#meta("Senast uppdaterad", data.generated_at)
#v(8pt)
#rect(height: 0.8pt, width: 100%, fill: line)
#v(8pt)

#if data.items.len() == 0 [
  #text(fill: muted, style: "italic")[Inga uppgifter i listan.]
] else [
  #for item in data.items [
    #block(spacing: 0.8em)[
      #grid(
        columns: (auto, 1fr),
        column-gutter: 0.7em,
        row-gutter: 0em,
        [#checkbox()],
        [#item_body(item)]
      )
    ]
  ]
]
