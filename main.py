#!/usr/bin/env python
import argparse

import pandas
import clickhouse_connect

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


df: pandas.DataFrame = client.query_df(query=readQuery(args.query_file))
print(df.to_markdown(index=False, tablefmt="github"))
