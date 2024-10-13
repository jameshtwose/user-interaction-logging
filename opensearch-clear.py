#!/usr/bin/env python

# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.
#
# Modifications Copyright OpenSearch Contributors. See
# GitHub history for details.


import os

from opensearchpy import OpenSearch

# connect to OpenSearch


def main() -> None:
    """
    an example showing how to create an synchronous connection to
    OpenSearch, create an index, index a document and search to
    return the document
    """
    host = "localhost"
    port = 9200
    auth = (
        "admin",
        os.getenv("OPENSEARCH_PASSWORD", "admin"),
    )  # For testing only. Don't store credentials in code.

    client = OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=False,
        ssl_show_warn=False,
    )

    info = client.info()
    print(f"Welcome to {info['version']['distribution']} {info['version']['number']}!")

    # create an index

    index_name = "canvas-index"

    # delete the document
    for i in range(1, 100):
        doc_id = str(i)
        response = client.delete(index=index_name, id=doc_id)
        print(response)

    # # delete the index

    # response = client.indices.delete(index=index_name)

    # print(response)


if __name__ == "__main__":
    main()