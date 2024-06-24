import os
import pathlib

import pytest

import main


@pytest.mark.parametrize(
    "content,expected",
    (
        # missing-title1
        ("#name", main.Query("a", "a", "a", "a")),
        # missing-title2
        ("# title", main.Query("a", "a", "a", "a")),
        # missing-description
        (
            "\n".join(
                (
                    "# title: asd",
                    "# sortBy: myfield",
                )
            ),
            main.Query("asd", "myfield", "a", "a"),
        ),
        # missing-sortBy
        (
            "\n".join(
                (
                    "# title: asd",
                    "# description: asdasdaasd",
                )
            ),
            main.Query("asd", "", "asdasdaasd", "a"),
        ),
        # multi-title
        (
            "\n".join(
                (
                    "# title: asd",
                    "# title: asdasdaasd",
                )
            ),
            main.Query("", "", "", "a"),
        ),
        # multi-sortBy
        (
            "\n".join(
                (
                    "# title: asd",
                    "# sortBy: asdasdaasd",
                    "# sortBy: asdasdaasd2",
                )
            ),
            main.Query("", "", "", "a"),
        ),
        # multi-pruneFields
        (
            "\n".join(
                (
                    "# title: asd",
                    "# sortBy: asdasdaasd",
                    "# description: asdasdaasd2",
                    "# pruneFields: asdasdaasd3",
                    "# pruneFields: asdasdaasd3",
                )
            ),
            main.Query("", "", "", "a"),
        ),
        # filter-invalid-type
        (
            "\n".join(
                (
                    "# title: asd",
                    "# sortBy: asdasdaasd",
                    "# description: asdasdaasd2",
                    "# filter: 1",
                )
            ),
            main.Query("", "", "", "a"),
        ),
        # filter-missing-field
        (
            "\n".join(
                (
                    "# title: asd",
                    "# sortBy: asdasdaasd",
                    "# description: asdasdaasd2",
                    "# filter: {'operator': '==', 'value': 'asd'}",
                )
            ),
            main.Query("", "", "", "a"),
        ),
        # filter-invalid-operator
        (
            "\n".join(
                (
                    "# title: asd",
                    "# sortBy: asdasdaasd",
                    "# description: asdasdaasd2",
                    "# filter: {'operator': '!=', 'field': 'myfield', 'value': 'asd'}",
                )
            ),
            main.Query("", "", "", "a"),
        ),
    ),
    ids=(
        "missing-title1",
        "missing-title2",
        "missing-description",
        "missing-sortBy",
        "multi-title",
        "multi-sortBy",
        "multi-pruneFields",
        "filter-invalid-type",
        "filter-missing-field",
        "filter-invalid-operator",
    ),
)
def test_readQueryFromFile_exception(
    content: str, expected: main.Query, tmp_path: pathlib.Path
):
    with open(tmp_path / "test.query", "w") as fd:
        fd.write(content)

    with pytest.raises(ValueError):
        main.readQueryFromFile(os.fspath(tmp_path / "test.query"))


