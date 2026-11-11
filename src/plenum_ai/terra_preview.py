"""A wholly original and unpaid 15-second Plenum Terra concept rough cut.

Three deterministic illustrated moving sequences are rendered by Pillow and
system FFmpeg, then assembled with an existing rights-reviewed sample of
Kokoro narration by the standard Plenum film factory. It is NOT real
pasture footage, trial evidence, a licensed stock movie, or an approved ad.
No video models, API credits, paid inference or voice impersonation are used.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SCENE_SECONDS = 800, 450, 12, 5
MODEL_CARD = "https://huggingface.co/hexgrad/Kokoro-82M"
SOURCE = ("https://github.com/chadkhalil21-svg/"
          "Plenum-Scientific-Intelligence/blob/main/src/plenum_ai/terra_preview.py")


def font(size: int):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def background(scene: int):
    image = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(image)
    pairs = (
        ((18, 42, 53), (82, 135, 121)),
        ((10, 26, 45), (26, 87, 89)),
        ((12, 38, 47), (36, 87, 71)),
    )
    top, bottom = pairs[scene]
    for y in range(H):
        f = y / (H - 1)
        draw.line((0, y, W, y), fill=tuple(
            int(top[j] * (1 - f) + bottom[j] * f) for j in range(3)
        ))
    return image


def cow(draw, x, y, scale, shade):
    """Hand-drawn illustrative animal silhouette; no documentary claim."""
    draw.ellipse((x, y, x + 145*scale, y + 65*scale), fill=shade)
    draw.ellipse((x+122*scale, y-10*scale, x+172*scale, y+42*scale), fill=shade)
    for xx in (26, 53, 105, 128):
        draw.rounded_rectangle((x+xx*scale, y+43*scale,
                                x+(xx+12)*scale, y+107*scale),
                               radius=3, fill=shade)
    draw.polygon(((x+165*scale,y-4*scale),
                  (x+185*scale,y-13*scale),
                  (x+178*scale,y+5*scale)), fill=shade)
    draw.line((x+7*scale,y+13*scale,x-17*scale,y+53*scale),
              fill=shade, width=max(2,int(scale*6)))


def draw_frame(scene, frame, base):
    t = frame / FPS
    image = base.copy()
    draw = ImageDraw.Draw(image)
    draw.text((36,26), "PLENUM  /  TERRA", font=font(18), fill=(219,235,229))
    draw.line((36,58,764,58), fill=(138,170,160),width=1)
    draw.text((36,78), "CONCEPT VISUALIZATION  |  NOT FIELD RESULTS",
              font=font(14),fill=(236,210,137))
    if scene == 0:
        draw.ellipse((-130,215,420,490), fill=(34,92,75))
        draw.ellipse((300,225,920,500),fill=(26,75,61))
        for k in range(65):
            x=k*13
            height=9+(k*7)%22
            sway=3*math.sin(t*1.5+k*.67)
            draw.line((x,445,x+sway,445-height),fill=(97,144,89),width=2)
        cow(draw,55+t*11,275,1.08,(15,47,42))
        cow(draw,480-t*5,303,.67,(13,51,42))
        draw.ellipse((615-t*13,119,692-t*13,153),fill=(180,209,196))
        draw.ellipse((657-t*13,110,727-t*13,151),fill=(180,209,196))
        draw.text((395,218),"A QUIET CHALLENGE",font=font(29),fill=(239,244,231))
    elif scene == 1:
        for idx in range(11):
            phase=(idx*41+t*40)%530
            x=65+(idx*63)%700+14*math.sin(t*1.4+idx)
            y=490-phase
            radius=8+idx%5
            draw.ellipse((x-radius,y-radius,x+radius,y+radius),
                         fill=(56,141,128),outline=(128,215,184),width=2)
        cx,cy=440,255
        draw.line((cx-70,cy,cx+70,cy),fill=(225,207,149),width=4)
        draw.line((cx,cy-72,cx,cy+72),fill=(225,207,149),width=4)
        draw.ellipse((cx-27,cy-27,cx+27,cy+27),fill=(200,190,136))
        for x,y in ((cx-76,cy),(cx+76,cy),(cx,cy-76),(cx,cy+76)):
            draw.ellipse((x-18,y-18,x+18,y+18),fill=(106,161,166),
                         outline=(225,230,222),width=3)
        draw.text((36,220),"METHANE",font=font(34),fill=(241,243,231))
        draw.text((36,266),"CH4  |  Digestion",font=font(17),fill=(190,226,207))
    else:
        cx=401
        draw.line((cx,331,cx,182),fill=(175,211,157),width=9)
        draw.line((cx,294,cx-54,248),fill=(175,211,157),width=5)
        draw.line((cx,249,cx+56,204),fill=(175,211,157),width=5)
        grow=.4+.6*min(1,t/3)
        for x,y,r in ((353,224,47),(458,184,56),(405,151,53)):
            rr=r*grow
            draw.ellipse((x-rr,y-rr/2,x+rr,y+rr/2),
                         fill=(92,164,106),outline=(158,208,148),width=3)
        draw.line((0,343,W,343),fill=(152,155,103),width=4)
        for n in range(8):
            ex=cx+(n-4)*22
            ey=396+(n*5)%25
            draw.line((cx,345,ex,ey),fill=(144,126,87),width=3)
        draw.text((36,214),"RESEARCH",font=font(31),fill=(244,239,219))
        draw.text((36,259),"ROOTED IN THE PASTURE",font=font(16),
                  fill=(211,229,196))
        draw.text((515,266),"PLENUM TERRA",font=font(22),fill=(238,238,210))
    draw.text((36,H-33),"ORIGINAL ANIMATED SCIENCE CONCEPT",
              font=font(12),fill=(178,203,187))
    return image


def make_clip(scene: int, path: Path):
    base = background(scene)
    command = ["ffmpeg","-hide_banner","-loglevel","error","-y",
               "-f","rawvideo","-pixel_format","rgb24",
               "-video_size",f"{W}x{H}","-framerate",str(FPS),"-i","pipe:0",
               "-an","-c:v","libx264","-preset","veryfast","-crf","23",
               "-pix_fmt","yuv420p",str(path)]
    process = subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    try:
        for i in range(FPS*SCENE_SECONDS):
            process.stdin.write(draw_frame(scene,i,base).tobytes())
        process.stdin.close()
        if process.wait(timeout=90):
            raise RuntimeError("Free FFmpeg scene failed: "
                               + process.stderr.read().decode()[-1000:])
    finally:
        if process.poll() is None:
            process.kill()


def create_storyboard(workspace: Path, voice_file: Path) -> Path:
    if workspace.exists() and any(workspace.iterdir()):
        raise FileExistsError("Use an empty workspace; never silently overwrite")
    workspace.mkdir(parents=True,exist_ok=True)
    voice_target = workspace / "narration.wav"
    voice_target.write_bytes(voice_file.read_bytes())
    captions = (
        ("THE PASTURE","Across the world's pastures, a quiet challenge persists."),
        ("THE METHANE QUESTION","Cattle release methane as part of digestion."),
        ("PLENUM TERRA","Exploring a potential research pathway."),
    )
    scenes=[]
    for i,(title,caption) in enumerate(captions):
        filename=f"motion_{i+1}.mp4"
        make_clip(i,workspace/filename)
        scenes.append({
            "type":"video","path":filename,"seconds":SCENE_SECONDS,
            "title":title,"caption":caption,"concept":True,
            "license":"owned","creator":"Plenum original procedural studio",
            "source_url":SOURCE,"rights_reviewed":True,
        })
    storyboard={
        "schema":"plenum-film-storyboard-v1",
        "title":"Plenum Terra / private animated science concept",
        "scenes":scenes,
        "narration":{
            "path":"narration.wav","license":"reviewed-license",
            "creator":"Kokoro-82M / hexgrad","source_url":MODEL_CARD,
            "rights_reviewed":True,"voice_usage_rights_reviewed":True,
        },
    }
    path=workspace/"storyboard.json"
    path.write_text(json.dumps(storyboard,indent=2)+"\n",encoding="utf-8")
    return path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--voice-file",type=Path,required=True)
    parser.add_argument("--workspace",type=Path,required=True)
    args=parser.parse_args()
    storyboard=create_storyboard(args.workspace,args.voice_file)
    from .film_factory import render
    receipt=render(storyboard,args.workspace/"final")
    # A genuine playable preview, never an authorized public documentary.
    assert receipt["voice_included"] is True
    assert receipt["public_distribution_approved"] is False
    print(json.dumps(receipt,indent=2))


if __name__=="__main__":
    main()
