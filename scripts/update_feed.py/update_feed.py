import html
import os
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path

ATOM = "{http://www.w3.org/2005/Atom}"
ATOM_NS = "http://www.w3.org/2005/Atom"
FEED_URL = "https://www.reddit.com/r/pokemongo/.rss"
FEED_LINK = "https://raw.githubusercontent.com/Pretendworking/r_pokemongo/main/feed.xml"


class TextOnly(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def plain_text(value):
    parser = TextOnly()
    parser.feed(html.unescape(value or ""))
    return " ".join(" ".join(parser.parts).split())


def atom_child(element, name):
    return element.find(ATOM + name)


def atom_value(element, name):
    child = atom_child(element, name)
    return "".join(child.itertext()).strip() if child is not None else ""


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        try:
            return parsedate_to_datetime(value).astimezone(timezone.utc)
        except (TypeError, ValueError):
            return None


def get_entry_link(entry):
    for link in entry.findall(ATOM + "link"):
        if link.get("rel") in (None, "alternate") and link.get("href"):
            return link.get("href")
    return atom_value(entry, "id")


def main():
    request = urllib.request.Request(
        FEED_URL,
        headers={
            "User-Agent": "r_pokemongo-rss (https://github.com/Pretendworking/r_pokemongo)",
            "Accept": "application/atom+xml, application/xml;q=0.9, */*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        source = ET.fromstring(response.read())

    ET.register_namespace("atom", ATOM_NS)
    rss = ET.Element("rss", {"version": "2.0"})
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "r/pokemongo on Reddit"
    ET.SubElement(channel, "link").text = "https://www.reddit.com/r/pokemongo/"
    ET.SubElement(channel, "description").text = "New posts from Reddit's r/pokemongo community."
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "ttl").text = "5"
    ET.SubElement(channel, f"{{{ATOM_NS}}}link", {
        "href": FEED_LINK,
        "rel": "self",
        "type": "application/rss+xml",
    })

    entries = source.findall(ATOM + "entry")
    newest = None
    for entry in entries[:100]:
        title = atom_value(entry, "title") or "(untitled Reddit post)"
        link = get_entry_link(entry)
        entry_id = atom_value(entry, "id") or link
        raw_date = atom_value(entry, "published") or atom_value(entry, "updated")
        published = parse_date(raw_date)
        if published and (newest is None or published > newest):
            newest = published

        content = atom_child(entry, "content")
        if content is None:
            content = atom_child(entry, "summary")
        description = plain_text("".join(content.itertext())) if content is not None else ""
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid", {"isPermaLink": "false"}).text = entry_id
        if published:
            ET.SubElement(item, "pubDate").text = format_datetime(published)
        if description:
            ET.SubElement(item, "description").text = description
        author = atom_value(entry, "author")
        if author:
            ET.SubElement(item, "author").text = author

    if newest:
        ET.SubElement(channel, "lastBuildDate").text = format_datetime(newest)

    data = ET.tostring(rss, encoding="utf-8", xml_declaration=True)
    ET.fromstring(data)  # Validate generated XML before replacing the published feed.
    path = Path("feed.xml")
    temporary = path.with_suffix(".xml.tmp")
    temporary.write_bytes(data + bytes([10]))
    os.replace(temporary, path)
    print(f"Wrote valid RSS 2.0 XML with {len(entries[:100])} Reddit entries.")


if __name__ == "__main__":
    main()
