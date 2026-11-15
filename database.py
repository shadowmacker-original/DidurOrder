import os
import sqlalchemy
from databases import Database

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root:1337_Svaga1337@localhost:3306/microservices_db"
)

database = Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()

orders = sqlalchemy.Table(
    "orders",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("total_amount", sqlalchemy.Numeric(10, 2)),
    sqlalchemy.Column("created_at", sqlalchemy.TIMESTAMP, server_default=sqlalchemy.func.now()),
)

order_items = sqlalchemy.Table(
    "order_items",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("order_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("orders.id")),
    sqlalchemy.Column("product_id", sqlalchemy.Integer),
    sqlalchemy.Column("quantity", sqlalchemy.Integer),
)

if DATABASE_URL.startswith("sqlite"):
    sync_url = DATABASE_URL.replace("+aiosqlite", "")
    engine = sqlalchemy.create_engine(sync_url, connect_args={"check_same_thread": False})
    metadata.create_all(engine)