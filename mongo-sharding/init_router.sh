#/usr/bin/sh

echo "sleep to ensure all services running"
sleep 5

echo "starting mongos_router"
docker compose -p mongo-sharding exec -T mongos_router mongosh --port 27020 <<EOF
sh.addShard( "mongod_rs0/mongod_rs0_0:27018" );
sh.addShard( "mongod_rs1/mongod_rs1_0:27018" );
sh.enableSharding("somedb");
sh.shardCollection("somedb.helloDoc", { "name" : "hashed" } );
use somedb;
for(var i = 0; i < 1000; i++) db.helloDoc.insertOne({age:i, name:"ly"+i});
EOF
