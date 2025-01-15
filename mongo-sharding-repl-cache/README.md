# pymongo-api

## Как запустить

1. Запускаем mongodb и приложение

```shell
docker compose up -d
```

2. Инциализируем mongo config server и шарды с репликами

```shell
chmod +x ./init.sh
./init.sh
```

3. Инциализируем mongo router

```shell
 chmod +x ./init_router.sh
 ./init_router.sh
```

4. Проверяеем приложение

```shell
curl http://localhost:8080/
```

5. Проверяем скорость загрузки с кэшем

```shell
curl -o /dev/null -s -w %{time_total}  http://localhost:8080/helloDoc/users
curl -o /dev/null -s -w %{time_total}  http://localhost:8080/helloDoc/users
```

### Ожидаемый результат

```json
{"mongo_topology_type":"Sharded","mongo_replicaset_name":null,"mongo_db":"somedb","read_preference":"Primary()","mongo_nodes":[["mongos_router",27020]],"mongo_primary_host":null,"mongo_secondary_hosts":[],"mongo_address":["mongos_router",27020],"mongo_is_primary":true,"mongo_is_mongos":true,"collections":{"helloDoc":{"documents_count":1000}},"shards":{"mongod_rs0":"mongod_rs0/mongod_rs0_2:27018,mongod_rs0_0:27018,mongod_rs0_1:27018","mongod_rs1":"mongod_rs1/mongod_rs1_2:27018,mongod_rs1_0:27018,mongod_rs1_1:27018"},"cache_enabled":true,"status":"OK"}
```

```text
1.225398
0.071087
```