#!/usr/bin/env python
import argparse

import jinja2
import pandas
import clickhouse_connect

env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("."), trim_blocks=True, lstrip_blocks=True
)
template = env.get_template("index.html.in")

parser = argparse.ArgumentParser()
parser.add_argument("query_file")

args = parser.parse_args()


client = clickhouse_connect.get_client(
    host="play.clickhouse.com",
    secure=True,
    port=443,
    username="play",
    password="clickhouse",
)


def readQuery(name: str) -> str:
    with open(name) as fd:
        query = fd.read()
    return query


query = readQuery(args.query_file)
df: pandas.DataFrame = client.query_df(query=query)
# breakpoint()
# print(df.to_csv(index=False))

headers = df.columns.tolist()
rows = df.values.tolist()

with open("index.html", "w") as fd:
    fd.write(template.render(headers=headers, rows=rows, query=query.strip()))
