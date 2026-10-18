import networkx as nx
from rozier.refiner import RozierRefiner
from tests._dummy_topology import DummyTopology

def make_simple_interaction_graph(num_qubits=8):
    G = nx.Graph()
    for i in range(num_qubits):
        G.add_node(i)
    # make a few edges clustered
    edges = [(0,1),(1,2),(2,3),(4,5),(5,6),(6,7),(2,5),(3,6)]
    for u,v in edges:
        G.add_edge(u,v,weight=1)
    return G

def test_refiner_adapter_basic():
    G = make_simple_interaction_graph(8)
    topo = DummyTopology(num_chips=4, qubits_per_chip=2)

    # Build a fake diagnosis report shape
    report = {
        '_interaction_graph': G,
        'qubit_health': {},
        'observation': {
            'topology': {'shape': 'line'}
        }
    }

    ref = RozierRefiner()
    result = ref.run(report, topology_graph=topo.chip_graph)

    assert 'placement_plan' in result
    assert 'toolbags' in result
    assert isinstance(result['toolbags'], dict)
    # placement_plan may be empty if not enough hardware nodes, but should be a dict
    assert isinstance(result['placement_plan'], dict)
