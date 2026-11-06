"""Original, deterministic interdisciplinary design and composition sketches.

Outputs interoperable SVG (vector art) and MusicXML (new algorithmically
constructed notation). No pre-existing melodies, recordings, lyrics, images
or proprietary creative prompts are copied. No audio playback is provided.
These are sketches, not engineering-certified designs or creative AGI.
"""
from html import escape
from math import cos, sin, tau
from pathlib import Path
from random import Random
import json

DOMAIN_PAIRS=(
    ("photonics","architecture","light-guided facade patterns"),
    ("robotics","ballet","expressive high-precision motion sketches"),
    ("biology","materials","nature-derived lattices with measurable strengths"),
    ("astronomy","music","celestial measurements translated to original sonic patterns"),
    ("agriculture","design","low-cost modular agricultural workspaces"),
    ("physics","film","scientifically annotated visual narratives"),
    ("chemistry","fashion","material textures with measured safety limits"),
    ("aerospace","sculpture","lightweight structural studies"),
    ("ecology","games","educational simulations of resource cycles"),
    ("mathematics","art","transformations expressed through geometric composition"),
)
COLOR_PALETTE=("#2a3d66","#3c779c","#46a4a1","#d5b96b","#e38e63")


def creative_seed(topic="interdisciplinary research",seed=1701):
    if not isinstance(topic,str) or not 2<=len(topic.strip())<=100:
        raise ValueError("Creative topic must be 2..100 characters")
    if not isinstance(seed,int) or not 0<=seed<=999999:
        raise ValueError("Seed must be 0..999999")
    return topic.strip(), Random(seed)


def svg_study(topic,seed=1701):
    name,rng=creative_seed(topic,seed)
    elements=[
        '<svg xmlns="http://www.w3.org/2000/svg" width="768" height="768" viewBox="0 0 768 768" role="img">',
        "<title>"+escape("Plenum original geometry: "+name)+"</title>",
        '<rect width="768" height="768" fill="#101c2f"/>',
    ]
    # A deliberately original seeded parametric geometry sketch.
    phase=rng.random()*tau
    for ring in range(12):
        radius=28+ring*22
        color=COLOR_PALETTE[ring%len(COLOR_PALETTE)]
        opacity=f"{0.30+0.05*(ring%6):.2f}"
        points=[]
        sides=5+(ring%7)
        for k in range(sides):
            theta=phase+k*tau/sides+(ring*.11)
            points.append(f"{384+radius*cos(theta):.2f},{384+radius*sin(theta):.2f}")
        elements.append(
            '<polygon points="'+" ".join(points)+'" fill="none" stroke="'+color+
            '" stroke-width="2" opacity="'+opacity+'"/>')
    for _ in range(11):
        x,y=rng.randrange(85,683),rng.randrange(85,683)
        r=rng.randrange(3,10)
        elements.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#d5b96b" opacity="0.7"/>')
    elements.append('</svg>')
    return "\n".join(elements)+"\n"


def musicxml_study(topic,seed=1701):
    name,rng=creative_seed(topic,seed)
    pitches=(("C",4),("D",4),("E",4),("G",4),("A",4),
             ("C",5),("D",5),("E",5))
    parts=[
        '<?xml version="1.0" encoding="utf-8"?>',
        '<!DOCTYPE score-partwise  PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">',
        '<score-partwise version="4.0">',
        '<work><work-title>'+escape("Original study: "+name)+'</work-title></work>',
        '<movement-title>'+escape("Original study: "+name)+'</movement-title>',
        '<identification><creator type="composer">Plenum procedural composition</creator></identification>',
        '<defaults><scaling><millimeters>7</millimeters><tenths>40</tenths></scaling></defaults>',
        '<part-list><score-part id="P1"><part-name>Keyboard</part-name>',
        '<part-abbreviation>Kbd</part-abbreviation><score-instrument id="I1"><instrument-name>Piano</instrument-name></score-instrument></score-part></part-list>',
        '<part id="P1">',
    ]
    last=2
    for measure in range(1,9):
        parts.append(f'<measure implicit="no" number="{measure}">')
        if measure==1:
            parts.append('<attributes><divisions>1</divisions><key><fifths>0</fifths></key><time><beats>4</beats><beat-type>4</beat-type></time><clef><sign>G</sign><line>2</line></clef></attributes>')
        for note_index in range(4):
            last=max(0,min(len(pitches)-1,last+rng.choice((-2,-1,0,1,2))))
            step,octave=pitches[last]
            parts.append('<note><pitch><step>'+step+'</step><octave>'+
                         str(octave)+'</octave></pitch><duration>1</duration><type>quarter</type></note>')
        parts.append('</measure>')
    parts.extend(['</part>','</score-partwise>'])
    return "\n".join(parts)+"\n"


def idea_studies(topic,seed=1701):
    name,rng=creative_seed(topic,seed)
    chosen=rng.sample(DOMAIN_PAIRS,5)
    return {
        "schema":"plenum-original-creative-ideas-v1",
        "theme":name,"seed":seed,
        "concepts":[{
            "discipline_a":a,"discipline_b":b,
            "speculative_idea":description,
            "design_task":f"Sketch an original {name} concept through {a} and {b}: {description}.",
            "research_next_step":"Define a measurable hypothesis and verify feasibility independently.",
            "new_scientific_breakthrough_claimed":False,
        } for a,b,description in chosen],
        "originality_or_patentability_ascertained":False,
        "copyright_clearance_for_third_party_material":False,
        "AI_creative_reasoning_used":False,
    }


def write_studies(topic,seed,outdir):
    name,_=creative_seed(topic,seed)
    target=Path(outdir)
    target.mkdir(parents=True,exist_ok=True)
    files={
        "artwork_svg":target/"geometric_study.svg",
        "score_musicxml":target/"original_score.musicxml",
        "ideas_json":target/"interdisciplinary_ideas.json",
    }
    if any(path.exists() or path.is_symlink() for path in files.values()):
        raise FileExistsError("Existing creative output cannot be overwritten")
    files["artwork_svg"].write_text(svg_study(name,seed),encoding="utf-8")
    files["score_musicxml"].write_text(musicxml_study(name,seed),encoding="utf-8")
    files["ideas_json"].write_text(json.dumps(idea_studies(name,seed),indent=2)+"\n",encoding="utf-8")
    return {
        "outputs":{k:str(v) for k,v in files.items()},
        "created_from_algorithm":True,
        "copied_copyrighted_music_or_art":False,
        "novelty_exclusivity_certified":False,
        "audio_playback_or_rendering_performed":False,
        "engineering_validation_performed":False,
        "formats":["SVG vector design","MusicXML notation","JSON original ideas"],
    }
