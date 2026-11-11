"""Free, no-key public YouTube caption research for existing Plenum Research Director.

Retrieve the original available caption track once per PUBLIC video, then keep
only platform names, confidence and time offsets, not copyrighted transcripts.
This cannot bypass inaccessible captions, cloud IP blocks or private accounts.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

REPO = "chadkhalil21-svg/Plenum-Scientific-Intelligence"
OWNER = "chadkhalil21-svg"
TITLE = "[Plenum Research] public video captions"
MARKER = "PLENUM_VIDEO_CAPTIONS_PUBLIC_V1"
ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "integrations/workforces/six_video_platforms_20261111.json"
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
ALIASES = {
    "ElevenLabs": ["eleven labs"],
    "AnythingLLM": ["anything llm"],
    "Open WebUI": ["open web ui"],
    "OpenHands": ["open hands"],
    "whisper.cpp": ["whisper dot cpp", "whisper cpp"],
    "llama.cpp": ["llama dot cpp", "llama cpp"],
    "AUTOMATIC1111 Stable Diffusion WebUI": ["stable diffusion web ui", "automatic 1111", "automatic1111"],
    "Broke": ["app called broke", "broke app"],
    "MCP": ["model context protocol", "mcp"],
    "F Cancer skill": ["cancer skill", "f cancer"],
    "AI Systems Academy": ["ai systems academy"],
    "Hugging Face": ["hugging face"],
    "Google Docs": ["google doc", "google docs"],
}


def parse_owner_event(event: dict) -> list[str]:
    issue = event.get("issue") or {}
    if (event.get("action") != "opened"
        or (event.get("repository") or {}).get("full_name") != REPO
        or (issue.get("user") or {}).get("login") != OWNER
        or issue.get("title") != TITLE
        or not isinstance(issue.get("number"), int) or issue["number"] < 1
        or not isinstance(issue.get("body"), str)):
        raise PermissionError("Not an original founder-owned public caption request")
    lines = issue["body"].splitlines()
    if (len(lines) != 2 or lines[0] != MARKER or not lines[1].startswith("videos: ")):
        raise ValueError("Require exact two-line caption command")
    video_ids = lines[1][8:].split(",")
    if (not 1 <= len(video_ids) <= 6
        or len(set(video_ids)) != len(video_ids)
        or any(not VIDEO_ID.fullmatch(x) for x in video_ids)):
        raise ValueError("Only one to six distinct public YouTube IDs")
    return video_ids


def load_catalog(path=CATALOG):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data.get("videos")
    if data.get("schema") != "plenum-founder-six-video-original-source-audit-v1" or not isinstance(rows,list) or len(rows) != 6:
        raise ValueError("Cannot use an unreviewed video catalog")
    by_id = {}
    for v in rows:
        video_id = v.get("id")
        if (not isinstance(video_id,str) or not VIDEO_ID.fullmatch(video_id)
            or video_id in by_id
            or not isinstance(v.get("platforms"),list)
            or len(v["platforms"]) > 30):
            raise ValueError("Unbounded source catalog")
        by_id[video_id] = v
    return by_id


def _patterns(name):
    names = [name, *ALIASES.get(name, [])]
    # Normalize product-name punctuation for spoken captions, e.g. whisper.cpp
    return [re.compile(r"(?<![a-z0-9])"+re.escape(x.lower()).replace(r"\ ","[ -]*")+r"(?![a-z0-9])")
            for x in names if len(x) >= 3]



def fetch_public_jina_captions(video_id: str, *, post=None):
    """Try official documented Jina Reader public YouTube transcript toggle.

    Anonymous Reader currently offers limited free requests. It gets ONLY
    the public video URL. No API key, cookies, private account or media
    download. Failure means unavailable, never a reason to purchase credits.
    https://github.com/jina-ai/reader/blob/main/cookbooks.md
    """
    if not VIDEO_ID.fullmatch(video_id):
        raise ValueError("Only permitted public video IDs")
    if post is None:
        import requests
        post = requests.post
    script = ("waitForSelector('ytd-video-description-transcript-section-renderer button')"
              ".then((el) => el.click())")
    response = post(
        "https://r.jina.ai/",
        files={
            "url":(None, "https://www.youtube.com/watch?v=" + video_id),
            "injectPageScript":(None,script),
        },
        headers={"Accept":"application/json","X-Timeout":"25000"},
        timeout=35
    )
    response.raise_for_status()
    doc = response.json()
    payload = doc.get("data",doc)
    content = payload.get("content") or payload.get("markdown") or ""
    if not isinstance(content,str) or not 300 <= len(content) <= 220000:
        raise ValueError("Jina response does not contain bounded public caption text")
    # Accept only clearly marked, timestamped caption rows after a transcript
    # heading; avoid misidentifying video chapter navigation as subtitles.
    markers = list(re.finditer(r"(?im)^\s*#{0,3}\s*(?:video )?transcript\s*:?\s*$",content))
    if not markers:
        raise ValueError("No verified transcript section in public reader output")
    scoped = content[markers[-1].end():]
    line = re.compile(r"(?m)^\s*(?:[-*]\s*)?\[?(\d{1,2}:\d{2}(?::\d{2})?)\]?\s*(?:[-|:]\s*)?(.{12,650})$")
    rows=[]
    for match in line.finditer(scoped):
        timecode, words=match.groups()
        parts=[int(v) for v in timecode.split(":")]
        seconds = parts[0]*60 + parts[1] if len(parts)==2 else parts[0]*3600 + parts[1]*60 + parts[2]
        if seconds > 86400 or not words.strip():
            continue
        rows.append({"start":float(seconds),"text":words.strip()})
        if len(rows) >= 5000:
            break
    if len(rows) < 15 or sum(len(x["text"]) for x in rows) < 750:
        raise ValueError("Only chapters/navigation or no usable captions from Jina")
    return rows

def review_video(video: dict, *, fetch=None, fallback=None):
    video_id = video["id"]
    if fetch is None:
        from youtube_transcript_api import YouTubeTranscriptApi
        fetch = YouTubeTranscriptApi().fetch
        fallback = fetch_public_jina_captions  # only for real GitHub project jobs
    result = {"id":video_id,"title":video["title"],
        "url":"https://www.youtube.com/watch?v="+video_id,
        "status":"CAPTION_UNAVAILABLE","caption_source":"YouTube public captions only",
        "captions_read":False,"caption_segments_count":0,"caption_text_saved":False,
        "platforms":[{"name":x["name"],"category":x["category"],
                      "found_in_caption":False,"timestamps_seconds":[]}
                     for x in video["platforms"]]}
    try:
        try:
            captions = fetch(video_id)
            rows = captions.to_raw_data() if hasattr(captions,"to_raw_data") else captions
        except Exception as original_exc:
            result["direct_failure_type"] = type(original_exc).__name__[:90]
            if fallback is None:
                raise
            result["fallback_attempted"] = True
            try:
                rows = fallback(video_id)
            except Exception as fallback_exc:
                result["fallback_failure_type"] = type(fallback_exc).__name__[:90]
                raise
            result["caption_source"] = "Jina Reader anonymous public YouTube caption view"
            result["free_fallback_used"] = True
        if not isinstance(rows, list) or not 8 <= len(rows) <= 5000:
            raise ValueError("Unusable or unbounded captions")
        if any(not isinstance(x,dict) or not isinstance(x.get("text"),str) or
               len(x["text"]) > 1200 or not isinstance(x.get("start"),(float,int))
               for x in rows):
            raise ValueError("Invalid caption segment format")
        result["captions_read"] = True
        result["caption_segments_count"] = len(rows)
        result["status"] = "CAPTIONS_RETRIEVED"
        text_samples = [(float(v["start"]), (v["text"]+" "+(rows[i+1]["text"] if i+1 < len(rows) else "")).lower())
                        for i,v in enumerate(rows)]
        for platform in result["platforms"]:
            pats = _patterns(platform["name"])
            stamps = []
            for sec, line in text_samples:
                if any(p.search(line) for p in pats):
                    if not stamps or sec > stamps[-1] + 3:
                        stamps.append(round(sec))
                    if len(stamps) >= 3:
                        break
            platform["found_in_caption"] = bool(stamps)
            platform["timestamps_seconds"] = stamps
        result["names_confirmed_in_captions"] = sum(int(x["found_in_caption"]) for x in result["platforms"])
        result["platform_list_complete_by_captions_alone"] = False
    except Exception as exc:
        # Failure is a reliable result, not authority to retry with keys,
        # scrape protected pages or fetch copyrighted audio through proxies.
        result["failure_type"] = type(exc).__name__[:90]
    return result


def research(ids: list[str], catalog, *, fetch=None):
    results = []
    for id in ids:
        if id not in catalog:
            raise ValueError("Founder requested video not yet audited in PUBLIC catalog")
        results.append(review_video(catalog[id],fetch=fetch))
    return {"schema":"plenum-free-captions-six-video-v1","outcomes":results,
        "requested":len(ids),"captions_retrieved":sum(x["captions_read"] for x in results),
        "text_or_audio_saved":False,"private_account_access":False,
        "paid_inference_used":False,"full_visual_playback_claimed":False,
        "not_an_exhaustive_platform_detector":True}


def post_result(report: dict, issue: int, token: str):
    lines = [
        "<!-- plenum-caption-evidence:v1 -->",
        "## Plenum Research | independent free-caption retrieval",
        f"Original public captions retrieved: **{report['captions_retrieved']}/{report['requested']}**.",
        "Only previously reviewed platform names/timestamps are reported; no full copyrighted transcripts or private credentials are stored.",
    ]
    for row in report["outcomes"]:
        n = row.get("names_confirmed_in_captions",0)
        lines.append(f"- [{row['id']}]({row['url']}): **{row['status']}**; "+
                     f"{n} of {len(row['platforms'])} previously identified names directly matched in captions; source: {row['caption_source']}.")
    lines.append("A failed caption request cannot certify a video has no captions; YouTube sometimes blocks public cloud IPs. Matching names alone does not validate vendor claims or prove exhaustive audiovisual review.")
    uri = f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"
    body = json.dumps({"body":"\n".join(lines)})
    req = Request(uri,body.encode("utf-8"),method="POST",headers={
        "Authorization":"Bearer "+token,
        "Accept":"application/vnd.github+json",
        "Content-Type":"application/json",
        "User-Agent":"PlenumResearchFreeCaptions/1"})
    with urlopen(req,timeout=20) as response:
        data=json.loads(response.read(40000))
    if not data.get("html_url"):
        raise RuntimeError("No acknowledged original GitHub comment")
    return data["html_url"]


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--event",required=True)
    parser.add_argument("--execute",action="store_true")
    parser.add_argument("--defer-report",action="store_true",help="Independent verifier posts the sole founder receipt")
    parser.add_argument("--out",default="reports/youtube-research/free-caption-evidence.json")
    args=parser.parse_args(argv)
    event=json.loads(Path(args.event).read_text(encoding="utf-8"))
    ids=parse_owner_event(event)
    catalog=load_catalog()
    out=Path(args.out)
    if out.is_absolute() or ".." in out.parts or not out.parts or out.parts[0]!="reports":
        parser.error("Only reports/ paths allowed")
    if not args.execute:
        print(json.dumps({"status":"PUBLIC_PREFLIGHT_ONLY","video_ids":ids,
                          "network_used":False,"account_actions":False}))
        return
    if (os.getenv("GITHUB_ACTIONS") != "true"
        or os.getenv("GITHUB_REPOSITORY") != REPO
        or os.getenv("GITHUB_EVENT_NAME") != "issues"):
        raise PermissionError("Only original project issue event may run public caption research")
    report=research(ids,catalog)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    token=os.getenv("GH_TOKEN")
    if not token:
        raise PermissionError("Scoped original GitHub issue token missing")
    if args.defer_report:
        print("PUBLIC_CAPTION_RESEARCH evidence saved for independent verifier")
    else:
        url=post_result(report,event["issue"]["number"],token)
        print("PUBLIC_CAPTION_RESEARCH "+url)


if __name__=="__main__":
    main()
