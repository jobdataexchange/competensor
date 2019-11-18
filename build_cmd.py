from nameko.standalone.rpc import ClusterRpcProxy

config = {
    'AMQP_URI': 'amqp://guest:guest@rabbitmq'
}

with ClusterRpcProxy(config) as cluster_rpc:
    cluster_rpc.setup_frameworks.with_providers_and_store_frameworks()
    cluster_rpc.setup_frameworks.and_convert_frameworks_to_embeddings()
