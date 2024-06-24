#!/usr/bin/env python
import os
import re
import ast
import copy
import typing
import asyncio
import argparse
import datetime
import subprocess
import dataclasses

import jinja2
import aiohttp
import gidgethub.aiohttp

# https://docs.github.com/en/graphql/overview/explorer
# https://docs.github.com/en/search-github/searching-on-github/searching-issues-and-pull-requests
# https://docs.github.com/en/search-github/github-code-search/understanding-github-code-search-syntax#language-qualifier

if os.environ.get("GITHUB_TOKEN"):
    TOKEN = os.environ["GITHUB_TOKEN"]
else:
    TOKEN = subprocess.check_output(["gh", "auth", "token"], text=True).strip()

REPO_URL = "https://github.com/JeanChristopheMorinPerso/stats"
if os.environ.get("GITHUB_REPOSITORY"):
    REPO_URL = f"https://github.com/{os.environ['GITHUB_REPOSITORY']}"


@dataclasses.dataclass
class Filter:
    field: str
    operator: str
    value: str


@dataclasses.dataclass
class Query:
    title: str
    description: str
    sortBy: str
    query: str
    pruneFields: list[str] | None = None
    filters: list[Filter] | None = None
    flattenKeys: list[str] | None = None


def readQueryFromFile(name: str) -> Query:
    with open(name) as fd:
        query = fd.read()

    title = None
    description_lines = []
    sortBy = None
    pruneFields = []
    filters = []
    flattenKeys = []

    queryLines = []
    for line in query.split("\n"):
        if match := re.match(r"^#\s+title\:\s+(?P<text>.*)$", line):
            if title:
                raise ValueError(f"Multiple titles found for {name}")
            title = match.group("text")
        elif match := re.match(r"^#\s+description\:\s+(?P<text>.*)$", line):
            description_lines.append(match.group("text"))
        elif match := re.match(r"^#\s+sortBy\:\s+(?P<sortBy>.*)$", line):
            if sortBy:
                raise ValueError(f"Multiple sortBy found for {name}")
            sortBy = match.group("sortBy")
        elif match := re.match(r"^#\s+pruneFields\:\s+(?P<pruneFields>.*)$", line):
            if pruneFields:
                raise ValueError(f"Multiple pruneFields found for {name}")
            pruneFields = [
                field.strip() for field in match.group("pruneFields").split(",")
            ]
        elif match := re.match(r"^#\s+filter\:\s+(?P<filter>.*)$", line):
            filter = ast.literal_eval(match.group("filter").strip())
            if not isinstance(filter, dict):
                raise ValueError(
                    f"Invalid filter type ({type(filter).__name__}) for {name}"
                )
            if sorted(["operator", "field", "value"]) != sorted(filter.keys()):
                raise ValueError(
                    f"Invalid filter keys {list(filter.keys())!r} for {name}"
                )

            if filter["operator"] not in ("==",):
                raise ValueError(
                    f"Invalid filter operator {filter['operator']} for {name}"
                )
            filters.append(Filter(**filter))
        elif match := re.match(r"^#\s+flatten\:\s+(?P<flatten>.*)$", line):
            flattenKeys.append(match.group("flatten"))
        else:
            queryLines.append(line)

    if not title:
        raise ValueError(f"No title found for {name}")
    if not description_lines:
        raise ValueError(f"No description found for {name}")
    if not sortBy:
        raise ValueError(f"No sortBy found for {name}")

    return Query(
        title.strip(),
        " ".join(description_lines).strip(),
        sortBy.strip(),
        "\n".join(queryLines).strip(),
        pruneFields=pruneFields,
        filters=filters,
        flattenKeys=flattenKeys,
    )


def convertToDatetime(field: str, row: list[str]):
    if field in row:
        row[field] = datetime.datetime.fromisoformat(row[field]).isoformat()


def getValue(dottedField: str, data: dict[str, typing.Any]) -> typing.Any:
    parts = dottedField.split(".", 1)
    if len(parts) == 1:
        return data[parts[0]]

    return getValue(parts[1], data[parts[0]])


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")

    args = parser.parse_args()

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("."), trim_blocks=True, lstrip_blocks=True
    )
    template = env.get_template("index.html.in")

    stats = []

    for queryfile in args.files:
        print(f"Processing {queryfile!r}")
        query = readQueryFromFile(queryfile)

        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(
                session, "JeanChristopheMorinPerso", oauth_token=TOKEN
            )

            data: list[dict[str, typing.Any]] = []
            endCursor = None
            hasNextPage = True
            page = 1

            while hasNextPage:
                print(f"Querying page {page}")

                result = await gh.graphql(query.query, endCursor=endCursor)
                for edge in result["search"]["edges"]:
                    edge = edge["node"]

                    for keyToFlatten in query.flattenKeys:
                        # We do the assumption that we always want to flatten to the top level,
                        # which might override stuff...
                        edge[keyToFlatten.split(".", 1)[0]] = getValue(
                            keyToFlatten, edge
                        )

                    # for field in edge.keys():
                    #     if field == "mergedBy":
                    #         edge["mergedBy"] = edge["mergedBy"]["login"]

                    data.append(edge)

                endCursor = result["search"]["pageInfo"]["endCursor"]
                hasNextPage = result["search"]["pageInfo"]["hasNextPage"]
                page += 1

        if not data:
            raise ValueError(
                f"No data returned for {queryfile}, something must be wrong with the query!"
            )

        headers = list(data[0].keys())

        # 1. Filter convert fields and filter rows
        for row in copy.deepcopy(data):
            rowIndex = data.index(row)
            convertToDatetime("Created__At", row)
            convertToDatetime("Merged__At", row)

            for filter in query.filters:
                for fieldName, fieldValue in row.items():
                    if fieldName != filter.field:
                        continue
                    if filter.operator == "==" and fieldValue != filter.value:
                        data.pop(rowIndex)

        # 2. Sort rows based on sortBy
        data = sorted(data, key=lambda x: x[query.sortBy])

        # 3. Prune fields
        for fieldToPrune in query.pruneFields:
            for row in data:
                del row[fieldToPrune]
            headers.remove(fieldToPrune)

        stats.append(
            {
                "title": query.title,
                "description": query.description,
                "data": [row.values() for row in data],
                "query": query.query,
                "headers": [key.replace("__", " ") for key in headers],
            }
        )

    with open("index.html", "w") as fd:
        fd.write(
            template.render(
                stats=stats,
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
                repoURL=REPO_URL,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
