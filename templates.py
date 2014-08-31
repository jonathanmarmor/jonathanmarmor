main = """\\version "2.12.3"

#(ly:set-option 'point-and-click #f) % switch off hyperlinks from noteheads to lilypond source files
#(set-global-staff-size {staff_size}) % 20 is default


%  Function to allow manually entered barlines
increaseBarNumber = \\applyContext
#(lambda (x)
  (let ((measurepos (ly:context-property x 'measurePosition)))
   ; Only increase bar number if not at start of measure.
   ; This way we ensure that you won't increase bar number twice
   ; if two parallel voices call increaseBarNumber simultanously:
   (if (< 0 (ly:moment-main-numerator measurepos)) ; ugh. ignore grace part
    (begin
     (ly:context-set-property!
      (ly:context-property-where-defined x 'internalBarNumber)
      'internalBarNumber
      (1+ (ly:context-property x 'internalBarNumber)))
     (ly:context-set-property!
      (ly:context-property-where-defined x 'currentBarNumber)
      'currentBarNumber
      (1+ (ly:context-property x 'currentBarNumber)))
     ; set main part of measurepos to zero, leave grace part as it is:
     (ly:context-set-property!
      (ly:context-property-where-defined x 'measurePosition)
      'measurePosition
      (ly:make-moment 0 1
       (ly:moment-grace-numerator measurepos)
       (ly:moment-grace-denominator measurepos)))))))

%  Named Increasing BAR
nibar = #(define-music-function (parser location x) (string?)
#{{
  \\bar $x
  \\increaseBarNumber
#}})

%  Increasing BAR
ibar = \\nibar "|"


\\paper {{
%	annotate-spacing = ##t
    #(set-paper-size "letter")
%	#(define top-margin (* 0.6 in))
%	#(define bottom-margin (* 0.4 in))
%	#(define left-margin (* 0.8 in))
%	#(define line-width (* 7.4 in))
%	page-top-space = 0.0\\in
%	foot-separation = 0.25\\in
%	head-separation = 0.0\\in
%	after-title-space = 0.0\\in
%	between-title-space = 0.0\\in
%    between-system-padding = 4\\mm % Default is 4mm
	ragged-bottom = ##f
	ragged-last-bottom = ##f
	first-page-number = 1
	print-first-page-number = ##t

	bookTitleMarkup = \\markup {{
		\\column {{
			\\fill-line {{
				\\line {{
					\\override #'(font-size . 6)
					{{ \\fromproperty #'header:maintitle }}
				}}
			}}
			\\fill-line {{
				\\line {{ \\null }}
				\\line {{ \\null }}
				\\line {{
					{{ \\fromproperty #'header:thecomposer }}
				}}
			}}
		}}
	}}
	scoreTitleMarkup = \\markup {{
		\\column {{
			\\fill-line {{
				\\line {{
					\\override #'(font-size . 4)
					{{ \\fromproperty #'header:movementtitle }}
				}}
			}}
			\\line {{ \\null }}
		}}
	}}
	oddHeaderMarkup = \\markup {{
		\\on-the-fly #not-first-page {{
			\\column {{
				\\fill-line {{
					{{
						\\override #'(font-size . 1)
						{{ " " }}
					}}
					{{
						\\override #'(font-size . 2)
						{{ \\fromproperty #'header:instrumentname }}
					}}
					{{
						\\override #'(font-size . 1)
						{{ \\on-the-fly #print-page-number-check-first \\fromproperty #'page:page-number-string }}
					}}
				}}
				\\line {{ \\null }}
			}}
		}}
		\\column {{
			\\fill-line {{
				\\override #'(font-size . 2)
				{{ \\fromproperty #'header:instrumentname }}
			}}
			\\line {{ \\null }}
		}}
	}}
	evenHeaderMarkup = \\markup {{
		\\on-the-fly #not-first-page {{
			\\column {{
				\\fill-line {{
					{{
						\\override #'(font-size . 1)
						{{ \\on-the-fly #print-page-number-check-first \\fromproperty #'page:page-number-string }}
					}}
					{{
						\\override #'(font-size . 2)
						{{ \\fromproperty #'header:instrumentname }}
					}}
					{{
						\\override #'(font-size . 1)
						{{ " " }}
					}}
				}}
				\\line {{ \\null }}
			}}
		}}
		\\column {{
			\\fill-line {{
				\\override #'(font-size . 2)
				{{ \\fromproperty #'header:instrumentname }}
			}}
			\\line {{ \\null }}
		}}
	}}
}}

\\book {{
	\\header {{
		maintitle = "{title}"
		thecomposer = "{composer}"
		tagline = ""
	}}
"""

