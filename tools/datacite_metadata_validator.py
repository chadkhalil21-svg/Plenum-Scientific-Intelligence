#!/usr/bin/env python3
"""Bounded offline DataCite JSON/XML metadata validator (public records only)."""

import argparse
import base64
import binascii
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from lxml import etree


NS = "http://datacite.org/schema/kernel-4"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_VERSION = "4.7"
SCHEMA_URI = f"https://schema.datacite.org/meta/kernel-{SCHEMA_VERSION}/metadata.xsd"
SCHEMA_HASHES = {
    "metadata.xsd": "be878f9afddeb677ec4cd274233de0c328246748305d9f58ee78352714412522",
    "include/xml.xsd": "cc701736c42cc64126fad063bb95f94484b5de3b5f808a86ea098b0957aff829",
    "include/datacite-titleType-v4.xsd": "03b4eb8c8b71ca2ef95b6a921be654f0dd18b4d89616a12708198d67f6fa463a",
    "include/datacite-contributorType-v4.xsd": "bf70f146ac4b1874877b8248b3f4cb2e1ba676ac90c52a8b862639cc7b2c8afa",
    "include/datacite-dateType-v4.xsd": "d6bf5a93077dccfb53aa73929e41c3d16d0b95920c64e76e655240367dc48812",
    "include/datacite-resourceType-v4.xsd": "57098b3aac1af97ddc0dce5b33a3b1db9fa8e45f84fbcaa8cf7598dd1f08787a",
    "include/datacite-relationType-v4.xsd": "248255d472bdb792065520d79f966c6d55d0997cf709877b3b8ebbf634e0d3d9",
    "include/datacite-relatedIdentifierType-v4.xsd": "1f838e3bc6a92e6f7fb419335664c258ee1864822e2af40fae5e4a65545079ad",
    "include/datacite-funderIdentifierType-v4.xsd": "eab86e3c6fb0d24d3508559e667641862838b988fe14147dc187ebd79c9bcfe8",
    "include/datacite-descriptionType-v4.xsd": "b69733e1cffe134eada14d604db17dcf913c21bc8552f6b7debcd3ce04eba3e9",
    "include/datacite-nameType-v4.xsd": "a841e852c1cf00e6301f489ce6b85d94017b6cffbdce991d2b7a5e7e27921e5a",
    "include/datacite-numberType-v4.xsd": "e9f9e3c66b34a4476bab683058734f22922d167f76e642db0c05a50842b94241",
}
MAX_RECORDS = 20
MAX_BYTES = 5_000_000
DOI = re.compile(r"10\.\d{4,9}/\S+", re.ASCII)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def bounded_bytes(path):
    with path.open("rb") as f:
        data = f.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError(f"Input exceeds {MAX_BYTES} bytes: {path.name}")
    return data


def normalized(value):
    return " ".join(value.split()) if isinstance(value, str) else ""


def doi_identity(value):
    value = normalized(value)
    return value.casefold() if DOI.fullmatch(value) else None


def as_dict(value):
    return value if isinstance(value, dict) else {}


def normalized_list(values, key):
    if not isinstance(values, list) or not values:
        return []
    return [normalized(as_dict(v).get(key)) for v in values]


def parser():
    return etree.XMLParser(resolve_entities=False, load_dtd=False,
                           no_network=True, huge_tree=False)


def xml_record(data):
    doc = etree.fromstring(data, parser())
    if doc.getroottree().docinfo.doctype:
        raise ValueError("DOCTYPE not permitted")
    return doc


