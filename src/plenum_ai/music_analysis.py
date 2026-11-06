"""music21 analysis of Plenum's own algorithmically generated MusicXML.

No external songs, recordings or publisher scores are downloaded. Analysis
describes this tiny procedural score only: it is not proof of musical quality,
creative novelty, human-level art or trained compositional intelligence.
"""
from collections import Counter
from math import isfinite
from .creative_studio import musicxml_study


def analyze_original_music(topic, seed=1701):
    from music21 import converter, note, stream
    xml=musicxml_study(topic,seed)
    score=converter.parseData(xml,format="musicxml")
    if not score.parts:
        raise ValueError("No valid original musical part found")
    notes=list(score.parts[0].recurse().getElementsByClass(note.Note))
    measures=list(score.parts[0].getElementsByClass(stream.Measure))
    if len(notes)!=32 or len(measures)!=8:
        raise ValueError("Unexpected procedural composition structure")
    midi=[int(n.pitch.midi) for n in notes]
    durations=[float(n.duration.quarterLength) for n in notes]
    if not all(isfinite(x) and x>0 for x in durations):
        raise ValueError("Invalid durations")
    step_sizes=[abs(b-a) for a,b in zip(midi[:-1],midi[1:])]
    histogram=Counter(n.pitch.pitchClass for n in notes)
    return {
        "schema":"plenum-original-music21-study-v1",
        "music_theory_library":"music21",
        "topic":topic,
        "original_seed":seed,
        "measures":len(measures),
        "note_count":len(notes),
        "total_quarter_notes":sum(durations),
        "distinct_pitch_classes":len(histogram),
        "pitch_class_histogram":{str(k):v for k,v in sorted(histogram.items())},
        "range_semitones":max(midi)-min(midi),
        "mean_abs_melodic_interval_semitones":sum(step_sizes)/len(step_sizes),
        "original_procedural_score":True,
        "copyrighted_source_score_imported":False,
        "audio_generated_or_played":False,
        "artistic_quality_or_originality_verified":False,
        "AI_composer_trained":False,
        "result_is_independent_music_analysis":True,
        "limitations":[
            "Analyzes only an eight-measure procedurally generated score.",
            "Note statistics cannot measure emotional quality, novelty or compositional craft.",
            "No recording synthesis or reproduction of an existing work.",
        ],
    }
