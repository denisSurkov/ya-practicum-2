project_name = 'temp'
shard_count = 2
each_shard_has_replicas = 3
include_redis = True

config_service_name = 'mongod_config_server'
router_service_name = 'mongos_router'

services = []
volumes = []
docker_commands = []
shard_connection_strings = []

config_entry = f"""
    {config_service_name}:
        image: dh-mirror.gitverse.ru/mongo:latest
        restart: always
        container_name: {config_service_name}
        volumes:
            - {config_service_name}:/data/db
        expose:
            - "27017"
        command: [
            "--configsvr",
            "--replSet",
            "{config_service_name}",
            "--bind_ip_all",
            "--port",
            "27017"
        ]
        healthcheck:
            test: [ "CMD", "mongosh", "--eval", "db.adminCommand('ping')", "--port", "27017" ]
            interval: 5s
            start_period: 10s
"""
services.append(config_entry)
volumes.append(config_service_name)

rs_config = f'rs.initiate( {{ _id: "{config_service_name}", configsvr: true, members: [ {{ _id: 0, host: "{config_service_name}:27017" }} ] }} )'
docker_compose_command = f'echo "\nstarting config {config_service_name}"\n'
docker_compose_command += f'docker compose -p {project_name} exec -T {config_service_name} mongosh --port 27017 <<EOF\n{rs_config}\nEOF\n'
docker_compose_command += f'echo "\nstarted config {config_service_name}"\n'
docker_commands.append(docker_compose_command)

config_server_location = f'{config_service_name}/{config_service_name}:27017'

router_entry = f"""
    {router_service_name}:
        image: dh-mirror.gitverse.ru/mongo:latest
        restart: always
        container_name: {router_service_name}
        volumes:
            - {router_service_name}:/data/db
        expose:
            - "27020"
        command: [
            "mongos",
            "--configdb", 
            "{config_server_location}",
            "--bind_ip_all",
            "--port",
            "27020"
        ]
        healthcheck:
            test: [ "CMD", "mongosh", "--eval", "db.adminCommand('ping')", "--port", "27020" ]
            interval: 5s
            start_period: 10s
"""
services.append(router_entry)
volumes.append(router_service_name)


for shard_number in range(shard_count):
    shard_name = f'mongod_rs{shard_number}'
    last_replica_name = ''

    members = []
    for replica_number in range(each_shard_has_replicas):
        replica_name = f'{shard_name}_{replica_number}'
        last_replica_name = replica_name

        service_entry = f"""
    { replica_name }:
        image: dh-mirror.gitverse.ru/mongo:latest
        restart: always
        container_name: { replica_name }
        volumes:
            - { replica_name }:/data/db
        expose:
            - "27018"
        command: [
            "--shardsvr",
            "--replSet",
            "{ shard_name }",
            "--bind_ip_all",
            "--port",
            "27018"
        ]
        healthcheck:
            test: [ "CMD", "mongosh", "--eval", "db.adminCommand('ping')", "--port", "27018" ]
            interval: 5s
            start_period: 10s
"""
        services.append(service_entry)

        volume_name = f'   {replica_name}:\n'
        volumes.append(replica_name)


        member = f'{{ _id: {replica_number}, host: "{replica_name}:27018" }}'
        members.append(member)

    members_str = ', '.join(members)
    members_str = f"[ {members_str} ]"

    config = f'rs.initiate( {{ _id: "{ shard_name }", members: { members_str } }} )'
    docker_compose_command = f'echo "starting shard {shard_name}"\n'
    docker_compose_command += f'docker compose -p {project_name} exec -T {last_replica_name} mongosh --port 27018 <<EOF\n{config}\nEOF\n'
    docker_compose_command += f'echo "started shard {shard_name}"\n'

    docker_commands.append(docker_compose_command)

    shard_connection = f'"{shard_name}/{last_replica_name}:27018"'
    shard_connection_strings.append(shard_connection)


pymongo_api_entry = f"""
    pymongo_api:
        container_name: pymongo_api
        build: 
            context: api_app
            dockerfile: Dockerfile
        image: kazhem/pymongo_api:1.0.0
        ports:
          - 8080:8080
        environment:
            MONGODB_URL: "mongodb://{router_service_name}:27020"
            MONGODB_DATABASE_NAME: "somedb"
"""
services.append(pymongo_api_entry)


init_mongo_router = f'\necho "starting {router_service_name}"\n'
init_mongo_router += f'docker compose -p {project_name} exec -T {router_service_name} mongosh --port 27020 <<EOF\n'
for shard_connection in shard_connection_strings:
    init_mongo_router += f'sh.addShard( {shard_connection} );\n'
init_mongo_router += 'sh.enableSharding("somedb");\n'
init_mongo_router += 'sh.shardCollection("somedb.helloDoc", { "name" : "hashed" } );\n'
init_mongo_router += 'use somedb;\n'
init_mongo_router += 'for(var i = 0; i < 1000; i++) db.helloDoc.insertOne({age:i, name:"ly"+i});\n'
init_mongo_router += 'EOF\n'
docker_commands.append(init_mongo_router)


if include_redis:
    redis_entry = """
    redis:
        container_name: redis
        image: redis:latest
        expose:
          - "6379"
"""
    services.append(redis_entry)



with open('init.sh', 'w') as f:
    f.write('#/usr/bin/sh\n')
    f.writelines(docker_commands)
    f.write('\n')


with open('temp.yml', 'w') as f:
    f.write(f'name: {project_name}\n')

    f.write('\n')

    f.write('services:\n')
    f.writelines(services)

    f.write('\n')

    f.write('volumes:\n')
    f.writelines(map(lambda v: f'   {v}:\n', volumes))