def compile_schema(schema_path):
    """The caller provides the pinned official schema and its local includes."""
    directory = schema_path.parent.resolve()
    discovered = {}

    def collect(path):
        path = path.resolve()
        if not path.is_relative_to(directory):
            raise ValueError("Schema dependency escapes trusted local directory")
        logical = path.relative_to(directory).as_posix()
        if logical in discovered:
            return
        raw = bounded_bytes(path)
        digest = sha256(raw)
        if SCHEMA_HASHES.get(logical) != digest:
            raise ValueError(f"Schema provenance mismatch: {logical}")
        discovered[logical] = digest
        root = xml_record(raw)
        for location in root.xpath("//xs:include/@schemaLocation | //xs:import/@schemaLocation",
                                   namespaces={"xs": "http://www.w3.org/2001/XMLSchema"}):
            if not re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.xsd", location):
                raise ValueError("Schema dependency must be a local relative XSD")
            collect(path.parent / location)

    collect(schema_path)
    if discovered != SCHEMA_HASHES:
        raise ValueError("Incomplete pinned schema dependency set")
    tree = etree.parse(str(schema_path.resolve()), parser())
    return etree.XMLSchema(tree), discovered


def validate_record(record, schema, counts, expected_client=None,
                    expected_year=None, expected_type=None):
    record = as_dict(record)
    attrs = as_dict(record.get("attributes"))
    errors, gaps = [], []
    identifier = doi_identity(record.get("id"))
    json_doi = doi_identity(attrs.get("doi"))
    if record.get("type") != "dois":
        errors.append("invalid_JSON_API_record_type")
    if not identifier or not json_doi or identifier != json_doi:
        errors.append("invalid_or_mismatched_JSON_DOI")
    if identifier and counts[identifier] != 1:
        errors.append("duplicate_record_DOI")

    publisher = attrs.get("publisher")
    publisher = as_dict(publisher).get("name") if isinstance(publisher, dict) else publisher
    year = attrs.get("publicationYear")
    year_text = str(year) if type(year) is int and 1000 <= year <= 9999 else ""
    values = {
        "doi": json_doi,
        "titles": normalized_list(attrs.get("titles"), "title"),
        "creators": normalized_list(attrs.get("creators"), "name"),
        "publisher": normalized(publisher),
        "year": year_text,
        "type": normalized(as_dict(attrs.get("types")).get("resourceTypeGeneral")),
    }
    for name, val in values.items():
        if not val or isinstance(val, list) and not all(val):
            errors.append(f"missing_or_invalid_JSON_{name}")

    client = as_dict(as_dict(as_dict(record.get("relationships")).get("client")).get("data")).get("id")
    if expected_client and client != expected_client:
        errors.append("outside_expected_client")
    if expected_year is not None and year != expected_year:
        errors.append("outside_expected_year")
    if expected_type and values["type"] != expected_type:
        errors.append("outside_expected_resource_type")
    for optional in ("descriptions", "subjects", "rightsList", "language", "relatedIdentifiers"):
        if not attrs.get(optional):
            gaps.append(f"missing_optional_{optional}")

    xml_digest = None
    schema_hint = None
    schema_passed = False
    consistency = False
    try:
        if not isinstance(attrs.get("xml"), str) or not attrs["xml"]:
            raise ValueError("missing_XML")
        raw = base64.b64decode(attrs["xml"], validate=True)
        if len(raw) > MAX_BYTES:
            raise ValueError("XML_size_limit")
        xml_digest = sha256(raw)
        root = xml_record(raw)
        if root.tag != f"{{{NS}}}resource" or attrs.get("schemaVersion") != NS:
            errors.append("unsupported_or_mismatched_kernel_namespace")
        schema_hint = root.get(f"{{{XSI}}}schemaLocation", "")
        tokens = schema_hint.split()
        if len(tokens) % 2 or len(set(tokens[::2])) != len(tokens[::2]):
            errors.append("malformed_schema_location")
        hints = dict(zip(tokens[::2], tokens[1::2]))
        declared = hints.get(NS, "")
        if declared in (f"https://schema.datacite.org/meta/kernel-4/metadata.xsd",
                        f"http://schema.datacite.org/meta/kernel-4/metadata.xsd", ""):
            gaps.append("original_schema_minor_unknown; checked_against_4.7")
        elif declared not in (SCHEMA_URI, SCHEMA_URI.replace("https://", "http://")):
            errors.append("different_or_unrecognized_declared_schema_version")
        schema_passed = schema.validate(root)
        if not schema_passed:
            errors.append("XML_schema_incompatible_with_4.7")

        def xpath(expr):
            return root.xpath(expr, namespaces={"d": NS})

        xml_values = {
            "doi": doi_identity(xpath("string(d:identifier)")),
            "titles": [normalized(v) for v in xpath("d:titles/d:title/text()")],
            "creators": [normalized(v) for v in xpath("d:creators/d:creator/d:creatorName/text()")],
            "publisher": normalized(xpath("string(d:publisher)")),
            "year": normalized(xpath("string(d:publicationYear)")),
            "type": normalized(xpath("string(d:resourceType/@resourceTypeGeneral)")),
        }
        differences = [name for name in values if values[name] != xml_values[name]]
        if differences:
            errors.extend(f"JSON_XML_mismatch_{name}" for name in differences)
        if xpath("string(d:identifier/@identifierType)").casefold() != "doi":
            errors.append("XML_identifier_type_not_DOI")
        consistency = not differences and bool(json_doi) and all(values.values()) and all(values["titles"]) and all(values["creators"])
    except (ValueError, binascii.Error, etree.XMLSyntaxError) as exc:
        errors.append(f"invalid_XML:{type(exc).__name__}")

    return {
        "doi": identifier,
        "client": client,
        "publication_year": year,
        "resource_type_general": values["type"],
        "title_count": len(values["titles"]),
        "creator_count": len(values["creators"]),
        "xml_sha256": xml_digest,
        "declared_schema_location": schema_hint,
        "xsd_4_7_compatible": schema_passed,
        "required_json_xml_consistent": consistency,
        "errors": errors,
        "review_flags": gaps,
        "status": "INVALID" if errors else "REVIEW_REQUIRED" if gaps else "VALIDATED",
    }


