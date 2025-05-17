from neo4j import GraphDatabase

class Interface:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=False)
        self._driver.verify_connectivity()

    def close(self):
        self._driver.close()

    def bfs(self, start_node, last_node):
        # TODO: Implement this method
        with self._driver.session() as session:

            graphResult = session.run("CALL gds.graph.exists('bfsGraph') YIELD exists")
            graph_exists = graphResult.single()["exists"]

            if not graph_exists:
                session.run("""
                    CALL gds.graph.project(
                        'bfsGraph',
                        'Location',
                        { TRIP: { properties: 'distance' } }
                    )
                """)

            query = """
                MATCH (source:Location {name: $start_node}), (target:Location {name: $target_node})
                CALL gds.shortestPath.dijkstra.stream('bfsGraph', {
                    sourceNode: source,
                    targetNodes: target,
                    relationshipWeightProperty: 'distance'
                })
                YIELD index, sourceNode, targetNode, totalCost, nodeIds, costs, path
                RETURN
                    index,
                    gds.util.asNode(sourceNode).name AS sourceNodeName,
                    gds.util.asNode(targetNode).name AS targetNodeName,
                    totalCost,
                    [nodeId IN nodeIds | gds.util.asNode(nodeId).name] AS nodeNames,
                    costs,
                    nodes(path) as path
                ORDER BY totalCost ASC
            """
            result = session.run(query, start_node=start_node, target_node=last_node)
            return result.data()

    def pagerank(self, max_iterations, weight_property):
        # TODO: Implement this method
        with self._driver.session() as session:
            prResult = session.run("CALL gds.graph.exists('bfsGraph') YIELD exists")
            pr_exists = prResult.single()["exists"]

            if not pr_exists:
                session.run("""
                    CALL gds.graph.project(
                        'prGraph',
                        'Location',
                        { TRIP: { properties: $weight_property } }
                    )
                """, weight_property=weight_property)

            query = """
                CALL gds.pageRank.stream('prGraph', {
                    maxIterations: $max_iter,
                    dampingFactor: 0.85,
                    relationshipWeightProperty: $weight_property
                })
                YIELD nodeId, score
                RETURN gds.util.asNode(nodeId).name AS name, score
                ORDER BY score DESC
            """
            result = session.run(query, max_iter=max_iterations, weight_property=weight_property)
            
            nodes = result.data()
            return [
                max(nodes, key=lambda x: x['score']), 
                min(nodes, key=lambda x: x['score'])
            ]

