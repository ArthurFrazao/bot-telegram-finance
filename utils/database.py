import os
import functools
from google.cloud import bigquery
from models import Card, Subscription

bq = bigquery.Client()

dataset = "vault"

@functools.cache
def list_cards():
    table = "cards"
    table_id = f"{bq.project}.{dataset}.{table}"
    query = f"SELECT name, payment_date, total_limit, uuid FROM `{table_id}` ORDER BY name"
    result = bq.query(query).result()
    return [Card(name=row.name, payment_date=row.payment_date, total_limit=row.total_limit, uuid=row.uuid)
            for row in result]

@functools.cache
def list_subscriptions():
    table = "subscriptions"
    table_id = f"{bq.project}.{dataset}.{table}"
    query = f"SELECT name, description, payment_date, uuid, card_id, price FROM `{table_id}` ORDER BY name"
    result = bq.query(query).result()
    return [Subscription(name=row.name, description=row.description, payment_date=row.payment_date, uuid=row.uuid,
                 card_id=row.card_id, price=row.price) for row in result]

def insert_card(card: Card):
    table = "cards"
    table_id = f"{bq.project}.{dataset}.{table}"
    rows_to_insert = [{
        "name": card.name,
        "payment_date": card.payment_date,
        "total_limit": card.total_limit,
        "uuid": card.uuid
    }]
    bq.load_table_from_json(rows_to_insert, table_id)

def delete_card(uuid: str):
    table = "cards"
    table_id = f"{bq.project}.{dataset}.{table}"
    query = f"DELETE FROM `{table_id}` WHERE uuid = '{uuid}'"
    result = bq.query(query).result()

def insert_subscription(subscription: Subscription):
    table = "subscriptions"
    table_id = f"{bq.project}.{dataset}.{table}"
    rows_to_insert = [{
        "name": subscription.name,
        "description": subscription.description,
        "payment_date": subscription.payment_date,
        "uuid": subscription.uuid,
        "card_id": subscription.card_id,
        "price": subscription.price,
    }]
    bq.load_table_from_json(rows_to_insert, table_id)

def delete_subscription(uuid: str):
    table = "subscriptions"
    table_id = f"{bq.project}.{dataset}.{table}"
    query = f"DELETE FROM `{table_id}` WHERE uuid = '{uuid}'"
    result = bq.query(query).result()