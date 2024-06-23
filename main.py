#!/usr/bin/env python
import re
import argparse

import jinja2
import pandas
import clickhouse_connect

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("."), trim_blocks=True, lstrip_blocks=True
)
template = env.get_template("index.html.in")

parser = argparse.ArgumentParser()
parser.add_argument("files", nargs="+")

args = parser.parse_args()


client = clickhouse_connect.get_client(
    host="play.clickhouse.com",
    secure=True,
    port=443,
    username="play",
    password="clickhouse",
)


def readQuery(name: str) -> tuple[str, str, str]:
    with open(name) as fd:
        query = fd.read()

    data = {}

    title = None
    description_lines = []

    for line in query.split("\n"):
        if match := re.match(r"^--\s+title\:\s+(?P<text>.*)$", line):
            if title:
                raise ValueError(f"Multiple titles found for {name}")
            title = match.group("text")
        elif match := re.match(r"^--\s+description\:\s+(?P<text>.*)$", line):
            description_lines.append(match.group("text"))

    print(title)
    if not title:
        raise ValueError(f"No title found for {name}")
    if not description_lines:
        raise ValueError(f"No description found for {name}")

    return title.strip(), " ".join(description_lines).strip(), query.strip()


stats = []
for queryfile in args.files:
    title, description, query = readQuery(queryfile)
    df: pandas.DataFrame = client.query_df(query=query)

    headers = df.columns.tolist()
    rows = df.values.tolist()
    stats.append(
        {
            "title": title,
            "description": description,
            "query": query,
            "headers": headers,
            "data": rows,
        }
    )

with open("index.html", "w") as fd:
    fd.write(template.render(stats=stats))