def validate(input_path, schema_path, expected_client=None, expected_year=None,
             expected_type=None, source_url=None):
    raw = bounded_bytes(input_path)
    payload = json.loads(raw)
    records = as_dict(payload).get("data")
    if not isinstance(records, list) or not 1 <= len(records) <= MAX_RECORDS:
        raise ValueError(f"Expected list of 1-{MAX_RECORDS} DataCite records")
    schema, schema_hashes = compile_schema(schema_path)
    counts = Counter(doi_identity(as_dict(r).get("id")) for r in records)
    results = [validate_record(r, schema, counts, expected_client, expected_year,
                               expected_type) for r in records]
    invalid = sum(r["status"] == "INVALID" for r in results)
    review = sum(r["status"] == "REVIEW_REQUIRED" for r in results)
    return {
        "input_sha256": sha256(raw),
        "input_bytes": len(raw),
        "validator_sha256": sha256(Path(__file__).read_bytes()),
        "source_url": source_url,
        "xsd_version": SCHEMA_VERSION,
        "xsd_source_url": SCHEMA_URI,
        "schema_file_sha256": schema_hashes,
        "lxml_version": list(etree.LXML_VERSION),
        "libxml_version": list(etree.LIBXML_VERSION),
        "expected_scope": {"client": expected_client, "year": expected_year, "type": expected_type},
        "summary": {
            "records": len(records), "unique_valid_record_ids": len([d for d in counts if d]),
            "xsd_4_7_compatible": sum(r["xsd_4_7_compatible"] for r in results),
            "required_json_xml_consistent": sum(r["required_json_xml_consistent"] for r in results),
            "invalid": invalid, "review_required": review, "validated": len(records) - invalid - review,
        },
        "records": results,
        "scope_limit": "Metadata only; no scientific quality, openness, licensing or data access certification. Unversioned XML hints cannot establish original minor version.",
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("input", type=Path)
    cli.add_argument("--schema", required=True, type=Path)
    cli.add_argument("--output", required=True, type=Path)
    cli.add_argument("--client")
    cli.add_argument("--year", type=int)
    cli.add_argument("--type", dest="resource_type")
    cli.add_argument("--source-url")
    args = cli.parse_args()
    report = validate(args.input, args.schema, args.client, args.year, args.resource_type, args.source_url)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True))
    return 2 if report["summary"]["invalid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