main_end = """}}"""


movement = """
	\\bookpart {{
		\\header {{
			movementtitle = "{title}"
			instrumentname = "{name}"
		}}
		\\score {{
			<<
				\\set Score.autoBeaming = ##t
				\\accidentalStyle Score.neo-modern
				\\override Score.Stem #'stemlet-length = #0.75
				\\override Score.PaperColumn #'keep-inside-line = ##t
"""

movement_end = """
			>>
			\\layout {{ }}
{midi}           \\midi {{ }}
		}}
	}}
"""

instrument = """
			\\new Staff {{
				\\override Staff.TimeSignature #'stencil = ##f  %  Hides time signature
				\\set Staff.instrumentName = \\markup {{ "{name}" }}
				\\set Staff.shortInstrumentName = \\markup {{ \\hcenter-in #5 "{short_name}" }}
				\\set Staff.midiInstrument = #"{midi_name}"
				\\set Staff.extraNatural = ##f
				\\clef {clef}
				\\override TextScript #'staff-padding = #2.0
				\\override Staff.VerticalAxisGroup #'minimum-Y-extent = #'(-5 . 5.5)  % sets minimum space between staves within a system
				\\transpose c {transpose_from_middle_c}
				\\tempo {tempo_duration} = {tempo_bpm}"""

instrument_end = """
				\\include "{path_to_music_file}"
			}}"""


rehearsal = """\\mark \\markup {{ \\override #\'(font-name . "Minion Semibold") \\override #\'(thickness . 0.01) \\override #'(box-padding . 0.4) \\box {{ "{rehearsal_text}" }} }}\n"""

bar = '\\nibar "{bar_type}" %  ----------  {bar_number}\n'
time_signature = '\\time {numerator}/{denominator}\n'
text_spanner_init = """\\override TextSpanner #\'staff-padding = #3.0 \\override TextSpanner #\'(bound-details left text) = \\markup {{ \\override #\'(font-name . "Minion Italic") {{ "{text_spanner_text}" }} }}\n"""

tempo_instruction_init = """\\override TextScript #\'staff-padding = #3.0\n"""
grace_notes_init = '\\grace {\n'
grace_notes_close = '}\n'
tie = '~'
beam_start = '['
beam_stop = ']'
slur_start = '('
slur_stop = ')'
articulation = '-{articulation}'
dynamic = ' \\{dynamic}'
fermata = ' \\fermata'
text_above = ' ^"{text}"'
text_below = ' _"{text}"'
breathe = ' \\breathe'
start_text_spanner = ' \\startTextSpan'
stop_text_spanner = ' \\stopTextSpan'
tempo_instruction = """ ^\\markup {{ \\override #\'(font-name . "Minion Italic") {{ "{tempo_instruction_text}" }} }}"""

note = """{rehearsal}{bar}{time_signature}{text_spanner_init}{tempo_instruction_init}{grace_notes_init}{grace_notes}{grace_notes_close}{pitches}{duration}{tie}{beam}{slur}{articulations}{dynamic}{fermata}{text_above}{text_below}{breathe}{start_text_spanner}{stop_text_spanner}{tempo_instruction}\n"""

grace_note = """{text_spanner_init_tab}{text_spanner_init}{tempo_instruction_init_tab}{tempo_instruction_init}{pitches_tab}{pitches}{duration}{tie}{beam}{slur}{articulations}{dynamic}{text_above}{text_below}{start_text_spanner}{stop_text_spanner}{tempo_instruction}\n"""

page_start = '\\new Voice {\n\n\\cadenzaOn %  Disables automatic insertion of barlines.\n'
page_end = '\n\\bar "|."\n}'
