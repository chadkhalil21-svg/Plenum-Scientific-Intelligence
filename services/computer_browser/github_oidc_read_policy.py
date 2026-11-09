"""Future Plus-compatible chat-to-owner-browser relay trust policy (SOURCE ONLY).

Unlike an unverified Github issue body, a GitHub Actions OIDC JWT is signed by
GitHub and binds the caller to an exact workflow, actor, repository and job.
This module never accepts owner cookies, website credentials, account contents
or a model-provided URL. NOT mounted on Cloud Run. Must not be enabled without
a separate owner-approved encrypted pairing and durable replay store.
"""
from dataclasses import dataclass
import os
import re
import time

ISSUER="https://token.actions.githubusercontent.com"
JWKS=ISSUER+"/.well-known/jwks"
REPOSITORY="chadkhalil21-svg/Plenum-Scientific-Intelligence"
# Public immutable GitHub IDs read from authenticated repository metadata.
REPOSITORY_ID="1447724141"
ACTOR_ID="251133044"
OWNER_SUBJECT=("repo:chadkhalil21-svg@"+ACTOR_ID+
               "/Plenum-Scientific-Intelligence@"+REPOSITORY_ID+
               ":environment:computer-browser-production")
WORKFLOW_REF=REPOSITORY+"/.github/workflows/chat-browser-owner-read.yml@refs/heads/main"
AUDIENCE="https://plenum-browser-owner-auth0-2lak3vl73q-ue.a.run.app/internal/chat-demo-read"
ENVIRONMENT="computer-browser-production"
MAX_LIFETIME=600


@dataclass(frozen=True)
class GitHubRelayIdentity:
    repository_id: str
    actor_id: str

    @classmethod
    def from_environment(cls):
        return cls(
            repository_id=os.environ.get("PLENUM_CHAT_RELAY_REPO_ID",""),
            actor_id=os.environ.get("PLENUM_CHAT_RELAY_ACTOR_ID",""),
        ).validate()

    def validate(self):
        if self.repository_id!=REPOSITORY_ID or self.actor_id!=ACTOR_ID:
            raise ValueError("Unrecognized immutable GitHub repository or owner identity")
        return self


def enforce_relay_claims(claims, identity, *, now=None):
    """Accept only already-signature-verified, short-lived issue workflow JWT."""
    identity.validate()
    t=int(time.time() if now is None else now)
    if not isinstance(claims,dict):
        raise PermissionError("No signed trusted workflow identity")
    iat,exp,nbf=claims.get("iat"),claims.get("exp"),claims.get("nbf")
    if (any(not isinstance(v,int) or isinstance(v,bool) for v in (iat,exp,nbf))
            or iat>t+10 or nbf>t+10 or exp<=t
            or not 0<exp-iat<=MAX_LIFETIME
            or nbf>iat+10
            or claims.get("iss")!=ISSUER
            or claims.get("aud")!=AUDIENCE
            or claims.get("repository")!=REPOSITORY
            or str(claims.get("repository_id"))!=identity.repository_id
            or claims.get("repository_owner")!="chadkhalil21-svg"
            or claims.get("actor")!="chadkhalil21-svg"
            or str(claims.get("actor_id"))!=identity.actor_id
            or claims.get("event_name")!="issues"
            or claims.get("ref")!="refs/heads/main"
            or claims.get("ref_type")!="branch"
            or claims.get("workflow_ref")!=WORKFLOW_REF
            or claims.get("environment")!=ENVIRONMENT
            or claims.get("repository_visibility")!="public"
            or claims.get("sub")!=OWNER_SUBJECT
            or str(claims.get("repository_owner_id"))!=ACTOR_ID
            or claims.get("runner_environment")!="github-hosted"
            or not isinstance(claims.get("jti"),str)
            or not 16<=len(claims["jti"])<=200
            or not isinstance(claims.get("run_id"),str)
            or not re.fullmatch(r"[1-9][0-9]{0,19}",claims["run_id"])):
        raise PermissionError("GitHub workflow identity or capability denied")
    # Do not return raw JWT claims, actor IDs, run IDs or a token.
    return {"trusted_github_workflow":True,
            "fixed_public_demo_read_only":True,
            "owner_pairing_still_required":True}


class GitHubOIDCTokenVerifier:
    """Pinned GitHub issuer/JWKS and RS256 only. Never trust token-provided key URIs."""

    def __init__(self, identity):
        self.identity=identity.validate()
        self._jwks=None

    def verify(self, token):
        import jwt
        if not isinstance(token,str) or not 80<=len(token)<=12000:
            raise PermissionError("Signed GitHub workflow token required")
        try:
            header=jwt.get_unverified_header(token)
            if header.get("alg")!="RS256" or not isinstance(header.get("kid"),str):
                raise PermissionError("GitHub signing key rejected")
            if self._jwks is None:
                self._jwks=jwt.PyJWKClient(JWKS,cache_jwk_set=True,lifespan=300,timeout=5)
            key=self._jwks.get_signing_key_from_jwt(token).key
            claims=jwt.decode(token,key,algorithms=["RS256"],issuer=ISSUER,
                audience=AUDIENCE,leeway=10,
                options={"require":["iss","aud","sub","iat","exp","nbf","jti"]})
            return enforce_relay_claims(claims,self.identity)
        except (jwt.PyJWTError,ValueError,TypeError,OSError) as exc:
            raise PermissionError("Invalid GitHub OIDC workflow token") from exc
