#import "@preview/cheq:0.3.0": checklist

#let data = json(sys.inputs.data)

#set page(
  margin: (x: 16mm, y: 14mm),
)

#set text(font: ("Linux Libertine", "Noto Sans", "DejaVu Sans"), size: 11pt)
#set par(leading: 1.25em, spacing: 0.4em)

#let ink = rgb(17, 24, 39)
#let muted = rgb(107, 114, 128)
#let line = rgb(229, 231, 235)

#show: checklist.with(fill: luma(96%), stroke: line, radius: 0.2em)

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
    - [ ] #item_body(item)
  ]
]
