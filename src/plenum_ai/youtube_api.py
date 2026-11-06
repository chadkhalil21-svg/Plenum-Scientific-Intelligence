"""Official YouTube Data API metadata access, only with explicit owner credential.

The lightweight public channel Atom feed remains available separately.
This module searches video metadata but NEVER downloads videos, captions,
audio or transcripts. API quota and usage terms apply; never log API key.
"""
import json
import os
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

MAX_BYTES=180_000
CHANNEL_ID=re.compile(r"^UC[A-Za-z0-9_-]{22}$")


def _fetch(url,opener=urlopen):
    request=Request(url,headers={"User-Agent":"PlenumScientificIntelligence/1.4 official-youtube-metadata",
                                 "Accept":"application/json"})
    try:
        with opener(request,timeout=15) as response:
            raw=response.read(MAX_BYTES+1)
    except Exception:
        # Never include exception text, since HTTP errors can contain a URL
        # including a private API key as a query parameter.
        raise RuntimeError("YouTube metadata API call failed; check key, quota and access") from None
    if len(raw)>MAX_BYTES:
        raise ValueError("YouTube API returned too much metadata")
    try:
        return json.loads(raw)
    except (ValueError,UnicodeDecodeError):
        raise ValueError("YouTube API returned invalid JSON") from None


def video_search(query,key,channel=None,max_results=5,opener=urlopen):
    if not isinstance(query,str) or not 2<=len(query.strip())<=120:
        raise ValueError("Video search query must be 2..120 characters")
    if not isinstance(key,str) or not 15<=len(key)<=300:
        raise ValueError("Owner-provided YOUTUBE_API_KEY required")
    if not isinstance(max_results,int) or not 1<=max_results<=10:
        raise ValueError("Limit to at most 10 videos")
    if channel and (not isinstance(channel,str) or not CHANNEL_ID.fullmatch(channel)):
        raise ValueError("Unsupported channel ID")
    params={"part":"snippet","type":"video","q":query.strip(),
            "order":"date","maxResults":max_results,"key":key}
    if channel:
        params["channelId"]=channel
    # API v3 official endpoint. Do not store request URLs in evidence artifacts.
    url="https://www.googleapis.com/youtube/v3/search?"+urlencode(params)
    response=_fetch(url,opener=opener)
    if not isinstance(response,dict) or not isinstance(response.get("items"),list):
        raise ValueError("Unexpected official YouTube video search format")
    out=[]
    for item in response["items"][:max_results]:
        if not isinstance(item,dict):
            continue
        video=(item.get("id") or {}).get("videoId")
        snippet=item.get("snippet") or {}
        if not isinstance(video,str) or not re.fullmatch(r"[A-Za-z0-9_-]{11}",video):
            continue
        out.append({
            "source":"youtube-data-api","tier":"public_video_metadata",
            "video_id":video,
            "title":str(snippet.get("title") or "")[:300],
            "published":str(snippet.get("publishedAt") or "")[:40],
            "channel_title":str(snippet.get("channelTitle") or "")[:120],
            "url":"https://www.youtube.com/watch?v="+video,
            "transcript_retrieved":False,"video_media_retrieved":False,
            "laboratory_claims_verified":False,
        })
    return {"channel_id":channel,"query":query,
            "videos":out,"service":"official_youtube_data_api_v3",
            "credential_present":True,
            "credential_stored_or_logged":False,
            "access_to_captions":False,"media_downloaded":False,
            "rights_to_republish":False,
            "quota_note":"Official Google API key and project-specific search quota required"}


def from_environment(query,channel=None,opener=urlopen):
    key=os.getenv("YOUTUBE_API_KEY")
    if not key:
        raise ValueError("YOUTUBE_API_KEY not configured; public channel feed remains optional")
    return video_search(query,key,channel=channel,opener=opener)
