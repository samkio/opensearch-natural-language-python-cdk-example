from adapter.open_search import OpenSearchClient
from adapter.secrets_manager import SecretsManagerSecret
from adapter.open_ai import OpenAIClient
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
import os

logger = Logger(service="natural_elastic_search")

os_client = OpenSearchClient(os.environ["OS_CLUSTER_ENDPOINT"], "docs")
openai_api_key = SecretsManagerSecret(os.environ["OPEN_AI_API_KEY_SECRET"]).get_value()
openai_client = OpenAIClient(openai_api_key)


@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> None:
    """Sample Python Lambda that populates an OpenSearch index
    with data and then performs queries against it using natural
    english language translated via OpenAI's text davinci model.

    :param event: Lambda event details.
    :param context: Lambda execution context.
    """

    # 1. Pre-load data into the OS cluster
    os_client.index_docs(
        [
            {"title": "Moneyball", "director": "Bennett Miller", "year": "2011"},
            {
                "title": "Star Wars: Episode I - The Phantom Menace",
                "director": "George Lucas",
                "year": "1999",
            },
            {"title": "28 Days Later", "director": "Danny Boyle", "year": "2002"},
            {"title": "Shaun of the Dead", "director": "Edgar Wright", "year": "2004"},
            {
                "title": "The Grand Budapest Hotel",
                "director": "Wes Anderson",
                "year": "2014",
            },
        ]
    )

    # 2. Perform static defined search
    response = os_client.query(
        '{"size": 5,"query": {"multi_match": {"query": "miller", "fields": ["title^2", "director"]}}}'
    )
    logger.info("Static search results", response=response)

    # 3. Perform natural search #1
    query = openai_client.query_to_open_search_query(
        "Find all movies that were made after 2010"
    )
    response = os_client.query(f'{{"size": 5,{query}}}')
    logger.info("Natural #1 search results", response=response)

    # 4. Perform natural search #2
    query = openai_client.query_to_open_search_query(
        "Find all movies that were directed by George Lucas with Star Wars in the title"
    )
    response = os_client.query(f'{{"size": 5,{query}}}')
    logger.info("Natural #2 search results", response=response)
