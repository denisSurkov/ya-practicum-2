#/usr/bin/sh

echo "sleep to ensure all services running"
sleep 5

echo "starting config mongod_config_server"

docker compose -p mongo-sharding exec -T mongod_config_server mongosh --port 27017 <<EOF
rs.initiate( { _id: "mongod_config_server", configsvr: true, members: [ { _id: 0, host: "mongod_config_server:27017" } ] } )
EOF

echo "started config mongod_config_server"


echo "starting shard mongod_rs0"
docker compose -p mongo-sharding exec -T mongod_rs0_0 mongosh --port 27018 <<EOF
rs.initiate( { _id: "mongod_rs0", members: [ { _id: 0, host: "mongod_rs0_0:27018" } ] } )
EOF
echo "started shard mongod_rs0"


echo "starting shard mongod_rs1"
docker compose -p mongo-sharding exec -T mongod_rs1_0 mongosh --port 27018 <<EOF
rs.initiate( { _id: "mongod_rs1", members: [ { _id: 0, host: "mongod_rs1_0:27018" } ] } )
EOF
echo "started shard mongod_rs1"
