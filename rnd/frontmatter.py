"""A small YAML-subset frontmatter reader (stdlib only).

Handles what entries and SKILL.md files actually use: scalars, inline lists,
block lists, one or more levels of nested maps, and | / > block scalars.
Anything fancier raises FrontmatterError rather than guessing.
"""

import re


class FrontmatterError(ValueError):
    pass


KEY_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*:(?:\s+(.*)|\s*)$")


def split(text):
    """Return (meta_text, body). meta_text is None when there is no frontmatter."""
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "".join(lines[1:i]), "".join(lines[i + 1:])
    raise FrontmatterError("frontmatter opened with --- but never closed")


def parse(meta_text):
    lines = [line.rstrip("\r\n") for line in meta_text.splitlines()]
    result, i = _parse_map(lines, 0, 0)
    j = _next_content(lines, i)
    if j < len(lines):
        raise FrontmatterError(f"line {j + 1}: could not parse {lines[j].strip()!r}")
    return result


def read(text):
    """Return (meta_dict, body). meta_dict is {} when there is no frontmatter."""
    meta_text, body = split(text)
    if meta_text is None:
        return {}, body
    return parse(meta_text), body


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _is_blank(line):
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


def _next_content(lines, i):
    while i < len(lines) and _is_blank(lines[i]):
        i += 1
    return i


def _parse_map(lines, i, indent):
    out = {}
    while True:
        i = _next_content(lines, i)
        if i >= len(lines):
            return out, i
        line = lines[i]
        ind = _indent(line)
        if ind < indent:
            return out, i
        if ind > indent:
            raise FrontmatterError(f"line {i + 1}: unexpected indent")
        if line.lstrip().startswith("-"):
            return out, i
        m = KEY_RE.match(line)
        if not m:
            raise FrontmatterError(f"line {i + 1}: expected 'key: value', got {line.strip()!r}")
        key, rest = m.group(1), (m.group(2) or "").strip()
        i += 1
        if rest[:1] in ("|", ">") and rest.rstrip("+-") in ("|", ">"):
            out[key], i = _block_scalar(lines, i, indent, folded=rest.startswith(">"))
        elif rest == "":
            j = _next_content(lines, i)
            if j < len(lines) and lines[j].lstrip().startswith("-") and _indent(lines[j]) >= indent:
                out[key], i = _parse_list(lines, j, _indent(lines[j]))
            elif j < len(lines) and _indent(lines[j]) > indent:
                out[key], i = _parse_map(lines, j, _indent(lines[j]))
            else:
                out[key] = None
        else:
            # A scalar may wrap onto more-indented continuation lines: plain
            # scalars always, quoted strings and inline lists until they close.
            while i < len(lines) and lines[i].strip() and _indent(lines[i]) > indent \
                    and _continues(rest):
                rest += " " + lines[i].strip()
                i += 1
            out[key] = _scalar(rest)


def _continues(rest):
    closer = {"'": "'", '"': '"', "[": "]"}.get(rest[:1])
    if closer is None:
        return True
    return len(rest) < 2 or not rest.endswith(closer)


def _parse_list(lines, i, indent):
    out = []
    while True:
        i = _next_content(lines, i)
        if i >= len(lines):
            return out, i
        line = lines[i]
        if _indent(line) != indent or not line.lstrip().startswith("-"):
            return out, i
        content = line.lstrip()[1:].strip()
        if KEY_RE.match(content):
            # "- key: value" starts a map whose keys align after the dash.
            lines[i] = " " * (indent + 2) + content
            item, i = _parse_map(lines, i, indent + 2)
            out.append(item)
            continue
        out.append(_scalar(content))
        i += 1


def _block_scalar(lines, i, parent_indent, folded):
    collected = []
    block_indent = None
    while i < len(lines):
        line = lines[i]
        if line.strip() == "":
            collected.append("")
            i += 1
            continue
        ind = _indent(line)
        if ind <= parent_indent:
            break
        if block_indent is None:
            block_indent = ind
        collected.append(line[min(ind, block_indent):])
        i += 1
    while collected and collected[-1] == "":
        collected.pop()
    if not folded:
        return "\n".join(collected), i
    paragraphs, current = [], []
    for part in collected:
        if part == "":
            if current:
                paragraphs.append(" ".join(current))
                current = []
        else:
            current.append(part.strip())
    if current:
        paragraphs.append(" ".join(current))
    return "\n".join(paragraphs), i


def _unquote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _scalar(value):
    value = value.strip()
    if value[:1] not in ("'", '"') and " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_unquote(part.strip()) for part in _split_commas(inner)]
    return _unquote(value)


def _split_commas(text):
    parts, current, quote = [], [], None
    for ch in text:
        if quote:
            current.append(ch)
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
            current.append(ch)
        elif ch == ",":
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    parts.append("".join(current))
    return [p for p in parts if p.strip()]