@pytest.mark.parametrize(
    "content,expected",
    (
        # basic
        (
            "\n".join(
                (
                    "# title: asd",
                    "# sortBy: asdasdaasd",
                    "# description: asdasdaasd2",
                    "a query here",
                    "and here",
                    "",
                )
            ),
            main.Query(
                "asd",
                "asdasdaasd2",
                "asdasdaasd",
                "a query here\nand here",
                pruneFields=[],
                filters=[],
                flattenKeys=[],
            ),
        ),
        # multiline-description
        (
            "\n".join(
                (
                    "# title: asd",
                    "# sortBy: asdasdaasd",
                    "# description: asdasdaasd2",
                    "# description: second part",
                    "a query here",
                    "and here",
                    "",
                )
            ),
            main.Query(
                "asd",
                "asdasdaasd2 second part",
                "asdasdaasd",
                "a query here\nand here",
                pruneFields=[],
                filters=[],
                flattenKeys=[],
            ),
        ),
        # pruneFields-single
        (
            "\n".join(
                (
                    "# title: asd",
                    "# sortBy: asdasdaasd",
                    "# description: asdasdaasd2",
                    "# pruneFields: field1",
                    "a query here",
                    "and here",
                    "",
                )
            ),
            main.Query(
                "asd",
                "asdasdaasd2",
                "asdasdaasd",
                "a query here\nand here",
                pruneFields=["field1"],
                filters=[],
                flattenKeys=[],
            ),
        ),
        # pruneFields-multi
        (
            "\n".join(
                (
                    "# title: asd",
                    "# sortBy: asdasdaasd",
                    "# description: asdasdaasd2",
                    "# pruneFields: field1,field2 , field3",
                    "a query here",
                    "and here",
                    "",
                )
            ),
            main.Query(
                "asd",
                "asdasdaasd2",
                "asdasdaasd",
                "a query here\nand here",
                pruneFields=["field1", "field2", "field3"],
                filters=[],
                flattenKeys=[],
            ),
        ),
        # filter-single
        (
            "\n".join(
                (
                    "# title: asd",
                    "# sortBy: asdasdaasd",
                    "# description: asdasdaasd2",
                    "# filter: {'operator': '==', 'field': 'fieldA', 'value': 'myvalue'}",
                    "a query here",
                    "and here",
                    "",
                )
            ),
            main.Query(
                "asd",
                "asdasdaasd2",
                "asdasdaasd",
                "a query here\nand here",
                pruneFields=[],
                filters=[main.Filter("fieldA", "==", "myvalue")],
                flattenKeys=[],
            ),
        ),
        # filter-multi
        (
            "\n".join(
                (
                    "# title: asd",
                    "# sortBy: asdasdaasd",
                    "# description: asdasdaasd2",
                    "# filter: {'operator': '==', 'field': 'fieldA', 'value': 'myvalueA'}",
                    "# filter: {'operator': '==', 'field': 'fieldB', 'value': 'myvalueB'}",
                    "a query here",
                    "and here",
                    "",
                )
            ),
            main.Query(
                "asd",
                "asdasdaasd2",
                "asdasdaasd",
                "a query here\nand here",
                pruneFields=[],
                filters=[
                    main.Filter("fieldA", "==", "myvalueA"),
                    main.Filter("fieldB", "==", "myvalueB"),
                ],
                flattenKeys=[],
            ),
        ),
        # flatten-single
        (
            "\n".join(
                (
                    "# title: asd",
                    "# sortBy: asdasdaasd",
                    "# description: asdasdaasd2",
                    "# flatten: field1.subfield1",
                    "a query here",
                    "and here",
                    "",
                )
            ),
            main.Query(
                "asd",
                "asdasdaasd2",
                "asdasdaasd",
                "a query here\nand here",
                pruneFields=[],
                filters=[],
                flattenKeys=["field1.subfield1"],
            ),
        ),
        # flatten-multi
        (
            "\n".join(
                (
                    "# title: asd",
                    "# sortBy: asdasdaasd",
                    "# description: asdasdaasd2",
                    "# flatten: field1.subfield1",
                    "# flatten: field2.subfield1.subfield2",
                    "a query here",
                    "and here",
                    "",
                )
            ),
            main.Query(
                "asd",
                "asdasdaasd2",
                "asdasdaasd",
                "a query here\nand here",
                pruneFields=[],
                filters=[],
                flattenKeys=["field1.subfield1", "field2.subfield1.subfield2"],
            ),
        ),
    ),
    ids=(
        "basic",
        "multiline-description",
        "pruneFields-single",
        "pruneFields-multi",
        "filter-single",
        "filter-multi",
        "flatten-single",
        "flatten-multi",
    ),
)
def test_readQueryFromFile(content: str, expected: main.Query, tmp_path: pathlib.Path):
    with open(tmp_path / "test.query", "w") as fd:
        fd.write(content)

    assert main.readQueryFromFile(os.fspath(tmp_path / "test.query")) == expected
